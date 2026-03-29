"""FastAPI router implementing Notion OAuth authorization flow."""

from __future__ import annotations

import base64
import json
import os
import secrets
import logging
from typing import Dict, Optional
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from backend.supabase_client import get_session, save_session

load_dotenv()

logger = logging.getLogger("notionclips.notion_oauth")

NOTION_OAUTH_URL     = "https://api.notion.com/v1/oauth/authorize"
NOTION_TOKEN_URL     = "https://api.notion.com/v1/oauth/token"

router = APIRouter(prefix="/auth/notion", tags=["notion_oauth"])


def _safe_frontend_base(frontend_url: Optional[str]) -> str:
    url = frontend_url or os.getenv("FRONTEND_URL", "http://localhost:3000")
    if not isinstance(url, str) or not url.strip():
        return "http://localhost:3000"
    return url.rstrip("/")


def _frontend_redirect(frontend_url: Optional[str], connected: bool, error: Optional[str] = None) -> RedirectResponse:
    base = _safe_frontend_base(frontend_url)
    query: Dict[str, str] = {"connected": "true" if connected else "false"}
    if error:
        query["error"] = error
    return RedirectResponse(url=f"{base}/app?{urlencode(query)}")


def _oauth_config(request: Optional[Request] = None) -> tuple[str, str, str]:
    client_id = os.getenv("NOTION_CLIENT_ID")
    client_secret = os.getenv("NOTION_CLIENT_SECRET")
    redirect_uri = os.getenv("NOTION_REDIRECT_URI")

    # Prefer explicit backend base URL when redirect is not configured.
    if not redirect_uri:
        backend_base = (
            os.getenv("PUBLIC_BACKEND_URL")
            or os.getenv("BACKEND_BASE_URL")
            or os.getenv("API_BASE_URL")
            or os.getenv("NEXT_PUBLIC_API_URL")
        )
        if backend_base:
            redirect_uri = f"{backend_base.rstrip('/')}/auth/notion/callback"

    # As a last resort, derive from the incoming request with forwarded headers.
    if not redirect_uri and request is not None:
        proto = request.headers.get("x-forwarded-proto", request.url.scheme)
        host = request.headers.get("x-forwarded-host") or request.headers.get("host")
        if host:
            redirect_uri = f"{proto}://{host}/auth/notion/callback"
            logger.warning("NOTION_REDIRECT_URI missing; using forwarded host %s", redirect_uri)
        else:
            base_url = str(request.base_url).rstrip("/")
            redirect_uri = f"{base_url}/auth/notion/callback"
            logger.warning("NOTION_REDIRECT_URI missing; using request base %s", redirect_uri)

    if redirect_uri:
        redirect_uri = redirect_uri.strip()
    missing = [
        name
        for name, value in (
            ("NOTION_CLIENT_ID", client_id),
            ("NOTION_CLIENT_SECRET", client_secret),
            ("NOTION_REDIRECT_URI", redirect_uri),
        )
        if not value
    ]
    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"Missing Notion OAuth environment variables: {', '.join(missing)}",
        )
    return str(client_id), str(client_secret), str(redirect_uri)


def _encode_state(
    session_id: str,
    notion_page_id: Optional[str],
    user_id: Optional[str],
    frontend_url: Optional[str],
) -> str:
    payload = {
        "session_id":     session_id,
        "notion_page_id": notion_page_id,
        "user_id":        user_id,
        "frontend_url":   frontend_url,
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
    user_id: Optional[str] = None


def _auth_params(
    session_id: str = Query(...),
    notion_page_id: Optional[str] = Query(default=None),
    user_id: Optional[str] = Query(default=None),
    frontend_url: Optional[str] = Query(default=None),
) -> Dict[str, Optional[str]]:
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    return {
        "session_id": session_id,
        "notion_page_id": notion_page_id,
        "user_id": user_id,
        "frontend_url": frontend_url,
    }


def _notion_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }


def _extract_page_title(page: Dict[str, object]) -> str:
    properties = page.get("properties", {})
    if not isinstance(properties, dict):
        return ""
    for value in properties.values():
        if not isinstance(value, dict):
            continue
        if value.get("type") != "title":
            continue
        title_items = value.get("title", [])
        if not isinstance(title_items, list):
            continue
        return "".join(
            item.get("plain_text", "") for item in title_items if isinstance(item, dict)
        )
    return ""


def _find_or_create_root_page(token: str) -> str:
    """
    Strategy:
    1. Search if 'NotionClip Notes' already exists — reuse it if found.
    2. Try creating a workspace-level page.
    3. If both fail, return empty string — push will fail gracefully.
    """
    headers = _notion_headers(token)

    search_resp = requests.post(
        "https://api.notion.com/v1/search",
        headers=headers,
        json={"query": "NotionClip Notes", "filter": {"property": "object", "value": "page"}},
        timeout=10,
    )
    if search_resp.ok:
        results = search_resp.json().get("results", [])
        for result in results:
            if not isinstance(result, dict):
                continue
            title_text = _extract_page_title(result)
            if title_text.strip() == "NotionClip Notes":
                found_id = result.get("id", "")
                if isinstance(found_id, str) and found_id:
                    logger.info("Found existing root page: %s", found_id)
                    return found_id
    else:
        logger.warning(
            "Notion root search failed status=%s body=%s",
            search_resp.status_code,
            search_resp.text[:300],
        )

    create_resp = requests.post(
        "https://api.notion.com/v1/pages",
        headers=headers,
        json={
            "parent": {"type": "workspace", "workspace": True},
            "icon": {"type": "emoji", "emoji": "🧠"},
            "properties": {
                "title": {
                    "title": [{"type": "text", "text": {"content": "NotionClip Notes"}}]
                }
            },
        },
        timeout=10,
    )
    if create_resp.ok:
        page_id = create_resp.json().get("id", "")
        if isinstance(page_id, str) and page_id:
            logger.info("Created root page: %s", page_id)
            return page_id
    logger.warning(
        "Failed to create root page status=%s body=%s",
        create_resp.status_code,
        create_resp.text[:400],
    )

    # Fallback: pick any accessible page returned by search.
    fallback_resp = requests.post(
        "https://api.notion.com/v1/search",
        headers=headers,
        json={"filter": {"property": "object", "value": "page"}},
        timeout=10,
    )
    if fallback_resp.ok:
        results = fallback_resp.json().get("results", [])
        for result in results:
            if not isinstance(result, dict):
                continue
            page_id = result.get("id", "")
            if isinstance(page_id, str) and page_id:
                logger.info("Using fallback accessible page as root: %s", page_id)
                return page_id

    logger.error("Unable to resolve root page from Notion OAuth token")

    return ""


def _create_child_page(token: str, parent_id: str, title: str, emoji: str) -> str:
    """Create a child page under parent_id. Returns page ID or empty string."""
    if not parent_id:
        logger.error("Skipping child page '%s' creation because parent_id is missing", title)
        return ""

    search_resp = requests.post(
        "https://api.notion.com/v1/search",
        headers=_notion_headers(token),
        json={"query": title, "filter": {"property": "object", "value": "page"}},
        timeout=10,
    )
    if search_resp.ok:
        results = search_resp.json().get("results", [])
        for result in results:
            if not isinstance(result, dict):
                continue
            title_text = _extract_page_title(result)
            parent = result.get("parent", {})
            parent_page_id = parent.get("page_id") if isinstance(parent, dict) else None
            if title_text.strip() == title and parent_page_id == parent_id:
                page_id = result.get("id", "")
                if isinstance(page_id, str) and page_id:
                    logger.info("Found existing child page '%s': %s", title, page_id)
                    return page_id
    else:
        logger.warning(
            "Child search failed for '%s' status=%s body=%s",
            title,
            search_resp.status_code,
            search_resp.text[:300],
        )

    resp = requests.post(
        "https://api.notion.com/v1/pages",
        headers=_notion_headers(token),
        json={
            "parent": {"type": "page_id", "page_id": parent_id},
            "icon": {"type": "emoji", "emoji": emoji},
            "properties": {
                "title": {"title": [{"type": "text", "text": {"content": title}}]}
            },
        },
        timeout=10,
    )
    if resp.ok:
        page_id = resp.json().get("id", "")
        if isinstance(page_id, str) and page_id:
            logger.info("Created child page '%s': %s", title, page_id)
            return page_id

    logger.error(
        "Failed to create child page '%s' status=%s body=%s",
        title,
        resp.status_code,
        resp.text[:300],
    )
    return ""


@router.get("", response_model=None)
def start_auth(
    request: Request,
    params: Dict[str, Optional[str]] = Depends(_auth_params),
) -> RedirectResponse:
    client_id, _, redirect_uri = _oauth_config(request)
    state = _encode_state(
        params["session_id"],
        params["notion_page_id"],
        params.get("user_id"),
        params.get("frontend_url"),
    )
    auth_query = urlencode(
        {
            "client_id": client_id,
            "response_type": "code",
            "owner": "user",
            "redirect_uri": redirect_uri,
            "state": state,
        }
    )
    auth_url = f"{NOTION_OAUTH_URL}?{auth_query}"
    return RedirectResponse(url=auth_url)


@router.get("/callback", response_model=None)
def oauth_callback(
    request: Request,
    code:  str = Query(...),
    state: str = Query(...),
) -> RedirectResponse:
    client_id, client_secret, redirect_uri = _oauth_config(request)
    state_payload = _decode_state(state)
    session_id    = state_payload["session_id"]
    frontend_url = state_payload.get("frontend_url")

    # Exchange code for token
    auth_header = base64.b64encode(
        f"{client_id}:{client_secret}".encode()
    ).decode()

    response = requests.post(
        NOTION_TOKEN_URL,
        json={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        },
        headers={"Content-Type": "application/json", "Authorization": f"Basic {auth_header}"},
        timeout=15,
    )

    logger.info("Token exchange status=%s", response.status_code)
    if response.status_code != 200:
        logger.error("Token exchange failed: %s", response.text[:500])
        return _frontend_redirect(frontend_url, connected=False, error="token_exchange_failed")

    data         = response.json()
    access_token = data.get("access_token", "")
    if not access_token:
        logger.error("Notion response missing access token")
        return _frontend_redirect(frontend_url, connected=False, error="missing_access_token")

    logger.info(
        "Notion OAuth success workspace=%s owner=%s",
        data.get("workspace_name"),
        data.get("owner", {}).get("type") if isinstance(data.get("owner"), dict) else "unknown",
    )

    # Create page structure
    root_page_id  = _find_or_create_root_page(access_token)
    if not root_page_id:
        return _frontend_redirect(frontend_url, connected=False, error="root_page_unavailable")

    study_page_id = _create_child_page(access_token, root_page_id, "Study Notes", "📚")
    work_page_id  = _create_child_page(access_token, root_page_id, "Work Briefs", "💼")
    quick_page_id = _create_child_page(access_token, root_page_id, "Quick Saves", "⚡")

    # Fallback to root page if one or more child pages cannot be initialized.
    if not study_page_id:
        study_page_id = root_page_id
    if not work_page_id:
        work_page_id = root_page_id
    if not quick_page_id:
        quick_page_id = root_page_id

    logger.info(
        "Saving session=%s root=%s study=%s work=%s quick=%s",
        session_id,
        root_page_id,
        study_page_id,
        work_page_id,
        quick_page_id,
    )

    save_session(
        session_id,
        access_token,
        root_page_id,
        study_page_id,
        work_page_id,
        quick_page_id,
        user_id=state_payload.get("user_id"),
    )

    return _frontend_redirect(frontend_url, connected=True)


@router.get("/status/{session_id}", response_model=AuthStatusResponse)
def auth_status(session_id: str) -> AuthStatusResponse:
    session   = get_session(session_id)
    has_token = bool(session and session.get("notion_token"))
    return AuthStatusResponse(
        session_id=session_id,
        has_token=has_token,
        notion_page_id=session.get("notion_page_id") if session else None,
        user_id=session.get("user_id") if session else None,
    )
