"""FastAPI router implementing Notion OAuth authorization flow."""

from __future__ import annotations

import base64
import json
import os
import secrets
import logging
from typing import Dict, Optional

import requests
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from backend.supabase_client import get_session, save_session

load_dotenv()

logger = logging.getLogger("notionclips.notion_oauth")

NOTION_CLIENT_ID     = os.getenv("NOTION_CLIENT_ID")
NOTION_CLIENT_SECRET = os.getenv("NOTION_CLIENT_SECRET")
NOTION_REDIRECT_URI  = os.getenv("NOTION_REDIRECT_URI")
NOTION_OAUTH_URL     = "https://api.notion.com/v1/oauth/authorize"
NOTION_TOKEN_URL     = "https://api.notion.com/v1/oauth/token"

router = APIRouter(prefix="/auth/notion", tags=["notion_oauth"])


def _require_oauth_env() -> None:
    """Ensure all required OAuth environment variables are present."""
    missing = [
        var for var in ["NOTION_CLIENT_ID", "NOTION_CLIENT_SECRET", "NOTION_REDIRECT_URI"]
        if not os.getenv(var)
    ]
    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"Missing Notion OAuth environment variables: {', '.join(missing)}",
        )


def _encode_state(session_id: str, notion_page_id: Optional[str]) -> str:
    """Encode session information into a URL-safe state string."""
    payload = {
        "session_id":     session_id,
        "notion_page_id": notion_page_id,
        "nonce":          secrets.token_hex(8),
    }
    return base64.urlsafe_b64encode(
        json.dumps(payload).encode("utf-8")
    ).decode("utf-8")


def _decode_state(state: str) -> Dict[str, Optional[str]]:
    """Decode a state string back into its payload."""
    try:
        decoded = base64.urlsafe_b64decode(state.encode("utf-8")).decode("utf-8")
        data = json.loads(decoded)
        if "session_id" not in data:
            raise ValueError("session_id missing from state payload")
        return data
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid state parameter") from exc


class AuthStatusResponse(BaseModel):
    """OAuth status payload."""
    session_id:     str
    has_token:      bool
    notion_page_id: Optional[str] = None


def _auth_params(
    session_id: str = Query(..., description="Client-generated session identifier"),
    notion_page_id: Optional[str] = Query(default=None),
) -> Dict[str, Optional[str]]:
    """Dependency for extracting auth query params."""
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    return {"session_id": session_id, "notion_page_id": notion_page_id}


@router.get("", response_model=None)
def start_auth(
    params: Dict[str, Optional[str]] = Depends(_auth_params),
) -> RedirectResponse:
    """Redirect browser to Notion OAuth consent page.

    redirect_uri is intentionally NOT included in the authorization URL.
    Notion uses the redirect URI registered in the integration settings.
    Including it in the URL causes a mismatch error.
    """
    _require_oauth_env()
    state = _encode_state(params["session_id"], params["notion_page_id"])

    auth_url = (
        f"{NOTION_OAUTH_URL}"
        f"?client_id={NOTION_CLIENT_ID}"
        f"&response_type=code"
        f"&owner=user"
        f"&state={state}"
    )
    return RedirectResponse(url=auth_url)


@router.get("/callback", response_model=None)
def oauth_callback(
    code:  str = Query(...),
    state: str = Query(...),
) -> RedirectResponse:
    """Handle Notion OAuth callback, exchange code for token, store session,
    then redirect user back to the frontend app page."""
    _require_oauth_env()
    state_payload  = _decode_state(state)
    session_id     = state_payload["session_id"]
    notion_page_id = state_payload.get("notion_page_id")

    # Exchange code for access token
    # Note: redirect_uri is NOT included here because it was not
    # included in the authorize URL — they must match
    token_payload = {
        "grant_type": "authorization_code",
        "code":       code,
    }
    auth_header = base64.b64encode(
        f"{NOTION_CLIENT_ID}:{NOTION_CLIENT_SECRET}".encode()
    ).decode()
    headers = {
        "Content-Type":  "application/json",
        "Authorization": f"Basic {auth_header}",
    }

    response = requests.post(
        NOTION_TOKEN_URL,
        json=token_payload,
        headers=headers,
        timeout=15,
    )
    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to exchange code for token: {response.text}",
        )

    data         = response.json()
    access_token = data.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=502,
            detail="Notion response missing access_token.",
        )

    root_page_id = ""
    study_page_id = ""
    work_page_id = ""
    quick_page_id = ""

    page_headers = {
        "Authorization": f"Bearer {access_token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }

    try:
        root_payload = {
            "parent": {"type": "workspace", "workspace": True},
            "icon": {"type": "emoji", "emoji": "🧠"},
            "properties": {
                "title": [{"type": "text", "text": {"content": "NotionClip Notes"}}]
            },
        }
        root_resp = requests.post(
            "https://api.notion.com/v1/pages",
            headers=page_headers,
            json=root_payload,
            timeout=15,
        )
        root_resp.raise_for_status()
        root_page_id = root_resp.json().get("id", "")
    except Exception as exc:  # pragma: no cover
        logger.exception("Failed to create root NotionClip Notes page: %s", exc)

    def _create_child(title: str, emoji: str) -> str:
        if not root_page_id:
            return ""
        try:
            child_payload = {
                "parent": {"type": "page_id", "page_id": root_page_id},
                "icon": {"type": "emoji", "emoji": emoji},
                "properties": {
                    "title": [{"type": "text", "text": {"content": title}}]
                },
            }
            child_resp = requests.post(
                "https://api.notion.com/v1/pages",
                headers=page_headers,
                json=child_payload,
                timeout=15,
            )
            child_resp.raise_for_status()
            return child_resp.json().get("id", "") or ""
        except Exception as exc:  # pragma: no cover
            logger.exception("Failed to create child page %s: %s", title, exc)
            return ""

    study_page_id = _create_child("Study Notes", "📚")
    work_page_id = _create_child("Work Briefs", "💼")
    quick_page_id = _create_child("Quick Saves", "⚡")

    save_session(session_id, access_token, root_page_id, study_page_id, work_page_id, quick_page_id)

    # Redirect back to frontend — store.tsx detects ?connected=true
    # and sets isConnected=true automatically
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    return RedirectResponse(url=f"{frontend_url}/app?connected=true")


@router.get("/status/{session_id}", response_model=AuthStatusResponse)
def auth_status(session_id: str) -> AuthStatusResponse:
    """Check whether a session has a stored Notion token."""
    session   = get_session(session_id)
    has_token = bool(session and session.get("notion_token"))
    return AuthStatusResponse(
        session_id=session_id,
        has_token=has_token,
        notion_page_id=session.get("notion_page_id") if session else None,
    )
