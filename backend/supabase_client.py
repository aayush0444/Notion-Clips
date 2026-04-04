"""Supabase session storage helpers for Notion OAuth tokens."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SESSIONS_TABLE = os.getenv("SUPABASE_SESSIONS_TABLE", "sessions")
TRANSCRIPTS_TABLE = os.getenv("SUPABASE_TRANSCRIPTS_TABLE", "transcript_cache")
INSIGHTS_TABLE = os.getenv("SUPABASE_INSIGHTS_TABLE", "insight_cache")
SMART_WATCH_TABLE = os.getenv("SUPABASE_SMART_WATCH_TABLE", "smart_watch_analyses")
STUDY_SESSIONS_TABLE = os.getenv("SUPABASE_STUDY_SESSIONS_TABLE", "study_sessions")
LIBRARY_TABLE = os.getenv("SUPABASE_LIBRARY_TABLE", "user_library")

_client: Optional[Client] = None

def get_latest_insight(session_id: str):
    """
    Fetches the most recent insight from insight_cache
    for this session_id. Returns None if not found.
    """
    try:
        client = _get_client()
        result = (
            client.table("insight_cache")
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", desc=True)
            .limit(1)
            .maybe_single()
            .execute()
        )
        return result.data if result.data else None
    except Exception:
        return None
def _get_client() -> Client:
    """Lazy-load Supabase client to avoid import side effects during testing."""
    global _client  # pylint: disable=global-statement
    if _client:
        return _client
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise RuntimeError("Supabase credentials are not configured in environment variables.")
    _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _client


def save_session(
    session_id: str,
    token: str,
    page_id: str,
    study_page_id: str,
    work_page_id: str,
    quick_page_id: str,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Insert or upsert a session row."""
    client = _get_client()
    payload = {
        "session_id": session_id,
        "user_id": user_id,
        "notion_token": token,
        "notion_page_id": page_id,
        "study_page_id": study_page_id,
        "work_page_id": work_page_id,
        "quick_page_id": quick_page_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    response = (
        client.table(SESSIONS_TABLE)
        .upsert(payload, on_conflict="session_id")
        .execute()
    )
    return response.data[0] if response.data else payload


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a session from Supabase by session_id."""
    try:
        client = _get_client()
        response = (
            client.table(SESSIONS_TABLE)
            .select("*")
            .eq("session_id", session_id)
            .maybe_single()
            .execute()
        )
        return response.data
    except Exception:
        return None


def get_user_id_from_bearer_token(authorization_header: Optional[str]) -> Optional[str]:
    """Resolve Supabase user id from Authorization: Bearer <jwt> header."""
    if not authorization_header:
        return None
    if not authorization_header.lower().startswith("bearer "):
        return None
    token = authorization_header.split(" ", 1)[1].strip()
    if not token:
        return None
    try:
        client = _get_client()
        user_response = client.auth.get_user(token)
        user = getattr(user_response, "user", None)
        user_id = getattr(user, "id", None)
        return user_id if isinstance(user_id, str) and user_id else None
    except Exception:
        return None


def get_cached_transcript(video_id: str) -> Optional[Dict[str, Any]]:
    """Fetch cached transcript data by canonical YouTube video_id."""
    client = _get_client()
    response = (
        client.table(TRANSCRIPTS_TABLE)
        .select("*")
        .eq("video_id", video_id)
        .maybe_single()
        .execute()
    )
    return response.data


def save_cached_transcript(video_id: str, transcript: str, duration_minutes: float) -> Dict[str, Any]:
    """Upsert transcript cache row for a YouTube video."""
    client = _get_client()
    payload = {
        "video_id": video_id,
        "transcript": transcript,
        "duration_minutes": duration_minutes,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    response = (
        client.table(TRANSCRIPTS_TABLE)
        .upsert(payload, on_conflict="video_id")
        .execute()
    )
    return response.data[0] if response.data else payload


def get_cached_insights(cache_key: str) -> Optional[Dict[str, Any]]:
    """Fetch cached extraction insights by cache_key."""
    client = _get_client()
    response = (
        client.table(INSIGHTS_TABLE)
        .select("*")
        .eq("cache_key", cache_key)
        .maybe_single()
        .execute()
    )
    return response.data


def save_cached_insights(
    cache_key: str,
    mode: str,
    transcript_hash: str,
    sections_key: str,
    insights: Dict[str, Any],
    word_count: int,
) -> Dict[str, Any]:
    """Upsert extracted insights cache row."""
    client = _get_client()
    payload = {
        "cache_key": cache_key,
        "mode": mode,
        "transcript_hash": transcript_hash,
        "sections_key": sections_key,
        "insights": insights,
        "word_count": word_count,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    response = (
        client.table(INSIGHTS_TABLE)
        .upsert(payload, on_conflict="cache_key")
        .execute()
    )
    return response.data[0] if response.data else payload


def save_smart_watch_analysis(
    session_id: str,
    video_id: str,
    video_url: str,
    user_question: str,
    verdict: Optional[str] = None,
    confidence: Optional[float] = None,
    reason: Optional[str] = None,
    user_id: Optional[str] = None,
    video_title: Optional[str] = None,
    estimated_timestamp_range: Optional[str] = None,
    relevant_moments: Optional[list] = None,
    stage1_ms: Optional[int] = None,
    stage2_ms: Optional[int] = None,
) -> Dict[str, Any]:
    """Insert a Smart Watch analysis row with explicit typed fields."""
    client = _get_client()
    record: Dict[str, Any] = {
        "session_id": session_id,
        "video_id": video_id,
        "video_url": video_url,
        "user_question": user_question,
        "verdict": verdict,
        "confidence": confidence,
        "reason": reason,
        "user_id": user_id,
        "video_title": video_title,
        "estimated_timestamp_range": estimated_timestamp_range,
        "relevant_moments": relevant_moments or [],
        "stage1_ms": stage1_ms,
        "stage2_ms": stage2_ms,
    }
    record = {k: v for k, v in record.items() if v is not None}
    record["created_at"] = datetime.now(timezone.utc).isoformat()
    response = client.table(SMART_WATCH_TABLE).insert(record).execute()
    return response.data[0] if response.data else record


def track_analytics_event(
    session_id: str,
    event_name: str,
    user_id: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Track lightweight product analytics in the shared insight cache table."""
    client = _get_client()
    event_payload = {
        "cache_key": f"event::{event_name}::{datetime.now(timezone.utc).timestamp()}::{session_id}",
        "mode": "analytics",
        "transcript_hash": session_id,
        "sections_key": event_name,
        "insights": {
            "event_name": event_name,
            "session_id": session_id,
            "user_id": user_id,
            "payload": payload or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        "word_count": 0,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    response = client.table(INSIGHTS_TABLE).insert(event_payload).execute()
    return response.data[0] if response.data else event_payload


def list_smart_watch_analyses(
    session_id: str,
    user_id: Optional[str] = None,
    limit: int = 30,
) -> list[Dict[str, Any]]:
    """List latest Smart Watch analyses for a user (or session fallback)."""
    client = _get_client()
    safe_limit = max(1, min(int(limit), 100))
    query = (
        client.table(SMART_WATCH_TABLE)
        .select("*")
        .order("created_at", desc=True)
        .limit(safe_limit)
    )
    if user_id:
        query = query.eq("user_id", user_id)
    else:
        query = query.eq("session_id", session_id)
    response = query.execute()
    return response.data or []


def list_analytics_events(
    session_id: str,
    user_id: Optional[str] = None,
    limit: int = 200,
) -> list[Dict[str, Any]]:
    """Read analytics events stored in insight cache table."""
    client = _get_client()
    safe_limit = max(1, min(int(limit), 500))
    query = (
        client.table(INSIGHTS_TABLE)
        .select("*")
        .eq("mode", "analytics")
        .order("updated_at", desc=True)
        .limit(safe_limit)
    )
    if user_id:
        query = query.eq("insights->>user_id", user_id)
    else:
        query = query.eq("transcript_hash", session_id)
    response = query.execute()
    return response.data or []


def create_study_session(
    user_id: Optional[str],
    session_id: str,
    learning_goal: str,
    student_level: str,
    sources: list
) -> str:
    """Creates session row, returns study_session_id."""
    client = _get_client()
    payload = {
        "user_id": user_id,
        "session_id": session_id,
        "learning_goal": learning_goal,
        "student_level": student_level,
        "sources": sources,
        "status": "building",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    response = client.table(STUDY_SESSIONS_TABLE).insert(payload).execute()
    if response.data and response.data[0].get("id"):
        return response.data[0]["id"]
    raise ValueError("Failed to create study session")


def get_study_session(study_session_id: str) -> Optional[dict]:
    """Fetches full session row. Returns None if not found."""
    client = _get_client()
    response = (
        client.table(STUDY_SESSIONS_TABLE)
        .select("*")
        .eq("id", study_session_id)
        .maybe_single()
        .execute()
    )
    return response.data if response else None


def update_study_session(
    study_session_id: str,
    updates: dict
) -> None:
    """
    Partial update — only keys present in updates dict are changed.
    Always sets updated_at = now().
    """
    client = _get_client()
    payload = dict(updates)
    payload["updated_at"] = datetime.now(timezone.utc).isoformat()
    client.table(STUDY_SESSIONS_TABLE).update(payload).eq("id", study_session_id).execute()


def append_qa_history(
    study_session_id: str,
    qa_entry: dict
) -> None:
    """
    Appends one entry to qa_history jsonb array.
    Uses Supabase's jsonb concatenation:
    qa_history = qa_history || '[{entry}]'::jsonb
    """
    client = _get_client()
    current = (
        client.table(STUDY_SESSIONS_TABLE)
        .select("qa_history")
        .eq("id", study_session_id)
        .maybe_single()
        .execute()
    )
    history = (current.data or {}).get("qa_history") if current else None
    if not isinstance(history, list):
        history = []
    history.append(qa_entry)
    client.table(STUDY_SESSIONS_TABLE).update(
        {"qa_history": history, "updated_at": datetime.now(timezone.utc).isoformat()}
    ).eq("id", study_session_id).execute()


# ============================================================================
# UNIFIED LIBRARY FUNCTIONS
# ============================================================================

def save_library_item(
    session_id: str,
    content_type: str,
    title: str,
    user_id: Optional[str] = None,
    source_url: Optional[str] = None,
    video_id: Optional[str] = None,
    summary: Optional[str] = None,
    content_data: Optional[Dict[str, Any]] = None,
    notion_page_id: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> Dict[str, Any]:
    """
    Save an item to the user's unified library.
    
    Args:
        session_id: Session identifier
        content_type: Type of content (youtube_study, youtube_work, youtube_quick, smart_watch, study_session)
        title: Item title
        user_id: Optional user ID (if authenticated)
        source_url: Optional source URL (YouTube, etc.)
        video_id: Optional video ID
        summary: Optional one-line summary
        content_data: Optional structured content (jsonb)
        notion_page_id: Optional Notion page ID
        tags: Optional list of tags
    
    Returns:
        The created library item
    """
    client = _get_client()
    
    item_data = {
        "session_id": session_id,
        "content_type": content_type,
        "title": title,
        "summary": summary or "",
        "content_data": content_data or {},
        "tags": tags or [],
    }
    
    if user_id:
        item_data["user_id"] = user_id
    if source_url:
        item_data["source_url"] = source_url
    if video_id:
        item_data["video_id"] = video_id
    if notion_page_id:
        item_data["notion_page_id"] = notion_page_id
    
    response = client.table(LIBRARY_TABLE).insert(item_data).execute()
    
    if not response.data:
        raise RuntimeError("Failed to save library item")
    
    return response.data[0]


def list_library_items(
    session_id: str,
    user_id: Optional[str] = None,
    content_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """
    List library items for a user/session with optional filtering.
    
    Args:
        session_id: Session identifier
        user_id: Optional user ID (if authenticated)
        content_type: Optional filter by content type
        limit: Maximum items to return (default 50, max 100)
        offset: Offset for pagination
    
    Returns:
        Dict with 'items', 'total', and 'has_more' keys
    """
    client = _get_client()
    safe_limit = max(1, min(int(limit), 100))
    
    # Build query
    query = client.table(LIBRARY_TABLE).select("*", count="exact")
    
    # Filter by user or session
    if user_id:
        query = query.eq("user_id", user_id)
    else:
        query = query.eq("session_id", session_id)
    
    # Filter by content type if specified
    if content_type:
        query = query.eq("content_type", content_type)
    
    # Apply ordering and pagination
    query = query.order("created_at", desc=True).range(offset, offset + safe_limit - 1)
    
    response = query.execute()
    
    items = response.data or []
    total = response.count or 0
    has_more = (offset + safe_limit) < total
    
    return {
        "items": items,
        "total": total,
        "has_more": has_more,
    }


def get_library_item(
    item_id: str,
    session_id: str,
    user_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Get a single library item by ID.
    
    Args:
        item_id: Library item UUID
        session_id: Session identifier
        user_id: Optional user ID (if authenticated)
    
    Returns:
        The library item or None if not found
    """
    client = _get_client()
    
    query = client.table(LIBRARY_TABLE).select("*").eq("id", item_id)
    
    # Ensure user can only access their own items
    if user_id:
        query = query.eq("user_id", user_id)
    else:
        query = query.eq("session_id", session_id)
    
    response = query.maybe_single().execute()
    
    return response.data


def delete_library_item(
    item_id: str,
    session_id: str,
    user_id: Optional[str] = None,
) -> bool:
    """
    Delete a library item by ID.
    
    Args:
        item_id: Library item UUID
        session_id: Session identifier
        user_id: Optional user ID (if authenticated)
    
    Returns:
        True if deleted, False if not found
    """
    client = _get_client()
    
    query = client.table(LIBRARY_TABLE).delete().eq("id", item_id)
    
    # Ensure user can only delete their own items
    if user_id:
        query = query.eq("user_id", user_id)
    else:
        query = query.eq("session_id", session_id)
    
    response = query.execute()
    
    return len(response.data or []) > 0


def search_library_items(
    session_id: str,
    query: str,
    user_id: Optional[str] = None,
    content_type: Optional[str] = None,
    limit: int = 50,
) -> Dict[str, Any]:
    """
    Search library items by text query.
    
    Args:
        session_id: Session identifier
        query: Search query string
        user_id: Optional user ID (if authenticated)
        content_type: Optional filter by content type
        limit: Maximum items to return
    
    Returns:
        Dict with 'items' and 'total' keys
    """
    client = _get_client()
    safe_limit = max(1, min(int(limit), 100))
    
    # Use PostgreSQL full-text search
    search_query = client.table(LIBRARY_TABLE).select("*", count="exact")
    
    # Filter by user or session
    if user_id:
        search_query = search_query.eq("user_id", user_id)
    else:
        search_query = search_query.eq("session_id", session_id)
    
    # Filter by content type if specified
    if content_type:
        search_query = search_query.eq("content_type", content_type)
    
    # Full-text search using textSearch
    search_query = search_query.text_search("title", query, config="english")
    
    # Apply ordering and limit
    search_query = search_query.order("created_at", desc=True).limit(safe_limit)
    
    response = search_query.execute()
    
    items = response.data or []
    total = response.count or 0
    
    return {
        "items": items,
        "total": total,
    }
