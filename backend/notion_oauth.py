"""FastAPI router implementing Notion OAuth authorization flow."""

from __future__ import annotations

import base64
import json
import os
import secrets
from typing import Dict, Optional

import requests
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from backend.supabase_client import get_session, save_session

load_dotenv()

NOTION_CLIENT_ID = os.getenv("NOTION_CLIENT_ID")
NOTION_CLIENT_SECRET = os.getenv("NOTION_CLIENT_SECRET")
NOTION_REDIRECT_URI = os.getenv("NOTION_REDIRECT_URI")
NOTION_OAUTH_URL = "https://api.notion.com/v1/oauth/authorize"
NOTION_TOKEN_URL = "https://api.notion.com/v1/oauth/token"
NOTION_SCOPES = os.getenv(
    "NOTION_OAUTH_SCOPES",
    "database.read,databases.read,databases.write,users.read",
)

router = APIRouter(prefix="/auth/notion", tags=["notion_oauth"])


def _require_oauth_env() -> None:
    """Ensure all required environment variables are present."""
    missing = [
        var
        for var in ["NOTION_CLIENT_ID", "NOTION_CLIENT_SECRET", "NOTION_REDIRECT_URI"]
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
        "session_id": session_id,
        "notion_page_id": notion_page_id,
        "nonce": secrets.token_hex(8),
    }
    encoded = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")
    return encoded


def _decode_state(state: str) -> Dict[str, Optional[str]]:
    """Decode a state string back into its payload."""
    try:
        decoded = base64.urlsafe_b64decode(state.encode("utf-8")).decode("utf-8")
        data = json.loads(decoded)
        if "session_id" not in data:
            raise ValueError("session_id missing from state payload")
        return data
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=400, detail="Invalid state parameter") from exc


class AuthStartResponse(BaseModel):
    """Response containing the URL to redirect users to Notion consent."""

    auth_url: str


class AuthCallbackResponse(BaseModel):
    """Response after successfully exchanging a code for a token."""

    status: str
    session_id: str
    workspace_name: Optional[str] = None


class AuthStatusResponse(BaseModel):
    """OAuth status payload."""

    session_id: str
    has_token: bool
    notion_page_id: Optional[str] = None


def _auth_params(
    session_id: str = Query(..., description="Client-generated session identifier"),
    notion_page_id: Optional[str] = Query(
        default=None,
        description="Optional Notion page ID supplied during auth to persist alongside token.",
    ),
) -> Dict[str, Optional[str]]:
    """Dependency for extracting auth query params."""
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    return {"session_id": session_id, "notion_page_id": notion_page_id}


@router.get("", response_model=None)
def start_auth(params: Dict[str, Optional[str]] = Depends(_auth_params)) -> RedirectResponse:
    """Redirect the requester to the Notion OAuth authorization URL."""
    _require_oauth_env()
    state = _encode_state(params["session_id"], params["notion_page_id"])
    scopes = NOTION_SCOPES.replace(" ", "")
    auth_url = (
        f"{NOTION_OAUTH_URL}"
        f"?client_id={NOTION_CLIENT_ID}"
        f"&response_type=code"
        f"&owner=user"
        f"&redirect_uri={NOTION_REDIRECT_URI}"
        f"&scope={scopes}"
        f"&state={state}"
    )
    return RedirectResponse(url=auth_url)


@router.get("/callback", response_model=AuthCallbackResponse)
def oauth_callback(code: str = Query(...), state: str = Query(...)) -> AuthCallbackResponse:
    """Handle OAuth callback, exchange code for token, and store session."""
    _require_oauth_env()
    state_payload = _decode_state(state)
    session_id = state_payload["session_id"]
    notion_page_id = state_payload.get("notion_page_id")

    token_payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": NOTION_REDIRECT_URI,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {base64.b64encode(f'{NOTION_CLIENT_ID}:{NOTION_CLIENT_SECRET}'.encode()).decode()}",
    }

    response = requests.post(NOTION_TOKEN_URL, json=token_payload, headers=headers, timeout=15)
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to exchange code for token.")

    data = response.json()
    access_token = data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=502, detail="Notion response missing access_token.")

    workspace_name = data.get("workspace_name")
    save_session(session_id, access_token, notion_page_id or "")

    return AuthCallbackResponse(
        status="ok",
        session_id=session_id,
        workspace_name=workspace_name,
    )


@router.get("/status/{session_id}", response_model=AuthStatusResponse)
def auth_status(session_id: str) -> AuthStatusResponse:
    """Check whether a session has a stored Notion token."""
    session = get_session(session_id)
    has_token = bool(session and session.get("notion_token"))
    return AuthStatusResponse(
        session_id=session_id,
        has_token=has_token,
        notion_page_id=session.get("notion_page_id") if session else None,
    )
