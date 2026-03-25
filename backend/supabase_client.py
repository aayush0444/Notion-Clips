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

_client: Optional[Client] = None


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
