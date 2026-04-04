import os
from datetime import datetime
from typing import Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import requests

from models import ActionItemList, MeetingSummary, StudyNotes, VideoInsights, WorkBrief

NOTION_VERSION = "2022-06-28"
NOTION_BLOCK_LIMIT = 90

GENERIC_TITLES = {
    "study notes",
    "work brief",
    "quick notes",
    "video summary",
    "notes",
    "summary",
    "study timestamp notes",
    "timestamp notes",
}


def get_headers(token: Optional[str] = None) -> dict:
    notion_token = token or os.getenv("NOTION_TOKEN", "")
    return {
        "Authorization": f"Bearer {notion_token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def clean_page_id(page_id: str) -> str:
    return (page_id or "").replace("-", "").strip()


def get_notion_page_id(notion_page_id: Optional[str]) -> str:
    return notion_page_id or os.getenv("NOTION_PAGE_ID", "")


def _normalize_title_text(raw: str) -> str:
    text = " ".join((raw or "").replace("\n", " ").split()).strip(" -:|")
    return text[:120]


def _is_generic_title(title: str) -> bool:
    normalized = _normalize_title_text(title).lower()
    return not normalized or normalized in GENERIC_TITLES


def _headline_from_summary(summary: str) -> str:
    cleaned = _normalize_title_text(summary)
    if not cleaned:
        return ""
    return cleaned[:90]


def _resolve_video_related_title(mode_label: str, title: str, summary_hint: str) -> str:
    clean_title = _normalize_title_text(title)
    if clean_title and not _is_generic_title(clean_title):
        return clean_title
    fallback = _headline_from_summary(summary_hint)
    if fallback:
        return fallback
    return f"{mode_label} Video Notes"


def _extract_database_title(db: dict) -> str:
    title_items = db.get("title", [])
    if not isinstance(title_items, list):
        return ""
    return "".join(item.get("plain_text", "") for item in title_items if isinstance(item, dict))


def _notion_error_message(response: requests.Response) -> str:
    try:
        payload = response.json()
        if isinstance(payload, dict):
            return str(payload.get("message") or payload.get("error") or "")
    except Exception:
        pass
    return (response.text or "").strip()


def _is_archived_object(payload: dict) -> bool:
    return bool(payload.get("archived") or payload.get("in_trash"))


def _is_archived_ancestor_error(message: str) -> bool:
    return "archived ancestor" in (message or "").lower()


def _retrieve_active_database(database_id: str, token: Optional[str]) -> Optional[dict]:
    response = requests.get(
        f"https://api.notion.com/v1/databases/{clean_page_id(database_id)}",
        headers=get_headers(token),
        timeout=10,
    )
    if response.status_code != 200:
        return None
    payload = response.json()
    if not isinstance(payload, dict) or _is_archived_object(payload):
        return None
    return payload


def _unarchive_page(page_id: str, token: Optional[str]) -> bool:
    response = requests.patch(
        f"https://api.notion.com/v1/pages/{clean_page_id(page_id)}",
        headers=get_headers(token),
        json={"archived": False},
        timeout=10,
    )
    return response.status_code in (200, 201)


def _fetch_youtube_metadata(url: str) -> dict:
    if not url or "youtu" not in url.lower():
        return {}
    try:
        response = requests.get(
            "https://www.youtube.com/oembed",
            params={"url": url, "format": "json"},
            timeout=8,
        )
        if response.status_code != 200:
            return {}
        payload = response.json()
        return {
            "title": _normalize_title_text(str(payload.get("title") or "")),
            "creator": _normalize_title_text(str(payload.get("author_name") or "")),
        }
    except Exception:
        return {}


def _database_properties_template() -> dict:
    return {
        "Title": {"title": {}},
        "Mode": {
            "select": {
                "options": [
                    {"name": "Study", "color": "purple"},
                    {"name": "Work", "color": "blue"},
                    {"name": "Quick", "color": "yellow"},
                ]
            }
        },
        "Source": {
            "select": {
                "options": [
                    {"name": "YouTube", "color": "red"},
                    {"name": "PDF", "color": "gray"},
                    {"name": "Article", "color": "orange"},
                ]
            }
        },
        "Link": {"url": {}},
        "One-line Summary": {"rich_text": {}},
        "AI Notes": {"rich_text": {}},
        "Your Notes": {"rich_text": {}},
        "Smart Watch Verdict": {
            "select": {
                "options": [
                    {"name": "Watch", "color": "green"},
                    {"name": "Skip", "color": "red"},
                    {"name": "Selective", "color": "yellow"},
                ]
            }
        },
        "Status": {
            "select": {
                "options": [
                    {"name": "To Learn", "color": "gray"},
                    {"name": "In Progress", "color": "blue"},
                    {"name": "Done", "color": "green"},
                ]
            }
        },
        "Tags": {"multi_select": {}},
        "Date Added": {"date": {}},
        "AutoFinished": {"checkbox": {}},
    }


def _ensure_database_properties(database_id: str, token: Optional[str]) -> None:
    response = requests.get(
        f"https://api.notion.com/v1/databases/{clean_page_id(database_id)}",
        headers=get_headers(token),
        timeout=10,
    )
    if response.status_code != 200:
        return
    existing = response.json().get("properties", {})
    desired = _database_properties_template()
    missing: dict = {}
    for key, value in desired.items():
        if key not in existing:
            missing[key] = value
    if not missing:
        return
    requests.patch(
        f"https://api.notion.com/v1/databases/{clean_page_id(database_id)}",
        headers=get_headers(token),
        json={"properties": missing},
        timeout=10,
    )


def _find_fallback_parent_page_id(token: str) -> Optional[str]:
    """Find an active page where NotionClip DB can be created if the saved parent was deleted."""
    headers = get_headers(token)
    try:
        search_resp = requests.post(
            "https://api.notion.com/v1/search",
            headers=headers,
            json={"filter": {"property": "object", "value": "page"}},
            timeout=10,
        )
        if not search_resp.ok:
            return None
        for result in search_resp.json().get("results", []):
            if not isinstance(result, dict):
                continue
            if _is_archived_object(result):
                continue
            page_id = result.get("id")
            if isinstance(page_id, str) and page_id:
                return page_id
    except Exception:
        return None
    return None


def _find_or_create_master_database(*, token: str, parent_page_id: str) -> str:
    headers = get_headers(token)
    search_resp = requests.post(
        "https://api.notion.com/v1/search",
        headers=headers,
        json={"query": "NotionClip", "filter": {"property": "object", "value": "database"}},
        timeout=10,
    )
    if search_resp.ok:
        results = search_resp.json().get("results", [])
        for result in results:
            if not isinstance(result, dict):
                continue
            title_text = _extract_database_title(result)
            if title_text.strip() == "NotionClip":
                found_id = result.get("id", "")
                if isinstance(found_id, str) and found_id:
                    if _is_archived_object(result):
                        continue
                    db_payload = _retrieve_active_database(found_id, token)
                    if not db_payload:
                        continue
                    _ensure_database_properties(found_id, token)
                    return found_id

    payload = {
        "parent": {"type": "page_id", "page_id": clean_page_id(parent_page_id)},
        "icon": {"type": "emoji", "emoji": "🧠"},
        "title": [{"type": "text", "text": {"content": "NotionClip"}}],
        "properties": _database_properties_template(),
    }
    create_resp = requests.post(
        "https://api.notion.com/v1/databases",
        headers=headers,
        json=payload,
        timeout=10,
    )
    if not create_resp.ok:
        message = _notion_error_message(create_resp)
        if _is_archived_ancestor_error(message) and _unarchive_page(parent_page_id, token):
            create_resp = requests.post(
                "https://api.notion.com/v1/databases",
                headers=headers,
                json=payload,
                timeout=10,
            )
            message = _notion_error_message(create_resp)

        # If the configured parent page was deleted/permanently removed,
        # create the master DB under any active page the integration can access.
        if not create_resp.ok:
            lower_msg = (message or "").lower()
            missing_parent = (
                "archived ancestor" in lower_msg
                or "could not find page" in lower_msg
                or "object_not_found" in lower_msg
                or "insufficient permissions" in lower_msg
            )
            if missing_parent:
                fallback_parent = _find_fallback_parent_page_id(token)
                if fallback_parent:
                    fallback_payload = {
                        **payload,
                        "parent": {"type": "page_id", "page_id": clean_page_id(fallback_parent)},
                    }
                    create_resp = requests.post(
                        "https://api.notion.com/v1/databases",
                        headers=headers,
                        json=fallback_payload,
                        timeout=10,
                    )
                    message = _notion_error_message(create_resp)

        if not create_resp.ok:
            raise Exception(f"Database creation failed: {message[:300]}")

    db_id = create_resp.json().get("id", "")
    if isinstance(db_id, str) and db_id:
        return db_id
    raise Exception("Database creation failed: Notion API did not return a database id")


def _create_database_entry(
    *,
    database_id: str,
    title: str,
    mode: str,
    source: str,
    link: str,
    summary: str,
    notion_token: Optional[str] = None,
    tags: Optional[list[str]] = None,
    smart_watch_verdict: Optional[str] = None,
    ai_notes: Optional[str] = None,
    your_notes: Optional[str] = None,
) -> str:
    now_iso = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    properties: dict = {
        "Title": {"title": [{"text": {"content": title[:200]}}]},
        "Mode": {"select": {"name": mode}},
        "Source": {"select": {"name": source}},
        "Link": {"url": link or ""},
        "One-line Summary": {"rich_text": [{"text": {"content": summary[:2000]}}]} if summary else {"rich_text": []},
        "Status": {"select": {"name": "To Learn"}},
        "Date Added": {"date": {"start": now_iso}},
        "AutoFinished": {"checkbox": False},
    }
    if ai_notes is not None:
        properties["AI Notes"] = {"rich_text": [{"text": {"content": ai_notes[:2000]}}]} if ai_notes else {"rich_text": []}
    if your_notes is not None:
        properties["Your Notes"] = {"rich_text": [{"text": {"content": your_notes[:2000]}}]} if your_notes else {"rich_text": []}
    if tags:
        properties["Tags"] = {"multi_select": [{"name": tag[:60]} for tag in tags]}
    if smart_watch_verdict:
        properties["Smart Watch Verdict"] = {"select": {"name": smart_watch_verdict}}

    payload = {
        "parent": {"database_id": clean_page_id(database_id)},
        "properties": properties,
    }
    response = requests.post(
        "https://api.notion.com/v1/pages",
        json=payload,
        headers=get_headers(notion_token),
    )
    if response.status_code not in (200, 201):
        raise Exception(f"Page creation failed: {response.json().get('message')}")
    return response.json().get("id")


def _update_database_entry(page_id: str, properties: dict, notion_token: Optional[str] = None) -> None:
    requests.patch(
        f"https://api.notion.com/v1/pages/{clean_page_id(page_id)}",
        json={"properties": properties},
        headers=get_headers(notion_token),
        timeout=10,
    )


def _create_child_page(
    *,
    parent_page_id: str,
    title: str,
    emoji: str,
    notion_token: Optional[str] = None,
    children: Optional[list] = None,
) -> str:
    payload = {
        "parent": {"type": "page_id", "page_id": clean_page_id(parent_page_id)},
        "icon": {"type": "emoji", "emoji": emoji},
        "properties": {"title": {"title": [{"text": {"content": title[:100]}}]}},
        "children": (children or [])[:NOTION_BLOCK_LIMIT],
    }
    response = requests.post(
        "https://api.notion.com/v1/pages",
        json=payload,
        headers=get_headers(notion_token),
    )
    if response.status_code not in (200, 201):
        raise Exception(f"Page creation failed: {response.json().get('message')}")

    page_id = response.json().get("id")
    overflow = (children or [])[NOTION_BLOCK_LIMIT:]
    if overflow:
        _append_blocks(page_id, overflow, notion_token)
    return page_id


def _list_child_pages(page_id: str, notion_token: Optional[str] = None) -> list[dict]:
    children: list[dict] = []
    next_cursor: Optional[str] = None
    page_id = clean_page_id(page_id)
    while True:
        params = {"page_size": 100}
        if next_cursor:
            params["start_cursor"] = next_cursor
        resp = requests.get(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            headers=get_headers(notion_token),
            params=params,
            timeout=10,
        )
        if resp.status_code != 200:
            break
        payload = resp.json()
        children.extend(payload.get("results", []))
        if not payload.get("has_more"):
            break
        next_cursor = payload.get("next_cursor")
    return children


def _find_child_page_by_title(page_id: str, title_prefix: str, notion_token: Optional[str] = None) -> Optional[str]:
    for block in _list_child_pages(page_id, notion_token):
        if block.get("type") != "child_page":
            continue
        child_title = (block.get("child_page") or {}).get("title", "")
        if child_title.startswith(title_prefix):
            return block.get("id")
    return None


def _build_timestamp_link(url: str, seconds: int) -> str:
    try:
        parsed = urlparse(url)
        params = dict(parse_qsl(parsed.query, keep_blank_values=True))
        params["t"] = str(max(0, int(seconds)))
        return urlunparse(parsed._replace(query=urlencode(params)))
    except Exception:
        sep = "&" if "?" in url else "?"
        return f"{url}{sep}t={max(0, int(seconds))}"


def make_bullet(text: str) -> dict:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]},
    }


def make_numbered(text: str) -> dict:
    return {
        "object": "block",
        "type": "numbered_list_item",
        "numbered_list_item": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]},
    }


def make_heading(text: str, level: int = 2) -> dict:
    h_type = f"heading_{level}"
    return {
        "object": "block",
        "type": h_type,
        h_type: {"rich_text": [{"type": "text", "text": {"content": text}}]},
    }


def make_divider() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}


def make_callout(text: str, emoji: str = "💡", color: str = "blue_background") -> dict:
    return {
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}],
            "icon": {"emoji": emoji},
            "color": color,
        },
    }


def make_code_block(text: str) -> dict:
    return {
        "object": "block",
        "type": "code",
        "code": {
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}],
            "language": "plain text",
        },
    }


def make_toggle(question: str, answer_placeholder: str = "[Write your answer here before expanding]") -> dict:
    return {
        "object": "block",
        "type": "toggle",
        "toggle": {
            "rich_text": [{"type": "text", "text": {"content": question[:2000]}}],
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": answer_placeholder},
                                "annotations": {"italic": True, "color": "gray"},
                            }
                        ]
                    },
                }
            ],
        },
    }


def make_todo(text: str, checked: bool = False) -> dict:
    return {
        "object": "block",
        "type": "to_do",
        "to_do": {
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}],
            "checked": checked,
        },
    }


def make_quote(text: str) -> dict:
    return {
        "object": "block",
        "type": "quote",
        "quote": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]},
    }


def make_bookmark(url: str) -> dict:
    return {"object": "block", "type": "bookmark", "bookmark": {"url": url}}


def make_paragraph(text: str, italic: bool = False, color: str = "default") -> dict:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": text[:2000]},
                    "annotations": {"italic": italic, "color": color},
                }
            ]
        },
    }


def make_rich_paragraph(chunks: list[dict]) -> dict:
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": chunks[:100]}}


def _append_blocks(page_id: str, blocks: list, notion_token: Optional[str] = None):
    page_id = clean_page_id(page_id)
    for i in range(0, len(blocks), NOTION_BLOCK_LIMIT):
        batch = blocks[i : i + NOTION_BLOCK_LIMIT]
        resp = requests.patch(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            json={"children": batch},
            headers=get_headers(notion_token),
        )
        if resp.status_code not in (200, 201):
            raise Exception(f"Failed to append blocks: {resp.json().get('message')}")


def _create_page_with_overflow(parent_page_id: str, payload: dict, extra_blocks: list, notion_token: Optional[str] = None) -> str:
    response = requests.post(
        "https://api.notion.com/v1/pages",
        json=payload,
        headers=get_headers(notion_token),
    )
    if response.status_code not in (200, 201):
        raise Exception(f"Page creation failed: {response.json().get('message')}")
    page_id = response.json().get("id")
    if extra_blocks:
        _append_blocks(page_id, extra_blocks, notion_token)
    return page_id


def _create_video_workspace(
    *,
    root_parent_page_id: str,
    video_url: str,
    title_hint: str,
    mode: str,
    summary_hint: str,
    source_type: str,
    notion_token: Optional[str] = None,
) -> dict:
    metadata = _fetch_youtube_metadata(video_url)
    resolved_title = metadata.get("title") or _resolve_video_related_title("Video", title_hint, summary_hint)
    resolved_creator = metadata.get("creator") or "Unknown Creator"

    db_id = _find_or_create_master_database(token=notion_token, parent_page_id=root_parent_page_id)
    db_page_id = _create_database_entry(
        database_id=db_id,
        title=resolved_title,
        mode=mode.title(),
        source=source_type,
        link=video_url,
        summary=summary_hint or "",
        notion_token=notion_token,
        ai_notes=summary_hint or "",
    )

    # DB row page: only a bookmark so the row itself stays clean
    db_row_header = []
    if video_url:
        db_row_header.append(make_bookmark(video_url))
    if db_row_header:
        _append_blocks(db_page_id, db_row_header, notion_token)

    # AI Notes child page: pre-seeded with video header + summary
    ai_notes_initial: list = [
        make_callout(
            f"Video: {resolved_title}\nCreator: {resolved_creator}",
            "🎬",
            "gray_background",
        ),
    ]
    if summary_hint:
        ai_notes_initial.extend([
            make_divider(),
            make_heading("AI Summary", level=3),
            make_callout(summary_hint[:2000], "🧠", "yellow_background"),
            make_divider(),
        ])

    ai_notes_page_id = _create_child_page(
        parent_page_id=db_page_id,
        title=f"AI Notes - {resolved_title}"[:100],
        emoji="🧠",
        notion_token=notion_token,
        children=ai_notes_initial,
    )

    # Your Notes child page: clean personal workspace
    take_notes_page_id = _create_child_page(
        parent_page_id=db_page_id,
        title=f"Your Notes - {resolved_title}"[:100],
        emoji="✍️",
        notion_token=notion_token,
        children=[
            make_heading("Your Notes", level=2),
            make_callout(
                "Personal thinking space. AI Notes has the structured summary - add your own reactions, questions, and connections here.",
                "✍️",
                "gray_background",
            ),
            make_divider(),
            make_heading("Thoughts while watching", level=3),
            make_paragraph(""),
            make_divider(),
            make_heading("Questions to follow up on", level=3),
            make_todo(""),
        ],
    )

    return {
        "workspace_page_id": db_page_id,
        "ai_notes_page_id": ai_notes_page_id,
        "take_notes_page_id": take_notes_page_id,
        "video_title": resolved_title,
        "creator": resolved_creator,
    }


def push_timestamp_notes(
    *,
    mode: str,
    source_url: str,
    timestamp_notes: list[dict],
    ai_summary: Optional[str] = None,
    video_title: Optional[str] = None,
    creator_name: Optional[str] = None,
    notion_token: Optional[str] = None,
    notion_page_id: Optional[str] = None,
) -> str:
    workspace_page_id: Optional[str] = None
    if notion_page_id:
        workspace_page_id = clean_page_id(notion_page_id)

    if workspace_page_id:
        metadata = _fetch_youtube_metadata(source_url)
        resolved_title = video_title or metadata.get("title") or "YouTube Video"
        resolved_creator = creator_name or metadata.get("creator") or "Unknown Creator"
        workspace = {
            "workspace_page_id": workspace_page_id,
            "video_title": _normalize_title_text(resolved_title),
            "creator": _normalize_title_text(resolved_creator),
        }
    else:
        parent_page_id = clean_page_id(get_notion_page_id(notion_page_id))
        workspace = _create_video_workspace(
            root_parent_page_id=parent_page_id,
            video_url=source_url,
            title_hint=video_title or "YouTube Video",
            mode=mode,
            summary_hint=ai_summary or "",
            source_type="YouTube" if "youtu" in (source_url or "").lower() else "Article",
            notion_token=notion_token,
        )

    take_notes_page_id = _find_child_page_by_title(
        workspace["workspace_page_id"],
        "Your Notes",
        notion_token,
    )
    if not take_notes_page_id:
        take_notes_page_id = _create_child_page(
            parent_page_id=workspace["workspace_page_id"],
            title=f"Your Notes - {workspace['video_title']}"[:100],
            emoji="✍️",
            notion_token=notion_token,
            children=[make_heading("Timestamp Notes", level=3)],
        )

    note_blocks: list[dict] = [
        make_divider(),
        make_heading("Detected Timestamp Notes", level=3),
        make_paragraph("Pushed from NotionClip. Click timestamp chips to jump to exact moments."),
    ]

    if timestamp_notes:
        for item in timestamp_notes[:200]:
            label = str(item.get("label") or item.get("timestamp") or "00:00")[:20]
            note = str(item.get("note") or "").strip()[:1800]
            title = str(item.get("title") or "").strip()[:180]
            if not title:
                title = f"Moment at {label}"
            seconds_raw = item.get("seconds")
            try:
                seconds = int(seconds_raw) if seconds_raw is not None else None
            except Exception:
                seconds = None

            rich: list[dict] = []
            if source_url and seconds is not None:
                rich.append(
                    {
                        "type": "text",
                        "text": {"content": f"[{label}]", "link": {"url": _build_timestamp_link(source_url, seconds)}},
                        "annotations": {"bold": True},
                    }
                )
            else:
                rich.append({"type": "text", "text": {"content": f"[{label}]"}, "annotations": {"bold": True}})

            if title:
                rich.append({"type": "text", "text": {"content": f" {title}"}, "annotations": {"bold": True}})
            if note:
                rich.append({"type": "text", "text": {"content": f"\n{note}"}})
            note_blocks.append(make_rich_paragraph(rich))
    else:
        note_blocks.append(make_paragraph("No timestamp notes were detected yet."))

    _append_blocks(take_notes_page_id, note_blocks, notion_token)

    your_notes_value = f"{len(timestamp_notes)} timestamp notes added" if timestamp_notes else "Timestamp notes added"
    _update_database_entry(
        workspace["workspace_page_id"],
        {"Your Notes": {"rich_text": [{"text": {"content": your_notes_value[:2000]}}]}},
        notion_token,
    )

    return workspace["workspace_page_id"]


def create_tasks_database(title: str, parent_page_id: str, notion_token: Optional[str] = None) -> str | None:
    parent_page_id = clean_page_id(parent_page_id)
    payload = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "icon": {"type": "emoji", "emoji": "✅"},
        "title": [{"type": "text", "text": {"content": f"Tasks: {title}"}}],
        "properties": {
            "Task": {"title": {}},
            "Assignee": {"rich_text": {}},
            "Due Date": {"date": {}},
            "Priority": {
                "select": {
                    "options": [
                        {"name": "High", "color": "red"},
                        {"name": "Medium", "color": "yellow"},
                        {"name": "Low", "color": "green"},
                    ]
                }
            },
            "Status": {
                "select": {
                    "options": [
                        {"name": "Not Started", "color": "gray"},
                        {"name": "In Progress", "color": "blue"},
                        {"name": "Done", "color": "green"},
                    ]
                }
            },
        },
    }
    response = requests.post(
        "https://api.notion.com/v1/databases",
        json=payload,
        headers=get_headers(notion_token),
    )
    if response.status_code in (200, 201):
        return response.json().get("id")
    raise Exception(f"Database creation failed: {response.json().get('message')}")


def push_tasks_to_database(task_list: ActionItemList, database_id: str, notion_token: Optional[str] = None):
    for item in task_list.items:
        payload = {
            "parent": {"database_id": database_id},
            "properties": {
                "Task": {"title": [{"text": {"content": item.task}}]},
                "Assignee": {"rich_text": [{"text": {"content": item.assignee}}]},
                "Priority": {"select": {"name": item.priority}},
                "Status": {"select": {"name": "Not Started"}},
            },
        }
        if item.due_date and item.due_date != "TBD":
            payload["properties"]["Due Date"] = {"date": {"start": item.due_date}}
        requests.post(
            "https://api.notion.com/v1/pages",
            json=payload,
            headers=get_headers(notion_token),
        )


def push_study_notes(
    notes: StudyNotes,
    video_url: str,
    notion_token: Optional[str] = None,
    notion_page_id: Optional[str] = None,
) -> str:
    parent_page_id = clean_page_id(get_notion_page_id(notion_page_id))
    workspace = _create_video_workspace(
        root_parent_page_id=parent_page_id,
        video_url=video_url,
        title_hint=notes.title or notes.core_concept or "YouTube Video",
        mode="study",
        summary_hint=notes.core_concept or "",
        source_type="YouTube" if "youtu" in (video_url or "").lower() else "Article",
        notion_token=notion_token,
    )

    all_blocks = [
        make_callout(
            f"Video: {workspace['video_title']}\nCreator: {workspace['creator']}",
            "🎬",
            "gray_background",
        )
    ]

    if notes.core_concept:
        all_blocks.append(make_heading("🧠 Video Summary"))
        all_blocks.append(make_callout(notes.core_concept, "📐", "yellow_background"))

    if notes.formula_sheet:
        all_blocks.append(make_heading("📋 Formula Sheet"))
        for formula in notes.formula_sheet:
            all_blocks.append(make_code_block(formula))

    if notes.key_facts:
        all_blocks.append(make_heading("⚡ Key Facts"))
        for fact in notes.key_facts:
            all_blocks.append(make_numbered(fact))

    if notes.common_mistakes:
        all_blocks.append(make_heading("⚠️ Common Mistakes"))
        for mistake in notes.common_mistakes:
            all_blocks.append(make_bullet(mistake))

    if notes.self_test:
        all_blocks.append(make_heading("🧪 Self-Test"))
        for question in notes.self_test:
            all_blocks.append(make_toggle(question, "Write your answer here..."))

    if notes.prerequisites:
        all_blocks.append(make_heading("📚 Prerequisites"))
        for prereq in notes.prerequisites:
            all_blocks.append(make_bullet(prereq))

    if notes.further_reading:
        all_blocks.append(make_heading("📖 Further Reading"))
        for resource in notes.further_reading:
            all_blocks.append(make_bullet(resource))

    _append_blocks(workspace["ai_notes_page_id"], all_blocks, notion_token)
    return workspace["workspace_page_id"]


def push_work_brief(
    brief: WorkBrief,
    video_url: str,
    notion_token: Optional[str] = None,
    notion_page_id: Optional[str] = None,
) -> str:
    parent_page_id = clean_page_id(get_notion_page_id(notion_page_id))
    workspace = _create_video_workspace(
        root_parent_page_id=parent_page_id,
        video_url=video_url,
        title_hint=brief.title or brief.one_liner or "YouTube Video",
        mode="work",
        summary_hint=brief.one_liner or "",
        source_type="YouTube" if "youtu" in (video_url or "").lower() else "Article",
        notion_token=notion_token,
    )

    recommendation = (brief.recommendation or "").strip()
    is_watch = recommendation.lower().startswith("watch")
    verdict_emoji = "🟢" if is_watch else "🔴"
    verdict_color = "green_background" if is_watch else "red_background"

    all_blocks = [
        make_callout(
            f"Video: {workspace['video_title']}\nCreator: {workspace['creator']}",
            "🎬",
            "gray_background",
        ),
        make_callout(recommendation, verdict_emoji, verdict_color),
        make_heading("🧠 Video Summary"),
        make_quote(brief.one_liner),
    ]

    if brief.key_points:
        all_blocks.append(make_heading("💡 Key Points"))
        for point in brief.key_points:
            all_blocks.append(make_bullet(point))

    if brief.tools_mentioned:
        all_blocks.append(make_heading("🛠️ Tools Mentioned"))
        for tool in brief.tools_mentioned:
            all_blocks.append(make_paragraph(tool))

    if brief.decisions_to_make:
        all_blocks.append(make_heading("✅ Decisions to Make"))
        for decision in brief.decisions_to_make:
            all_blocks.append(make_todo(decision))

    if brief.next_actions:
        all_blocks.append(make_heading("🚀 Next Actions"))
        for action in brief.next_actions:
            all_blocks.append(make_todo(action))

    _append_blocks(workspace["ai_notes_page_id"], all_blocks, notion_token)
    return workspace["workspace_page_id"]


def push_youtube(
    insights: VideoInsights,
    video_url: str,
    task_list: ActionItemList = None,
    sections: dict = None,
    notion_token: Optional[str] = None,
    notion_page_id: Optional[str] = None,
):
    if sections is None:
        sections = {"summary": True, "key_takeaways": True, "topics": True, "action_items": True}

    parent_page_id = clean_page_id(get_notion_page_id(notion_page_id))
    workspace = _create_video_workspace(
        root_parent_page_id=parent_page_id,
        video_url=video_url,
        title_hint=insights.title or insights.summary or "YouTube Video",
        mode="quick",
        summary_hint=insights.summary or "",
        source_type="YouTube" if "youtu" in (video_url or "").lower() else "Article",
        notion_token=notion_token,
    )

    page_blocks = [
        make_callout(
            f"Video: {workspace['video_title']}\nCreator: {workspace['creator']}",
            "🎬",
            "gray_background",
        ),
        make_divider(),
    ]

    if sections.get("summary", True) and insights.summary:
        page_blocks.append(make_heading("🧠 Video Summary"))
        page_blocks.append(make_callout(insights.summary, "🎬", "yellow_background"))
        page_blocks.append(make_divider())

    if sections.get("key_takeaways", True) and insights.key_takeaways:
        page_blocks.append(make_heading("💡 Key Takeaways"))
        for t in insights.key_takeaways:
            page_blocks.append(make_bullet(t))
        page_blocks.append(make_divider())

    if sections.get("topics", True) and insights.topics_covered:
        page_blocks.append(make_heading("📚 Topics Covered"))
        for t in insights.topics_covered:
            page_blocks.append(make_bullet(t))
        page_blocks.append(make_divider())

    if sections.get("action_items", True) and insights.action_items:
        page_blocks.append(make_heading("✅ Action Items"))
        for a in insights.action_items:
            page_blocks.append(make_bullet(a))

    _append_blocks(workspace["ai_notes_page_id"], page_blocks, notion_token)
    if task_list:
        db_id = create_tasks_database(insights.title, workspace["ai_notes_page_id"], notion_token)
        if db_id:
            push_tasks_to_database(task_list, db_id, notion_token)
    return workspace["workspace_page_id"]


def push_meeting(
    task_list: ActionItemList,
    summary: MeetingSummary,
    notion_token: Optional[str] = None,
    notion_page_id: Optional[str] = None,
) -> str:
    parent_page_id = clean_page_id(get_notion_page_id(notion_page_id))

    blocks = [
        make_heading("Meeting Summary", level=2),
        make_callout(summary.summary, "🧠", "yellow_background"),
        make_heading("Key Decisions", level=3),
    ]
    for item in summary.key_decisions:
        blocks.append(make_bullet(item))
    blocks.append(make_heading("Next Steps", level=3))
    for item in summary.next_steps:
        blocks.append(make_bullet(item))

    payload = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "icon": {"type": "emoji", "emoji": "🎙️"},
        "properties": {"title": {"title": [{"text": {"content": f"Meeting: {summary.title[:60]}"}}]}},
        "children": blocks[:NOTION_BLOCK_LIMIT],
    }
    summary_page_id = _create_page_with_overflow(parent_page_id, payload, blocks[NOTION_BLOCK_LIMIT:], notion_token)
    if task_list:
        db_id = create_tasks_database(summary.title, summary_page_id, notion_token)
        if db_id:
            push_tasks_to_database(task_list, db_id, notion_token)
    return summary_page_id
