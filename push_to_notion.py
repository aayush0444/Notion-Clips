import os
from typing import Optional

import requests
import streamlit as st
from dotenv import load_dotenv
from models import ActionItemList, MeetingSummary, VideoInsights, StudyNotes, WorkBrief

load_dotenv()

NOTION_VERSION  = "2022-06-28"
PRIORITY_COLORS = {"High": "red", "Medium": "yellow", "Low": "green"}

# Notion API limit: 100 children blocks per request
NOTION_BLOCK_LIMIT = 90  # leave some buffer


# ─── Auth Helpers ─────────────────────────────────────────────────────────────

def get_notion_token(override: Optional[str] = None):
    if override:
        return override
    token = os.getenv("NOTION_TOKEN")
    if token:
        return token
    try:
        return st.secrets.get("NOTION_TOKEN", "")
    except Exception:
        return None


def clean_page_id(page_id: str) -> str:
    if not page_id:
        raise ValueError("Notion Page ID not found. Please add your Page ID in Settings.")
    if "/" in page_id:
        page_id = page_id.split("/")[-1].split("?")[0]
    return page_id.replace("-", "")[-32:]


def get_notion_page_id(override: Optional[str] = None):
    if override:
        return clean_page_id(override)
    page_id = os.getenv("NOTION_PAGE_ID")
    if page_id:
        return clean_page_id(page_id)
    try:
        secret_value = st.secrets.get("NOTION_PAGE_ID", "")
        return clean_page_id(secret_value) if secret_value else None
    except Exception:
        return None


def get_headers(token_override: Optional[str] = None):
    token = get_notion_token(token_override)
    if not token:
        raise ValueError("Notion token not found. Please add your token in Settings.")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }


# ─── Block Builders ───────────────────────────────────────────────────────────

def make_bullet(text: str) -> dict:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}]
        }
    }

def make_numbered(text: str) -> dict:
    return {
        "object": "block",
        "type": "numbered_list_item",
        "numbered_list_item": {
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}]
        }
    }

def make_heading(text: str, level: int = 2) -> dict:
    h_type = f"heading_{level}"
    return {
        "object": "block",
        "type": h_type,
        h_type: {
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

def make_code_block(text: str) -> dict:
    """Monospaced block — ideal for formulas."""
    return {
        "object": "block",
        "type": "code",
        "code": {
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}],
            "language": "plain text"
        }
    }

def make_toggle(question: str, answer_placeholder: str = "[Write your answer here before expanding]") -> dict:
    """
    Toggle block for self-test questions.
    Question is visible as the title.
    Answer placeholder is hidden inside — student fills it in for active recall.
    """
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
                                "annotations": {"italic": True, "color": "gray"}
                            }
                        ]
                    }
                }
            ]
        }
    }

def make_todo(text: str, checked: bool = False) -> dict:
    """Checkbox item — actually checkable in Notion."""
    return {
        "object": "block",
        "type": "to_do",
        "to_do": {
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}],
            "checked": checked
        }
    }

def make_quote(text: str) -> dict:
    return {
        "object": "block",
        "type": "quote",
        "quote": {
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}]
        }
    }

def make_bookmark(url: str) -> dict:
    return {
        "object": "block",
        "type": "bookmark",
        "bookmark": {"url": url}
    }

def make_paragraph(text: str, italic: bool = False, color: str = "default") -> dict:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": text[:2000]},
                    "annotations": {"italic": italic, "color": color}
                }
            ]
        }
    }


# ─── Append Blocks (handles >90 block limit) ──────────────────────────────────

def _append_blocks(page_id: str, blocks: list, notion_token: Optional[str] = None):
    """
    Append blocks to an existing page in batches of NOTION_BLOCK_LIMIT.
    Notion allows max 100 children per request.
    """
    page_id = clean_page_id(page_id)
    for i in range(0, len(blocks), NOTION_BLOCK_LIMIT):
        batch = blocks[i:i + NOTION_BLOCK_LIMIT]
        resp = requests.patch(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            json={"children": batch},
            headers=get_headers(notion_token)
        )
        if resp.status_code not in (200, 201):
            raise Exception(f"Failed to append blocks: {resp.json().get('message')}")


def _create_page_with_overflow(
    parent_page_id: str,
    payload: dict,
    extra_blocks: list,
    notion_token: Optional[str] = None
) -> str:
    """
    Create a page with the first batch of children inline,
    then append remaining blocks separately.
    Returns the created page ID.
    """
    response = requests.post(
        "https://api.notion.com/v1/pages",
        json=payload,
        headers=get_headers(notion_token)
    )
    if response.status_code not in (200, 201):
        raise Exception(f"Page creation failed: {response.json().get('message')}")

    page_id = response.json().get("id")

    # Append remaining blocks if any
    if extra_blocks:
        _append_blocks(page_id, extra_blocks, notion_token)

    return page_id


# ─── Tasks Database (shared between modes) ────────────────────────────────────

def create_tasks_database(title: str, parent_page_id: str, notion_token: Optional[str] = None) -> str | None:
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
        json=payload, headers=get_headers(notion_token)
    )
    if response.status_code in (200, 201):
        return response.json().get("id")
    raise Exception(f"Database creation failed: {response.json().get('message')}")


def push_tasks_to_database(task_list: ActionItemList, database_id: str, notion_token: Optional[str] = None):
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
            json=payload, headers=get_headers(notion_token)
        )


# ─── Study Mode Push ──────────────────────────────────────────────────────────

def push_study_notes(
    notes: StudyNotes,
    video_url: str,
    notion_token: Optional[str] = None,
    notion_page_id: Optional[str] = None,
) -> str:
    """
    Create a structured study notes page in Notion.

    Page structure:
    - Video bookmark
    - Core Concept callout (the one thing to memorise)
    - Formula Sheet (code blocks — monospaced, scannable)
    - Key Facts (numbered list — scales to video length)
    - Common Mistakes
    - Self-Test (toggle blocks — question visible, answer hidden)
    - Prerequisites + Further Reading
    """
    parent_page_id = clean_page_id(get_notion_page_id(notion_page_id))

    all_blocks = [
        make_bookmark(video_url),
        make_divider(),
        make_callout(notes.core_concept, "📐", "yellow_background"),
        make_divider(),
    ]

    # Formula Sheet
    if notes.formula_sheet:
        all_blocks.append(make_heading("📋 Formula Sheet"))
        all_blocks.append(
            make_paragraph(
                "Each formula below includes definitions of every variable.",
                italic=True, color="gray"
            )
        )
        for formula in notes.formula_sheet:
            all_blocks.append(make_code_block(formula))
        all_blocks.append(make_divider())

    # Key Facts (scaled — could be 30-50 for a 2hr video)
    if notes.key_facts:
        all_blocks.append(make_heading("⚡ Key Facts"))
        all_blocks.append(
            make_paragraph(
                f"{len(notes.key_facts)} facts extracted from this video. "
                "Timestamps (≈MM:SS) indicate where in the video each fact appears.",
                italic=True, color="gray"
            )
        )
        for fact in notes.key_facts:
            all_blocks.append(make_numbered(fact))
        all_blocks.append(make_divider())

    # Common Mistakes
    if notes.common_mistakes:
        all_blocks.append(make_heading("⚠️ Common Mistakes"))
        for mistake in notes.common_mistakes:
            all_blocks.append(make_bullet(mistake))
        all_blocks.append(make_divider())

    # Self-Test (toggle blocks)
    if notes.self_test:
        all_blocks.append(make_heading("🧪 Self-Test"))
        all_blocks.append(
            make_paragraph(
                "Click each question to open it. Try to answer before looking.",
                italic=True, color="gray"
            )
        )
        for i, question in enumerate(notes.self_test, 1):
            all_blocks.append(make_toggle(f"Q{i}: {question}"))
        all_blocks.append(make_divider())

    # Prerequisites
    if notes.prerequisites:
        all_blocks.append(make_heading("📚 Prerequisites", level=3))
        for prereq in notes.prerequisites:
            all_blocks.append(make_bullet(prereq))

    # Further Reading
    if notes.further_reading:
        all_blocks.append(make_heading("📖 Further Reading", level=3))
        for resource in notes.further_reading:
            all_blocks.append(make_bullet(resource))

    # Split into first batch (inline) and overflow
    first_batch  = all_blocks[:NOTION_BLOCK_LIMIT]
    extra_blocks = all_blocks[NOTION_BLOCK_LIMIT:]

    payload = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "icon": {"type": "emoji", "emoji": "📐"},
        "properties": {
            "title": {"title": [{"text": {"content": f"Study: {notes.title}"}}]}
        },
        "children": first_batch
    }

    page_id = _create_page_with_overflow(parent_page_id, payload, extra_blocks, notion_token)
    return page_id


# ─── Work Mode Push ───────────────────────────────────────────────────────────

def push_work_brief(
    brief: WorkBrief,
    video_url: str,
    notion_token: Optional[str] = None,
    notion_page_id: Optional[str] = None,
) -> str:
    """
    Create a structured work brief page in Notion.

    Page structure:
    - Video bookmark
    - Watch/Skip verdict callout (prominent, coloured)
    - One-liner quote
    - Key Points
    - Tools Mentioned
    - Decisions to Make (checkbox items — actually checkable)
    - Next Actions
    """
    parent_page_id = clean_page_id(get_notion_page_id(notion_page_id))

    # Determine watch/skip styling
    is_watch = brief.watch_or_skip.lower().startswith("watch")
    verdict_emoji = "🟢" if is_watch else "🔴"
    verdict_color = "green_background" if is_watch else "red_background"

    all_blocks = [
        make_bookmark(video_url),
        make_divider(),
        make_callout(brief.watch_or_skip, verdict_emoji, verdict_color),
        make_quote(brief.one_liner),
        make_divider(),
    ]

    # Key Points
    if brief.key_points:
        all_blocks.append(make_heading("💡 Key Points"))
        for point in brief.key_points:
            all_blocks.append(make_bullet(point))
        all_blocks.append(make_divider())

    # Tools Mentioned
    if brief.tools_mentioned:
        all_blocks.append(make_heading("🛠️ Tools Mentioned", level=3))
        # All tools in one paragraph with code formatting per tool
        # Notion rich_text supports annotations per span
        tools_block = {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": []
            }
        }
        for i, tool in enumerate(brief.tools_mentioned):
            tools_block["paragraph"]["rich_text"].append({
                "type": "text",
                "text": {"content": tool},
                "annotations": {"code": True}
            })
            if i < len(brief.tools_mentioned) - 1:
                tools_block["paragraph"]["rich_text"].append({
                    "type": "text",
                    "text": {"content": "  "}
                })
        all_blocks.append(tools_block)
        all_blocks.append(make_divider())

    # Decisions to Make (actual Notion checkboxes)
    if brief.decisions_to_make:
        all_blocks.append(make_heading("✅ Decisions to Make"))
        all_blocks.append(
            make_paragraph(
                "Check these off as your team works through them.",
                italic=True, color="gray"
            )
        )
        for decision in brief.decisions_to_make:
            all_blocks.append(make_todo(decision, checked=False))
        all_blocks.append(make_divider())

    # Next Actions
    if brief.next_actions:
        all_blocks.append(make_heading("🚀 Next Actions", level=3))
        for action in brief.next_actions:
            all_blocks.append(make_bullet(action))

    # Split and create
    first_batch  = all_blocks[:NOTION_BLOCK_LIMIT]
    extra_blocks = all_blocks[NOTION_BLOCK_LIMIT:]

    payload = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "icon": {"type": "emoji", "emoji": verdict_emoji},
        "properties": {
            "title": {"title": [{"text": {"content": f"Brief: {brief.title}"}}]}
        },
        "children": first_batch
    }

    page_id = _create_page_with_overflow(parent_page_id, payload, extra_blocks, notion_token)
    return page_id


# ─── Quick Mode Push (unchanged) ─────────────────────────────────────────────

def push_youtube(
    insights: VideoInsights,
    video_url: str,
    task_list: ActionItemList = None,
    sections: dict = None,
    notion_token: Optional[str] = None,
    notion_page_id: Optional[str] = None,
):
    if sections is None:
        sections = {
            "summary": True, "key_takeaways": True,
            "topics": True, "action_items": True,
        }

    parent_page_id = clean_page_id(get_notion_page_id(notion_page_id))

    page_blocks = [make_bookmark(video_url), make_divider()]

    if sections.get("summary", True) and insights.summary:
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

    first_batch  = page_blocks[:NOTION_BLOCK_LIMIT]
    extra_blocks = page_blocks[NOTION_BLOCK_LIMIT:]

    payload = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "icon": {"type": "emoji", "emoji": "🎬"},
        "properties": {
            "title": {"title": [{"text": {"content": f"YouTube: {insights.title}"}}]}
        },
        "children": first_batch
    }

    page_id = _create_page_with_overflow(parent_page_id, payload, extra_blocks, notion_token)

    if task_list and task_list.items:
        db_id = create_tasks_database(insights.title, page_id, notion_token)
        if db_id:
            push_tasks_to_database(task_list, db_id, notion_token)


# ─── Meeting Mode (unchanged) ─────────────────────────────────────────────────

def push_meeting(
    task_list: ActionItemList,
    summary: MeetingSummary,
    notion_token: Optional[str] = None,
    notion_page_id: Optional[str] = None,
):
    parent_page_id = clean_page_id(get_notion_page_id(notion_page_id))

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
        json=payload, headers=get_headers(notion_token)
    )
    if response.status_code not in (200, 201):
        raise Exception(f"Page creation failed: {response.json().get('message')}")

    summary_page_id = response.json().get("id")

    if task_list and task_list.items:
        db_id = create_tasks_database(summary.title, summary_page_id, notion_token)
        if db_id:
            push_tasks_to_database(task_list, db_id, notion_token)
