import os
import requests
import streamlit as st
from dotenv import load_dotenv
from models import ActionItemList, MeetingSummary, VideoInsights

load_dotenv()

NOTION_VERSION  = "2022-06-28"
PRIORITY_COLORS = {"High": "red", "Medium": "yellow", "Low": "green"}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_notion_token():
    """Read token from .env first, then Streamlit secrets."""
    token = os.getenv("NOTION_TOKEN")
    if token:
        return token
    try:
        return st.secrets.get("NOTION_TOKEN", "")
    except Exception:
        return None

def get_notion_page_id():
    """Read page ID from .env first, then Streamlit secrets."""
    page_id = os.getenv("NOTION_PAGE_ID")
    if page_id:
        return page_id
    try:
        return st.secrets.get("NOTION_PAGE_ID", "")
    except Exception:
        return None

def get_headers():
    token = get_notion_token()
    if not token:
        raise ValueError(
            "Notion token not found. Please add your token in Settings."
        )
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }

def clean_page_id(page_id: str) -> str:
    if not page_id:
        raise ValueError(
            "Notion Page ID not found. Please add your Page ID in Settings."
        )
    if "/" in page_id:
        page_id = page_id.split("/")[-1].split("?")[0]
    return page_id.replace("-", "")[-32:]

def make_bullet(text: str) -> dict:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}]
        }
    }

def make_heading(text: str) -> dict:
    return {
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": [{"type": "text", "text": {"content": text}}]
        }
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
            "color": color
        }
    }

def create_tasks_database(title: str, parent_page_id: str) -> str | None:
    parent_page_id = clean_page_id(parent_page_id)
    payload = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "icon": {"type": "emoji", "emoji": "✅"},
        "title": [{"type": "text", "text": {"content": f"Tasks: {title}"}}],
        "properties": {
            "Task":     {"title": {}},
            "Assignee": {"rich_text": {}},
            "Due Date": {"date": {}},
            "Priority": {
                "select": {
                    "options": [
                        {"name": "High",   "color": "red"},
                        {"name": "Medium", "color": "yellow"},
                        {"name": "Low",    "color": "green"},
                    ]
                }
            },
            "Status": {
                "select": {
                    "options": [
                        {"name": "Not Started", "color": "gray"},
                        {"name": "In Progress", "color": "blue"},
                        {"name": "Done",        "color": "green"},
                    ]
                }
            }
        }
    }
    response = requests.post(
        "https://api.notion.com/v1/databases",
        json=payload, headers=get_headers()
    )
    if response.status_code == 200:
        return response.json().get("id")
    else:
        raise Exception(f"Database creation failed: {response.json().get('message')}")

def push_tasks_to_database(task_list: ActionItemList, database_id: str):
    for item in task_list.items:
        priority = item.priority if item.priority in PRIORITY_COLORS else "Medium"
        payload = {
            "parent": {"database_id": database_id},
            "properties": {
                "Task":     {"title": [{"text": {"content": item.task}}]},
                "Assignee": {"rich_text": [{"text": {"content": item.assignee}}]},
                "Priority": {"select": {"name": priority}},
                "Status":   {"select": {"name": "Not Started"}},
            }
        }
        if item.due_date and item.due_date != "TBD":
            payload["properties"]["Due Date"] = {"date": {"start": item.due_date}}

        requests.post(
            "https://api.notion.com/v1/pages",
            json=payload, headers=get_headers()
        )


# ─── Meeting Mode ─────────────────────────────────────────────────────────────

def push_meeting(task_list: ActionItemList, summary: MeetingSummary):
    parent_page_id = clean_page_id(get_notion_page_id())

    page_blocks = [
        make_callout(summary.summary, "💡", "blue_background"),
        make_divider(),
        make_heading("✅ Key Decisions"),
        *[make_bullet(d) for d in summary.key_decisions],
        make_divider(),
        make_heading("🚀 Next Steps"),
        *[make_bullet(s) for s in summary.next_steps],
        make_divider(),
        make_heading("📌 Action Items ↓"),
    ]

    payload = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "icon": {"type": "emoji", "emoji": "📋"},
        "properties": {
            "title": {"title": [{"text": {"content": f"Meeting: {summary.title}"}}]}
        },
        "children": page_blocks
    }

    response = requests.post(
        "https://api.notion.com/v1/pages",
        json=payload, headers=get_headers()
    )
    if response.status_code != 200:
        raise Exception(f"Page creation failed: {response.json().get('message')}")

    summary_page_id = response.json().get("id")

    if task_list and task_list.items:
        db_id = create_tasks_database(summary.title, summary_page_id)
        if db_id:
            push_tasks_to_database(task_list, db_id)


# ─── YouTube Mode ─────────────────────────────────────────────────────────────

def push_youtube(insights: VideoInsights, video_url: str, task_list: ActionItemList = None):
    parent_page_id = clean_page_id(get_notion_page_id())

    page_blocks = [
        {
            "object": "block",
            "type": "bookmark",
            "bookmark": {"url": video_url}
        },
        make_divider(),
        make_callout(insights.summary, "🎬", "yellow_background"),
        make_divider(),
        make_heading("💡 Key Takeaways"),
        *[make_bullet(t) for t in insights.key_takeaways],
        make_divider(),
        make_heading("📚 Topics Covered"),
        *[make_bullet(t) for t in insights.topics_covered],
        make_divider(),
        make_heading("✅ Action Items"),
        *[make_bullet(a) for a in insights.action_items],
    ]

    payload = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "icon": {"type": "emoji", "emoji": "🎬"},
        "properties": {
            "title": {"title": [{"text": {"content": f"YouTube: {insights.title}"}}]}
        },
        "children": page_blocks
    }

    response = requests.post(
        "https://api.notion.com/v1/pages",
        json=payload, headers=get_headers()
    )
    if response.status_code != 200:
        raise Exception(f"Notion push failed: {response.json().get('message')}")

    notes_page_id = response.json().get("id")

    if task_list and task_list.items:
        db_id = create_tasks_database(insights.title, notes_page_id)
        if db_id:
            push_tasks_to_database(task_list, db_id)