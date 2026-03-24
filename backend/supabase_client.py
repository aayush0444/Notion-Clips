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
) -> Dict[str, Any]:
    """Insert or upsert a session row."""
    client = _get_client()
    payload = {
        "session_id": session_id,
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
