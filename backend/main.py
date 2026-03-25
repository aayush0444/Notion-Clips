"""FastAPI application entrypoint for the Notionclips backend service."""

from __future__ import annotations

import logging
import os
import time
import hashlib
import json
from typing import Any, Dict, List, Literal, Optional
import requests

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.notion_oauth import router as notion_oauth_router
from backend.supabase_client import (
    get_cached_insights,
    get_cached_transcript,
    get_session,
    save_cached_insights,
    save_cached_transcript,
)
from gemini import answer_question, extract_video_insights
from models import ActionItem, ActionItemList, StudyNotes, VideoInsights, WorkBrief
from push_to_notion import push_study_notes, push_work_brief, push_youtube
from youtube_mode import extract_video_id, get_youtube_transcript

load_dotenv()

logger = logging.getLogger("notionclips.backend")
logger.setLevel(logging.INFO)

ModeLiteral = Literal["study", "work", "quick"]


class TranscriptRequest(BaseModel):
    """Request payload for /transcript endpoint."""

    video_id: str = Field(..., description="YouTube video ID or URL")


class TranscriptResponse(BaseModel):
    """Response payload for /transcript endpoint."""

    transcript: str
    duration_minutes: float
    cache_hit: bool = False
    fetch_ms: int = 0


class ExtractRequest(BaseModel):
    """Request payload for /extract endpoint."""

    transcript: str = Field(..., description="Full transcript text to analyze")
    mode: ModeLiteral = Field("study", description="Extraction mode")
    sections: Optional[Dict[str, bool]] = Field(
        default=None,
        description="Optional section toggles for quick mode (summary/key_takeaways/topics/action_items).",
    )
    duration_minutes: Optional[float] = Field(
        default=None,
        description="Optional video duration metadata for downstream logging.",
    )


class ExtractResponse(BaseModel):
    """Response payload for /extract endpoint."""

    mode: ModeLiteral
    word_count: int
    duration_minutes: Optional[float]
    insights: Dict[str, Any]
    cache_hit: bool = False


class QARequest(BaseModel):
    """Request payload for /qa endpoint."""

    question: str = Field(..., description="User question about the video.")
    transcript: str = Field(..., description="Full transcript text used for Q&A.")
    mode: ModeLiteral = Field("study", description="Current study/work/quick mode.")
    chat_mode: Literal["strict", "open"] = Field(
        "strict",
        description="strict limits answers to transcript; open allows broader context.",
    )
    chat_history: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Prior chat messages for conversational context.",
    )
    notion_page_id: Optional[str] = None
    session_id: Optional[str] = None


class QAResponse(BaseModel):
    """Response payload for /qa endpoint."""

    answer: str


class NotionEditRequest(BaseModel):
    """Request payload for /notion/edit endpoint."""

    page_id: str
    instruction: str
    session_id: str


class PushRequest(BaseModel):
    """Request payload for /push endpoint."""

    mode: ModeLiteral
    insights: Dict[str, Any]
    video_url: Optional[str] = Field(
        default="",
        description="Source video URL. Used to create the Notion bookmark block.",
    )
    notion_token: Optional[str] = None
    notion_page_id: Optional[str] = None
    session_id: Optional[str] = Field(
        default=None,
        description="Supabase session identifier. Used to fetch stored Notion credentials.",
    )
    sections: Optional[Dict[str, bool]] = Field(
        default=None,
        description="Section toggles for quick-mode pushes (same structure as /extract).",
    )
    tasks: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional ActionItemList payload for quick mode task database creation.",
    )


class PushResponse(BaseModel):
    """Response payload for /push endpoint."""

    status: str
    page_id: Optional[str] = None


app = FastAPI(
    title="Notionclips Backend",
    version="1.0.0",
    description="REST API for transcript retrieval, AI extraction, Notion pushes, and Notion OAuth.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notion_oauth_router)
PROMPT_VERSION = "v1"


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "ok"}


@app.post("/transcript", response_model=TranscriptResponse)
async def fetch_transcript(payload: TranscriptRequest) -> TranscriptResponse:
    """Fetch a transcript for the requested YouTube video."""
    start = time.perf_counter()
    input_value = payload.video_id.strip()
    if not input_value:
        raise HTTPException(status_code=400, detail="video_id is required")
    video_id = extract_video_id(input_value)
    if not video_id:
        raise HTTPException(status_code=400, detail="Unable to parse video_id from input")

    try:
        cached = get_cached_transcript(video_id)
    except Exception as exc:
        logger.warning("Transcript cache read failed for video_id=%s: %s", video_id, exc)
        cached = None

    if cached and cached.get("transcript"):
        transcript = str(cached.get("transcript", "")).strip()
        if transcript:
            duration_raw = cached.get("duration_minutes")
            try:
                duration = float(duration_raw) if duration_raw is not None else len(transcript.split()) / 130
            except (TypeError, ValueError):
                duration = len(transcript.split()) / 130
            logger.info("Transcript cache hit for video_id=%s", video_id)
            fetch_ms = int((time.perf_counter() - start) * 1000)
            return TranscriptResponse(
                transcript=transcript,
                duration_minutes=duration,
                cache_hit=True,
                fetch_ms=fetch_ms,
            )

    try:
        transcript, duration = get_youtube_transcript(video_id)
    except Exception as exc:  # pragma: no cover - FastAPI handles logging
        logger.exception("Transcript fetch failed for video_id=%s", video_id)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    try:
        save_cached_transcript(video_id, transcript, duration)
        logger.info("Transcript cache save success for video_id=%s", video_id)
    except Exception as exc:
        logger.warning("Transcript cache write failed for video_id=%s: %s", video_id, exc)

    fetch_ms = int((time.perf_counter() - start) * 1000)
    return TranscriptResponse(
        transcript=transcript,
        duration_minutes=duration,
        cache_hit=False,
        fetch_ms=fetch_ms,
    )


@app.post("/extract", response_model=ExtractResponse)
async def extract_insights(payload: ExtractRequest) -> ExtractResponse:
    """Run AI extraction on a provided transcript."""
    transcript = payload.transcript.strip()
    if not transcript:
        raise HTTPException(status_code=400, detail="transcript must not be empty")

    sections = payload.sections or {
        "summary": True,
        "key_takeaways": True,
        "topics": True,
        "action_items": True,
    }
    sections_key = json.dumps(sections, sort_keys=True, separators=(",", ":"))
    transcript_hash = hashlib.sha256(transcript.encode("utf-8")).hexdigest()
    cache_key = hashlib.sha256(
        f"{payload.mode}|{sections_key}|{transcript_hash}|{PROMPT_VERSION}".encode("utf-8")
    ).hexdigest()

    try:
        cached = get_cached_insights(cache_key)
    except Exception as exc:
        logger.warning("Insights cache read failed key=%s: %s", cache_key[:10], exc)
        cached = None

    if cached and isinstance(cached.get("insights"), dict):
        logger.info("Insights cache hit key=%s mode=%s", cache_key[:10], payload.mode)
        return ExtractResponse(
            mode=payload.mode,
            word_count=int(cached.get("word_count") or len(transcript.split())),
            duration_minutes=payload.duration_minutes,
            insights=cached["insights"],
            cache_hit=True,
        )

    try:
        insights = extract_video_insights(
            transcript,
            mode=payload.mode,
            sections=sections,
            duration_minutes=payload.duration_minutes or 0,
        )
    except Exception as exc:  # pragma: no cover
        logger.exception("Extraction failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    word_count = len(transcript.split())
    if isinstance(insights, (StudyNotes, WorkBrief, VideoInsights)):
        serialized = insights.dict()
    else:
        serialized = insights

    try:
        save_cached_insights(
            cache_key=cache_key,
            mode=payload.mode,
            transcript_hash=transcript_hash,
            sections_key=sections_key,
            insights=serialized,
            word_count=word_count,
        )
        logger.info("Insights cache save key=%s mode=%s", cache_key[:10], payload.mode)
    except Exception as exc:
        logger.warning("Insights cache write failed key=%s: %s", cache_key[:10], exc)

    return ExtractResponse(
        mode=payload.mode,
        word_count=word_count,
        duration_minutes=payload.duration_minutes,
        insights=serialized,
        cache_hit=False,
    )


def _resolve_notion_credentials(
    token: Optional[str], page_id: Optional[str], session_id: Optional[str], mode: str
) -> Dict[str, Optional[str]]:
    """Resolve Notion credentials from direct payload or Supabase session."""
    resolved_token = token
    resolved_page_id = page_id

    if session_id:
        session = get_session(session_id)
        if session:
            resolved_token = resolved_token or session.get("notion_token")

            if not resolved_page_id:
                if mode == "study":
                    resolved_page_id = session.get("study_page_id")
                elif mode == "work":
                    resolved_page_id = session.get("work_page_id")
                elif mode == "quick":
                    resolved_page_id = session.get("quick_page_id")

            if not resolved_page_id:
                resolved_page_id = session.get("notion_page_id")

    if not resolved_page_id:
        resolved_page_id = os.getenv("NOTION_PAGE_ID")

    return {"token": resolved_token, "page_id": resolved_page_id}


def _build_tasks(payload: Optional[Dict[str, Any]]) -> Optional[ActionItemList]:
    """Convert raw task payloads into an ActionItemList."""
    if not payload:
        return None

    items_data = payload.get("items")
    if not isinstance(items_data, list):
        return None

    try:
        items = [ActionItem(**item) for item in items_data]
        return ActionItemList(items=items)
    except Exception:
        logger.warning("Invalid tasks payload supplied; ignoring.")
        return None


@app.post("/push", response_model=PushResponse)
async def push_to_notion_endpoint(payload: PushRequest) -> PushResponse:
    """Push extracted insights to Notion using either supplied or session-based credentials."""
    creds = _resolve_notion_credentials(
        payload.notion_token, payload.notion_page_id, payload.session_id, payload.mode
    )

    if not creds["token"] or not creds["page_id"]:
        raise HTTPException(
            status_code=400,
            detail="Notion credentials are required via notion_token/notion_page_id or session_id.",
        )

    try:
        if payload.mode == "study":
            insights = StudyNotes(**payload.insights)
            page_id = push_study_notes(
                insights,
                payload.video_url or "",
                notion_token=creds["token"],
                notion_page_id=creds["page_id"],
            )
        elif payload.mode == "work":
            insights = WorkBrief(**payload.insights)
            page_id = push_work_brief(
                insights,
                payload.video_url or "",
                notion_token=creds["token"],
                notion_page_id=creds["page_id"],
            )
        else:
            insights = VideoInsights(**payload.insights)
            tasks = _build_tasks(payload.tasks)
            sections = payload.sections or {
                "summary": True,
                "key_takeaways": True,
                "topics": True,
                "action_items": True,
            }
            page_id = push_youtube(
                insights,
                payload.video_url or "",
                task_list=tasks,
                sections=sections,
                notion_token=creds["token"],
                notion_page_id=creds["page_id"],
            )
    except Exception as exc:  # pragma: no cover
        logger.exception("Failed to push insights to Notion")
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return PushResponse(status="ok", page_id=page_id)


@app.post("/qa", response_model=QAResponse)
async def answer_question_endpoint(payload: QARequest) -> QAResponse:
    """Answer user questions about a transcript using Gemini helper."""
    transcript = payload.transcript.strip()
    if not transcript:
        raise HTTPException(status_code=400, detail="transcript must not be empty for Q&A")

    try:
        answer = answer_question(
            question=payload.question,
            transcript=transcript,
            mode=payload.mode,
            chat_history=payload.chat_history,
            notion_page_id=payload.notion_page_id,
            session_id=payload.session_id,
        )
    except Exception as exc:  # pragma: no cover
        logger.exception("Q&A generation failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return QAResponse(answer=answer)


@app.post("/notion/edit")
async def notion_edit(payload: NotionEditRequest):
    """Append a paragraph block to an existing Notion page."""
    session = get_session(payload.session_id)
    if not session or not session.get("notion_token"):
        raise HTTPException(status_code=401, detail="No Notion token for this session")

    token = session["notion_token"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    block = {
        "children": [{
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": payload.instruction[:2000]}}]
            }
        }]
    }
    res = requests.patch(
        f"https://api.notion.com/v1/blocks/{payload.page_id}/children",
        json=block,
        headers=headers,
        timeout=10
    )
    if res.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Notion edit failed: {res.text}")
    return {"status": "ok"}
