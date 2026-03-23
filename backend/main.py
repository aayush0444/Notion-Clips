"""FastAPI application entrypoint for the Notionclips backend service."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Literal, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.notion_oauth import router as notion_oauth_router
from backend.supabase_client import get_session
from gemini import answer_question, extract_video_insights
from models import ActionItem, ActionItemList, StudyNotes, VideoInsights, WorkBrief
from push_to_notion import push_study_notes, push_work_brief, push_youtube
from youtube_mode import get_youtube_transcript

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


class QAResponse(BaseModel):
    """Response payload for /qa endpoint."""

    answer: str


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


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "ok"}


@app.post("/transcript", response_model=TranscriptResponse)
async def fetch_transcript(payload: TranscriptRequest) -> TranscriptResponse:
    """Fetch a transcript for the requested YouTube video."""
    video_id = payload.video_id.strip()
    if not video_id:
        raise HTTPException(status_code=400, detail="video_id is required")

    try:
        transcript, duration = get_youtube_transcript(video_id)
    except Exception as exc:  # pragma: no cover - FastAPI handles logging
        logger.exception("Transcript fetch failed for video_id=%s", video_id)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return TranscriptResponse(transcript=transcript, duration_minutes=duration)


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

    return ExtractResponse(
        mode=payload.mode,
        word_count=word_count,
        duration_minutes=payload.duration_minutes,
        insights=serialized,
    )


def _resolve_notion_credentials(
    token: Optional[str], page_id: Optional[str], session_id: Optional[str]
) -> Dict[str, Optional[str]]:
    """Resolve Notion credentials from direct payload or Supabase session."""
    resolved_token = token
    resolved_page_id = page_id

    if session_id:
        session = get_session(session_id)
        if session:
            resolved_token = resolved_token or session.get("notion_token")
            resolved_page_id = resolved_page_id or session.get("notion_page_id")

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
        payload.notion_token, payload.notion_page_id, payload.session_id
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
            chat_mode=payload.chat_mode,
        )
    except Exception as exc:  # pragma: no cover
        logger.exception("Q&A generation failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return QAResponse(answer=answer)
