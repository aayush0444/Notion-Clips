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
    payload = {
        "session_id":     session_id,
        "notion_page_id": notion_page_id,
        "nonce":          secrets.token_hex(8),
    }
    return base64.urlsafe_b64encode(
        json.dumps(payload).encode("utf-8")
    ).decode("utf-8")


def _decode_state(state: str) -> Dict[str, Optional[str]]:
    try:
        decoded = base64.urlsafe_b64decode(state.encode("utf-8")).decode("utf-8")
        data = json.loads(decoded)
        if "session_id" not in data:
            raise ValueError("session_id missing from state payload")
        return data
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid state parameter") from exc


class AuthStatusResponse(BaseModel):
    session_id:     str
    has_token:      bool
    notion_page_id: Optional[str] = None


def _auth_params(
    session_id: str = Query(...),
    notion_page_id: Optional[str] = Query(default=None),
) -> Dict[str, Optional[str]]:
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    return {"session_id": session_id, "notion_page_id": notion_page_id}


def _notion_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }


def _find_or_create_root_page(token: str) -> str:
    """
    Strategy:
    1. Search if 'NotionClip Notes' already exists — reuse it if found.
    2. Try creating a workspace-level page.
    3. If both fail, return empty string — push will fail gracefully.
    """
    headers = _notion_headers(token)

    # ── Step 1: Search for existing page ────────────────────────────────────
    try:
        search_resp = requests.post(
            "https://api.notion.com/v1/search",
            headers=headers,
            json={"query": "NotionClip Notes", "filter": {"property": "object", "value": "page"}},
            timeout=10,
        )
        print(f"[SEARCH] status={search_resp.status_code} body={search_resp.text[:300]}")
        if search_resp.status_code == 200:
            results = search_resp.json().get("results", [])
            for r in results:
                title_list = r.get("properties", {}).get("title", {}).get("title", [])
                title_text = "".join(t.get("plain_text", "") for t in title_list)
                if "NotionClip" in title_text:
                    found_id = r.get("id", "")
                    print(f"[SEARCH] Found existing page: {found_id}")
                    return found_id
    except Exception as e:
        print(f"[SEARCH] Exception: {e}")

    # ── Step 2: Create workspace-level page ──────────────────────────────────
    try:
        create_resp = requests.post(
            "https://api.notion.com/v1/pages",
            headers=headers,
            json={
                "parent": {"type": "workspace", "workspace": True},
                "icon": {"type": "emoji", "emoji": "🧠"},
                "properties": {
                    "title": [{"type": "text", "text": {"content": "NotionClip Notes"}}]
                },
            },
            timeout=10,
        )
        print(f"[CREATE ROOT] status={create_resp.status_code} body={create_resp.text[:400]}")
        if create_resp.status_code == 200:
            page_id = create_resp.json().get("id", "")
            print(f"[CREATE ROOT] Success: {page_id}")
            return page_id
        else:
            print(f"[CREATE ROOT] Failed — {create_resp.status_code}: {create_resp.text[:300]}")
    except Exception as e:
        print(f"[CREATE ROOT] Exception: {e}")

    return ""


def _create_child_page(token: str, parent_id: str, title: str, emoji: str) -> str:
    """Create a child page under parent_id. Returns page ID or empty string."""
    if not parent_id:
        print(f"[CREATE CHILD] Skipping {title} — no parent_id")
        return ""
    try:
        resp = requests.post(
            "https://api.notion.com/v1/pages",
            headers=_notion_headers(token),
            json={
                "parent": {"type": "page_id", "page_id": parent_id},
                "icon": {"type": "emoji", "emoji": emoji},
                "properties": {
                    "title": [{"type": "text", "text": {"content": title}}]
                },
            },
            timeout=10,
        )
        print(f"[CREATE CHILD '{title}'] status={resp.status_code} body={resp.text[:300]}")
        if resp.status_code == 200:
            page_id = resp.json().get("id", "")
            print(f"[CREATE CHILD '{title}'] Success: {page_id}")
            return page_id
        return ""
    except Exception as e:
        print(f"[CREATE CHILD '{title}'] Exception: {e}")
        return ""


@router.get("", response_model=None)
def start_auth(
    params: Dict[str, Optional[str]] = Depends(_auth_params),
) -> RedirectResponse:
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
    _require_oauth_env()
    state_payload = _decode_state(state)
    session_id    = state_payload["session_id"]

    # Exchange code for token
    auth_header = base64.b64encode(
        f"{NOTION_CLIENT_ID}:{NOTION_CLIENT_SECRET}".encode()
    ).decode()

    response = requests.post(
        NOTION_TOKEN_URL,
        json={"grant_type": "authorization_code", "code": code},
        headers={"Content-Type": "application/json", "Authorization": f"Basic {auth_header}"},
        timeout=15,
    )

    print(f"[TOKEN EXCHANGE] status={response.status_code}")
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Token exchange failed: {response.text}")

    data         = response.json()
    access_token = data.get("access_token", "")
    if not access_token:
        raise HTTPException(status_code=502, detail="Notion response missing access_token.")

    print(f"[TOKEN EXCHANGE] token prefix={access_token[:20]} workspace={data.get('workspace_name')}")

    # Create page structure
    root_page_id  = _find_or_create_root_page(access_token)
    study_page_id = _create_child_page(access_token, root_page_id, "Study Notes", "📚")
    work_page_id  = _create_child_page(access_token, root_page_id, "Work Briefs", "💼")
    quick_page_id = _create_child_page(access_token, root_page_id, "Quick Saves", "⚡")

    print(f"[SESSION SAVE] root={root_page_id} study={study_page_id} work={work_page_id} quick={quick_page_id}")

    save_session(session_id, access_token, root_page_id, study_page_id, work_page_id, quick_page_id)

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    return RedirectResponse(url=f"{frontend_url}/app?connected=true")


@router.get("/status/{session_id}", response_model=AuthStatusResponse)
def auth_status(session_id: str) -> AuthStatusResponse:
    session   = get_session(session_id)
    has_token = bool(session and session.get("notion_token"))
    return AuthStatusResponse(
        session_id=session_id,
        has_token=has_token,
        notion_page_id=session.get("notion_page_id") if session else None,
    )