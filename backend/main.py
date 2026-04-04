"""FastAPI application entrypoint for the Notionclips backend service."""

from __future__ import annotations
from backend.export_utils import insights_to_markdown
from fastapi.responses import PlainTextResponse

import logging
import os
import time
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
import requests

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.content_ingestion import extract_text_from_pdf, extract_text_from_url
from backend.notion_oauth import router as notion_oauth_router
from backend.smart_watch import router as smart_watch_router
from backend.study_session import router as study_session_router
from backend.unified_library import router as unified_library_router
from backend.supabase_client import (
    get_cached_insights,
    get_cached_transcript,
    get_latest_insight,
    get_session,
    save_cached_insights,
    save_cached_transcript,
    save_library_item,
)
from gemini import answer_question, extract_insights as generate_insights, get_pre_watch_verdict
from models import ActionItem, ActionItemList, PreWatchVerdict, StudyNotes, VideoInsights, WorkBrief, SynthesisAnalysis
from push_to_notion import push_study_notes, push_timestamp_notes, push_work_brief, push_youtube
from youtube_mode import extract_video_id, get_youtube_transcript

load_dotenv()

logger = logging.getLogger("notionclips.backend")
logger.setLevel(logging.INFO)

ModeLiteral = Literal["study", "work", "quick"]


class TranscriptRequest(BaseModel):
    """Request payload for /transcript endpoint."""

    video_id: str = Field(..., description="YouTube video ID or URL")
    allow_supadata: bool = Field(
        True,
        description="When false, transcript fetching will avoid Supadata fallback and use scraping only.",
    )


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
    questions: Optional[List[str]] = Field(
        default=None,
        description="User questions to focus extraction on (optional)",
    )
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


class ArticleExtractRequest(BaseModel):
    url: str
    mode: ModeLiteral = "study"
    session_id: str
    user_id: Optional[str] = None
    sections: Optional[Dict[str, bool]] = None


def _extract_with_cache(
    content_text: str,
    mode: ModeLiteral,
    sections: Dict[str, bool],
    source_hash: str,
    source_type: str,
    duration_minutes: Optional[float] = None,
    questions: Optional[List[str]] = None,
) -> ExtractResponse:
    sections_key = json.dumps(sections, sort_keys=True, separators=(",", ":"))
    questions_key = ""
    if questions:
        questions_key = "|" + json.dumps(sorted(questions), separators=(",", ":"))
    cache_key = hashlib.sha256(
        f"{source_type}|{mode}|{sections_key}|{source_hash}|{PROMPT_VERSION}{questions_key}".encode("utf-8")
    ).hexdigest()

    try:
        cached = get_cached_insights(cache_key)
    except Exception as exc:
        logger.warning("Insights cache read failed key=%s: %s", cache_key[:10], exc)
        cached = None

    if cached and isinstance(cached.get("insights"), dict):
        logger.info("Insights cache hit key=%s mode=%s source=%s", cache_key[:10], mode, source_type)
        return ExtractResponse(
            mode=mode,
            word_count=int(cached.get("word_count") or len(content_text.split())),
            duration_minutes=duration_minutes,
            insights=cached["insights"],
            cache_hit=True,
        )

    try:
        insights = generate_insights(
            content=content_text,
            mode=mode,
            sections=sections,
            duration_minutes=duration_minutes or 0,
            source_type=source_type,
            questions=questions,
        )
    except Exception as exc:  # pragma: no cover
        logger.exception("Extraction failed for source=%s", source_type)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    word_count = len(content_text.split())
    serialized = insights.dict() if isinstance(insights, (StudyNotes, WorkBrief, VideoInsights)) else insights

    try:
        save_cached_insights(
            cache_key=cache_key,
            mode=mode,
            transcript_hash=source_hash,
            sections_key=sections_key,
            insights=serialized,
            word_count=word_count,
        )
    except Exception as exc:
        logger.warning("Insights cache write failed key=%s: %s", cache_key[:10], exc)

    return ExtractResponse(
        mode=mode,
        word_count=word_count,
        duration_minutes=duration_minutes,
        insights=serialized,
        cache_hit=False,
    )


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


class VerdictRequest(BaseModel):
    transcript: str = Field(..., description="Transcript text used to decide watch/skim/skip.")
    mode: ModeLiteral = Field("quick", description="User intent mode for verdict context.")


class VerdictResponse(BaseModel):
    verdict: str
    why: str
    best_for: str
    relevant_moments: List[str]
    what_youll_miss_if_skip: str


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
    timestamp_notes: Optional[List[PushTimestampNotePayload]] = Field(
        default=None,
        description="Optional timestamp notes to persist into the same Notion row workspace.",
    )


class PushResponse(BaseModel):
    """Response payload for /push endpoint."""

    status: str
    page_id: Optional[str] = None
    page_url: Optional[str] = None
    row_page_id: Optional[str] = None
    database_id: Optional[str] = None
    status_message: Optional[str] = None


class PushTimestampNotePayload(BaseModel):
    label: str
    seconds: int
    note: str
    title: Optional[str] = None


class TimestampNotePayload(BaseModel):
    label: str
    seconds: int
    note: str
    title: Optional[str] = None


class TimestampNotionRequest(BaseModel):
    mode: ModeLiteral = "study"
    source_url: str
    notes: List[TimestampNotePayload] = Field(default_factory=list)
    ai_summary: Optional[str] = None
    video_title: Optional[str] = None
    creator_name: Optional[str] = None
    notion_token: Optional[str] = None
    notion_page_id: Optional[str] = None
    session_id: Optional[str] = None


class TimestampNotionResponse(BaseModel):
    status: str
    page_id: str
    page_url: str


class CaptureMomentRequest(BaseModel):
    session_id: str
    video_url: str
    video_title: Optional[str] = None
    creator_name: Optional[str] = None
    seconds: int
    note: Optional[str] = None
    intent: Optional[str] = None
    mode: ModeLiteral = "study"


class CaptureMomentItem(BaseModel):
    label: str
    seconds: int
    note: str
    created_at: str


class CaptureMomentResponse(BaseModel):
    status: str
    total_moments: int
    moment: CaptureMomentItem


class CaptureMomentsResponse(BaseModel):
    status: str
    video_url: str
    video_title: Optional[str] = None
    creator_name: Optional[str] = None
    intent: Optional[str] = None
    mode: ModeLiteral = "study"
    moments: List[CaptureMomentItem] = Field(default_factory=list)


class SynthesisRequest(BaseModel):
    """Request payload for /synthesis endpoint."""

    session_ids: List[str] = Field(..., description="List of session IDs to synthesize")
    user_question: Optional[str] = Field(
        default=None,
        description="Optional context question the user is trying to answer by combining sources"
    )


class SynthesisResponse(BaseModel):
    """Response payload for /synthesis endpoint."""

    analysis: SynthesisAnalysis
    sources_count: int
    synthesis_cache_used: bool = False


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
app.include_router(smart_watch_router)
app.include_router(study_session_router)
app.include_router(unified_library_router)
PROMPT_VERSION = "v1"

# MVP in-memory capture store for extension in-player moments.
# Key: "session_id::video_id" -> payload with metadata and captured moments.
CAPTURE_STORE: Dict[str, Dict[str, Any]] = {}


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
        transcript, duration = get_youtube_transcript(
            video_id,
            allow_supadata=payload.allow_supadata,
        )
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
    transcript_hash = hashlib.sha256(transcript.encode("utf-8")).hexdigest()
    return _extract_with_cache(
        content_text=transcript,
        mode=payload.mode,
        sections=sections,
        source_hash=transcript_hash,
        source_type="video",
        duration_minutes=payload.duration_minutes,
        questions=payload.questions,
    )


@app.post("/extract/pdf", response_model=ExtractResponse)
async def extract_pdf(
    file: UploadFile = File(...),
    mode: ModeLiteral = Form("study"),
    session_id: str = Form(...),
    user_id: Optional[str] = Form(None),
    sections: Optional[str] = Form(None),
) -> ExtractResponse:
    if not session_id.strip():
        raise HTTPException(status_code=400, detail="session_id is required")
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=422,
            detail={"error": "pdf_unreadable", "message": "Could not read this PDF. Try a text-based PDF."},
        )
    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail={"error": "file_too_large", "message": "PDF must be under 10MB"},
        )

    try:
        _, text = extract_text_from_pdf(file_bytes)
    except Exception:
        raise HTTPException(
            status_code=422,
            detail={"error": "pdf_unreadable", "message": "Could not read this PDF. Try a text-based PDF."},
        )
    if not text.strip():
        raise HTTPException(
            status_code=422,
            detail={"error": "pdf_unreadable", "message": "Could not read this PDF. Try a text-based PDF."},
        )

    parsed_sections = {"summary": True, "key_takeaways": True, "topics": True, "action_items": True}
    if sections:
        try:
            candidate = json.loads(sections)
            if isinstance(candidate, dict):
                parsed_sections = candidate
        except Exception:
            pass

    source_hash = hashlib.sha256(file_bytes).hexdigest()
    return _extract_with_cache(
        content_text=text,
        mode=mode,
        sections=parsed_sections,
        source_hash=source_hash,
        source_type="pdf",
        duration_minutes=None,
    )


@app.post("/extract/article", response_model=ExtractResponse)
async def extract_article(payload: ArticleExtractRequest) -> ExtractResponse:
    url = payload.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="url is required")
    if not payload.session_id.strip():
        raise HTTPException(status_code=400, detail="session_id is required")

    try:
        _, text = extract_text_from_url(url)
    except Exception:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "article_unreadable",
                "message": "Could not extract content from this URL. The site may block automated access.",
            },
        )

    sections = payload.sections or {"summary": True, "key_takeaways": True, "topics": True, "action_items": True}
    source_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return _extract_with_cache(
        content_text=text,
        mode=payload.mode,
        sections=sections,
        source_hash=source_hash,
        source_type="article",
        duration_minutes=None,
    )
@app.get("/export/markdown")
async def export_markdown(
    session_id: str,
    source_url: str = ""
):
    """
    Fetches latest insight from insight_cache for this session
    and returns it as a Markdown string with suggested filename.
    """
    try:
        # Fetch from insight_cache using session_id
        result = get_latest_insight(session_id)

        if not result:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "no_analysis_found",
                    "message": "No analysis found for this session. "
                               "Process a video or document first."
                }
            )

        insights = result["insights"]
        md, filename = insights_to_markdown(insights, source_url)

        return {
            "markdown": md,
            "filename": filename
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "export_failed",
                "message": "Could not generate export. Please try again."
            }
        )

def _resolve_notion_credentials(
    token: Optional[str], page_id: Optional[str], session_id: Optional[str], mode: str
) -> Dict[str, Optional[str]]:
    """Resolve Notion credentials from direct payload or Supabase session."""
    resolved_token = token
    resolved_page_id = page_id
    session: Optional[Dict[str, Any]] = None

    def _page_is_active(target_page_id: Optional[str], target_token: Optional[str]) -> bool:
        if not target_page_id or not target_token:
            return False
        try:
            resp = requests.get(
                f"https://api.notion.com/v1/pages/{str(target_page_id).replace('-', '')}",
                headers={
                    "Authorization": f"Bearer {target_token}",
                    "Notion-Version": "2022-06-28",
                    "Content-Type": "application/json",
                },
                timeout=8,
            )
            if resp.status_code != 200:
                return False
            payload = resp.json()
            return not bool(payload.get("archived") or payload.get("in_trash"))
        except Exception:
            return False

    if session_id:
        session = get_session(session_id)
        if session:
            resolved_token = resolved_token or session.get("notion_token")

            if not resolved_page_id:
                resolved_page_id = session.get("notion_page_id")

                # Legacy fallback only if unified root is missing.
                if not resolved_page_id:
                    if mode == "study":
                        resolved_page_id = session.get("study_page_id")
                    elif mode == "work":
                        resolved_page_id = session.get("work_page_id")
                    elif mode == "quick":
                        resolved_page_id = session.get("quick_page_id")

            if resolved_page_id and resolved_token and not _page_is_active(resolved_page_id, resolved_token):
                logger.warning("Resolved Notion page is archived/inaccessible. Trying fallbacks.")
                fallback_candidates = [
                    session.get("notion_page_id") if session else None,
                    os.getenv("NOTION_PAGE_ID"),
                ]
                resolved_page_id = None
                for candidate in fallback_candidates:
                    if candidate and _page_is_active(candidate, resolved_token):
                        resolved_page_id = candidate
                        break

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


def _fetch_youtube_metadata(url: str) -> Dict[str, str]:
    if not url or "youtu" not in url.lower():
        return {}
    try:
        res = requests.get(
            "https://www.youtube.com/oembed",
            params={"url": url, "format": "json"},
            timeout=8,
        )
        if res.status_code != 200:
            return {}
        payload = res.json()
        title = str(payload.get("title") or "").strip()
        creator = str(payload.get("author_name") or "").strip()
        return {"title": title, "creator": creator}
    except Exception:
        return {}


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
    
    status_msg = None
    if payload.timestamp_notes:
        try:
            summary_hint = ""
            if payload.mode == "study":
                summary_hint = str(payload.insights.get("core_concept") or "")
            elif payload.mode == "work":
                summary_hint = str(
                    payload.insights.get("one_liner")
                    or payload.insights.get("recommendation")
                    or ""
                )
            else:
                summary_hint = str(payload.insights.get("summary") or payload.insights.get("title") or "")
    
            _, status_msg = push_timestamp_notes(
                mode=payload.mode,
                source_url=payload.video_url or "",
                timestamp_notes=[item.dict() for item in payload.timestamp_notes],
                ai_summary=summary_hint,
                video_title=str(payload.insights.get("title") or "") or None,
                creator_name=str(
                    payload.insights.get("creator") or payload.insights.get("creator_name") or ""
                )
                or None,
                notion_token=creds["token"],
                notion_page_id=page_id,
            )
        except Exception as exc:
            logger.warning("Timestamp note sync skipped for /push request: %s", exc)

    # Save to unified library
    try:
        video_id = extract_video_id(payload.video_url or "") if payload.video_url else None
        
        # Determine content type based on mode
        content_type_map = {
            "study": "youtube_study",
            "work": "youtube_work",
            "quick": "youtube_quick",
        }
        content_type = content_type_map.get(payload.mode, "youtube_quick")
        
        # Extract title and summary based on mode
        title = str(payload.insights.get("title") or "Untitled")
        summary = ""
        content_data = {}
        
        if payload.mode == "study":
            summary = str(payload.insights.get("core_concept") or "")
            content_data = {
                "core_concept": payload.insights.get("core_concept"),
                "formula_sheet": payload.insights.get("formula_sheet"),
                "key_facts": payload.insights.get("key_facts"),
                "common_mistakes": payload.insights.get("common_mistakes"),
                "self_test": payload.insights.get("self_test"),
                "prerequisites": payload.insights.get("prerequisites"),
                "further_reading": payload.insights.get("further_reading"),
                "moments": payload.insights.get("moments"),
            }
        elif payload.mode == "work":
            summary = str(payload.insights.get("one_liner") or "")
            content_data = {
                "one_liner": payload.insights.get("one_liner"),
                "recommendation": payload.insights.get("recommendation"),
                "key_points": payload.insights.get("key_points"),
                "tools_mentioned": payload.insights.get("tools_mentioned"),
                "decisions_to_make": payload.insights.get("decisions_to_make"),
                "next_actions": payload.insights.get("next_actions"),
                "moments": payload.insights.get("moments"),
            }
        else:  # quick mode
            summary = str(payload.insights.get("summary") or "")
            content_data = {
                "summary": payload.insights.get("summary"),
                "key_takeaways": payload.insights.get("key_takeaways"),
                "topics_covered": payload.insights.get("topics_covered"),
                "action_items": payload.insights.get("action_items"),
                "moments": payload.insights.get("moments"),
            }
        
        # Get user_id if available from session
        user_id = None
        if payload.session_id:
            session = get_session(payload.session_id)
            if session:
                user_id = session.get("user_id")
        
        # Save to library
        save_library_item(
            session_id=payload.session_id or "unknown",
            user_id=user_id,
            content_type=content_type,
            title=title,
            source_url=payload.video_url,
            video_id=video_id,
            summary=summary,
            content_data=content_data,
            notion_page_id=page_id,
        )
        logger.info(f"Saved {content_type} to library: {title}")
    except Exception as exc:
        logger.warning(f"Failed to save to library: {exc}")

    database_id = _resolve_parent_database_id(page_id, creds["token"]) if page_id else None
    return PushResponse(
        status="ok",
        page_id=page_id,
        page_url=_notion_page_url(page_id),
        row_page_id=page_id,
        database_id=database_id,
    )


def _notion_page_url(page_id: str) -> str:
    clean = (page_id or "").replace("-", "")
    return f"https://www.notion.so/{clean}" if clean else "https://www.notion.so"


def _resolve_parent_database_id(page_id: str, notion_token: str) -> Optional[str]:
    try:
        clean_id = (page_id or "").replace("-", "")
        if not clean_id:
            return None
        resp = requests.get(
            f"https://api.notion.com/v1/pages/{clean_id}",
            headers={
                "Authorization": f"Bearer {notion_token}",
                "Notion-Version": "2022-06-28",
            },
            timeout=10,
        )
        if resp.status_code != 200:
            return None
        parent = (resp.json() or {}).get("parent") or {}
        if parent.get("type") == "database_id":
            return parent.get("database_id")
        return None
    except Exception:
        return None


def _seconds_to_label(total_seconds: int) -> str:
    safe = max(0, int(total_seconds))
    hours = safe // 3600
    minutes = (safe % 3600) // 60
    seconds = safe % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def _capture_store_key(session_id: str, video_url: str) -> str:
    video_id = extract_video_id(video_url) or video_url.strip()
    return f"{session_id.strip()}::{video_id}"


def _get_or_init_capture_bucket(
    session_id: str,
    video_url: str,
    video_title: Optional[str],
    creator_name: Optional[str],
    intent: Optional[str],
    mode: ModeLiteral,
) -> Dict[str, Any]:
    key = _capture_store_key(session_id, video_url)
    bucket = CAPTURE_STORE.get(key)
    if bucket:
        if video_title and not bucket.get("video_title"):
            bucket["video_title"] = video_title
        if creator_name and not bucket.get("creator_name"):
            bucket["creator_name"] = creator_name
        if intent:
            bucket["intent"] = intent
        if mode:
            bucket["mode"] = mode
        return bucket

    bucket = {
        "session_id": session_id,
        "video_url": video_url,
        "video_title": video_title or "",
        "creator_name": creator_name or "",
        "intent": intent or "",
        "mode": mode,
        "moments": [],
    }
    CAPTURE_STORE[key] = bucket
    return bucket


@app.post("/capture/moment", response_model=CaptureMomentResponse)
async def capture_moment(payload: CaptureMomentRequest) -> CaptureMomentResponse:
    """Store one in-player captured timestamp moment for the current session/video."""
    session_id = payload.session_id.strip()
    video_url = payload.video_url.strip()
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    if not video_url:
        raise HTTPException(status_code=400, detail="video_url is required")

    safe_seconds = max(0, int(payload.seconds))
    note = (payload.note or "Captured in player").strip() or "Captured in player"

    bucket = _get_or_init_capture_bucket(
        session_id=session_id,
        video_url=video_url,
        video_title=payload.video_title,
        creator_name=payload.creator_name,
        intent=payload.intent,
        mode=payload.mode,
    )

    for existing in bucket["moments"]:
        if abs(int(existing.get("seconds", 0)) - safe_seconds) <= 2:
            existing["note"] = note
            existing["label"] = _seconds_to_label(safe_seconds)
            existing["created_at"] = datetime.now(timezone.utc).isoformat()
            moment = CaptureMomentItem(**existing)
            return CaptureMomentResponse(status="ok", total_moments=len(bucket["moments"]), moment=moment)

    created = {
        "label": _seconds_to_label(safe_seconds),
        "seconds": safe_seconds,
        "note": note,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    bucket["moments"].append(created)
    bucket["moments"].sort(key=lambda item: int(item.get("seconds", 0)))

    return CaptureMomentResponse(
        status="ok",
        total_moments=len(bucket["moments"]),
        moment=CaptureMomentItem(**created),
    )


@app.get("/capture/moments", response_model=CaptureMomentsResponse)
async def list_captured_moments(session_id: str, video_url: str) -> CaptureMomentsResponse:
    """Return all captured moments for a given session + video."""
    session_clean = session_id.strip()
    source_clean = video_url.strip()
    if not session_clean:
        raise HTTPException(status_code=400, detail="session_id is required")
    if not source_clean:
        raise HTTPException(status_code=400, detail="video_url is required")

    key = _capture_store_key(session_clean, source_clean)
    bucket = CAPTURE_STORE.get(key)

    if not bucket:
        return CaptureMomentsResponse(status="ok", video_url=source_clean, moments=[])

    moments = [CaptureMomentItem(**item) for item in bucket.get("moments", [])]
    return CaptureMomentsResponse(
        status="ok",
        video_url=bucket.get("video_url") or source_clean,
        video_title=bucket.get("video_title") or None,
        creator_name=bucket.get("creator_name") or None,
        intent=bucket.get("intent") or None,
        mode=bucket.get("mode") or "study",
        moments=moments,
    )


@app.post("/notion/timestamp-notes", response_model=TimestampNotionResponse)
@app.post("/timestamp-notes", response_model=TimestampNotionResponse)
async def push_timestamp_notes_endpoint(payload: TimestampNotionRequest) -> TimestampNotionResponse:
    """Create a dedicated Notion page for timestamp notes."""
    if not payload.source_url.strip():
        raise HTTPException(status_code=400, detail="source_url is required")

    creds = _resolve_notion_credentials(
        payload.notion_token, payload.notion_page_id, payload.session_id, payload.mode
    )

    if not creds["token"] or not creds["page_id"]:
        raise HTTPException(
            status_code=400,
            detail="Notion credentials are required via notion_token/notion_page_id or session_id.",
        )

    metadata = _fetch_youtube_metadata(payload.source_url)
    resolved_title = payload.video_title or metadata.get("title") or ""
    resolved_creator = payload.creator_name or metadata.get("creator") or ""

    notes_payload = [item.dict() for item in payload.notes]

    try:
        page_id = push_timestamp_notes(
            mode=payload.mode,
            source_url=payload.source_url,
            timestamp_notes=notes_payload,
            ai_summary=payload.ai_summary,
            video_title=resolved_title,
            creator_name=resolved_creator,
            notion_token=creds["token"],
            notion_page_id=creds["page_id"],
        )
    except Exception as exc:  # pragma: no cover
        logger.exception("Failed to push timestamp notes to Notion")
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return TimestampNotionResponse(
        status="ok",
        page_id=page_id,
        page_url=_notion_page_url(page_id),
    )


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


@app.post("/verdict", response_model=VerdictResponse)
async def pre_watch_verdict_endpoint(payload: VerdictRequest) -> VerdictResponse:
    transcript = payload.transcript.strip()
    if not transcript:
        raise HTTPException(status_code=400, detail="transcript must not be empty for verdict")

    verdict = get_pre_watch_verdict(transcript=transcript, mode=payload.mode)

    if isinstance(verdict, PreWatchVerdict):
        serialized = verdict.dict()
    else:
        serialized = verdict
    return VerdictResponse(**serialized)


@app.post("/synthesis", response_model=SynthesisResponse)
async def synthesize_sources(payload: SynthesisRequest) -> SynthesisResponse:
    """Generate unified analysis across multiple extraction sessions."""
    if not payload.session_ids or len(payload.session_ids) < 2:
        raise HTTPException(
            status_code=400,
            detail="Cross-source synthesis requires at least 2 session IDs"
        )

    # Fetch all insights from session cache
    insights_list = []
    titles_list = []
    
    for session_id in payload.session_ids:
        try:
            session = get_session(session_id)
            if session and session.get("latest_insights"):
                insights = session["latest_insights"]
                title = insights.get("title") or f"Source {len(insights_list) + 1}"
                insights_list.append(insights)
                titles_list.append(title)
        except Exception as e:
            logger.warning(f"Failed to fetch insights for session {session_id}: {e}")
            # Continue with other sessions even if one fails

    if not insights_list:
        raise HTTPException(
            status_code=404,
            detail="No insights found for the provided session IDs"
        )

    # Prepare context for synthesis
    from gemini import synthesize_insights
    
    context = {
        "sources": insights_list,
        "titles": titles_list,
        "user_question": payload.user_question
    }

    try:
        synthesis = synthesize_insights(**context)
        return SynthesisResponse(
            analysis=synthesis,
            sources_count=len(insights_list),
            synthesis_cache_used=False
        )
    except Exception as e:
        logger.exception("Synthesis failed")
        raise HTTPException(status_code=502, detail=f"Synthesis failed: {str(e)}")


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


