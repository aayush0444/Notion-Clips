import os
import requests
import streamlit as st
from dotenv import load_dotenv
from models import ActionItemList, MeetingSummary, VideoInsights, StudyNotes, WorkBrief

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

def make_numbered(text: str) -> dict:
    return {
        "object": "block",
        "type": "numbered_list_item",
        "numbered_list_item": {
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

def make_quote(text: str) -> dict:
    return {
        "object": "block",
        "type": "quote",
        "quote": {
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}]
        }
    }

def make_code(text: str, language: str = "plain text") -> dict:
    return {
        "object": "block",
        "type": "code",
        "code": {
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}],
            "language": language
        }
    }

def make_paragraph(text: str) -> dict:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}]
        }
    }

def make_toggle(question: str, answer_placeholder: str) -> dict:
    """
    Toggle block: question is visible title.
    Answer placeholder is inside — hidden until the user clicks to expand.
    This forces active recall: student must attempt the answer before opening.
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
                                "text": {"content": answer_placeholder[:2000]},
                                "annotations": {"italic": True, "color": "gray"}
                            }
                        ]
                    }
                }
            ]
        }
    }

def make_todo(text: str, checked: bool = False) -> dict:
    """Notion checkbox item — actually checkable in the Notion UI."""
    return {
        "object": "block",
        "type": "to_do",
        "to_do": {
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}],
            "checked": checked
        }
    }

def make_tools_paragraph(tools: list) -> dict:
    """
    Renders tool names as inline code spans in a single paragraph.
    Each tool name gets code annotation (monospaced, slight background).
    """
    rich_text = []
    for i, tool in enumerate(tools):
        rich_text.append({
            "type": "text",
            "text": {"content": tool},
            "annotations": {"code": True}
        })
        if i < len(tools) - 1:
            rich_text.append({
                "type": "text",
                "text": {"content": "   "}
            })
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": rich_text}
    }

def make_bookmark(url: str) -> dict:
    return {
        "object": "block",
        "type": "bookmark",
        "bookmark": {"url": url}
    }

def _create_page(parent_page_id: str, title: str, emoji: str, blocks: list) -> str:
    """Create a Notion page and return its ID. Raises on failure."""
    parent_page_id = clean_page_id(parent_page_id)
    payload = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "icon": {"type": "emoji", "emoji": emoji},
        "properties": {
            "title": {"title": [{"text": {"content": title}}]}
        },
        "children": blocks
    }
    response = requests.post(
        "https://api.notion.com/v1/pages",
        json=payload,
        headers=get_headers()
    )
    if response.status_code != 200:
        raise Exception(f"Page creation failed: {response.json().get('message')}")
    return response.json().get("id")

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


# ─── YouTube Quick Mode ───────────────────────────────────────────────────────

def push_youtube(
    insights: VideoInsights,
    video_url: str,
    task_list: ActionItemList = None,
    sections: dict = None
):
    """
    Push Quick mode YouTube notes to Notion.
    sections dict controls which blocks are included in the page.
    If sections is None, all blocks are included (backward compatible).
    """
    if sections is None:
        sections = {
            "summary":       True,
            "key_takeaways": True,
            "topics":        True,
            "action_items":  True,
        }

    parent_page_id = clean_page_id(get_notion_page_id())

    page_blocks = [
        make_bookmark(video_url),
        make_divider(),
    ]

    if sections.get("summary", True) and insights.summary:
        page_blocks.append(make_callout(insights.summary, "🎬", "yellow_background"))
        page_blocks.append(make_divider())

    if sections.get("key_takeaways", True) and insights.key_takeaways:
        page_blocks.append(make_heading("💡 Key Takeaways"))
        page_blocks.extend([make_bullet(t) for t in insights.key_takeaways])
        page_blocks.append(make_divider())

    if sections.get("topics", True) and insights.topics_covered:
        page_blocks.append(make_heading("📚 Topics Covered"))
        page_blocks.extend([make_bullet(t) for t in insights.topics_covered])
        page_blocks.append(make_divider())

    if sections.get("action_items", True) and insights.action_items:
        page_blocks.append(make_heading("✅ Action Items"))
        page_blocks.extend([make_bullet(a) for a in insights.action_items])

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


# ─── YouTube Study Mode ───────────────────────────────────────────────────────

def push_study_notes(notes: StudyNotes, video_url: str):
    """
    Push Study Mode output to Notion.

    Page structure:
    - Video bookmark
    - Core Concept callout (yellow — the thing to memorise)
    - Formula Sheet as code blocks (monospaced)
    - Key Facts as numbered list
    - Common Mistakes as bullets
    - Self-Test as toggle blocks (question visible, answer placeholder hidden inside)
    - Prerequisites + Further Reading as bullets
    """
    parent_page_id = clean_page_id(get_notion_page_id())

    blocks = [
        make_bookmark(video_url),
        make_divider(),

        # Core concept — most important block on the page
        make_callout(notes.core_concept, "📐", "yellow_background"),
        make_divider(),
    ]

    # Formula sheet
    if notes.formula_sheet:
        blocks.append(make_heading("📋 Formula Sheet"))
        for formula in notes.formula_sheet:
            blocks.append(make_code(formula, language="plain text"))
        blocks.append(make_divider())

    # Key facts
    if notes.key_facts:
        blocks.append(make_heading("⚡ Key Facts"))
        for fact in notes.key_facts:
            blocks.append(make_numbered(fact))
        blocks.append(make_divider())

    # Common mistakes
    if notes.common_mistakes:
        blocks.append(make_heading("⚠️ Common Mistakes"))
        for mistake in notes.common_mistakes:
            blocks.append(make_bullet(f"⚠️ {mistake}"))
        blocks.append(make_divider())

    # Self-test — toggle blocks so answers are hidden
    if notes.self_test:
        blocks.append(make_heading("🧪 Self-Test"))
        blocks.append(make_paragraph(
            "Try to answer each question before expanding it. "
            "Write your answer out — don't just think it."
        ))
        for question in notes.self_test:
            blocks.append(make_toggle(
                question=question,
                answer_placeholder="[Write your answer here before opening — active recall works better than passive reading]"
            ))
        blocks.append(make_divider())

    # Prerequisites
    if notes.prerequisites:
        blocks.append(make_heading("📚 Prerequisites"))
        for prereq in notes.prerequisites:
            blocks.append(make_bullet(prereq))

    # Further reading
    if notes.further_reading:
        blocks.append(make_heading("📖 Further Reading"))
        for resource in notes.further_reading:
            blocks.append(make_bullet(resource))

    _create_page(
        parent_page_id=parent_page_id,
        title=f"Study: {notes.title}",
        emoji="📐",
        blocks=blocks
    )


# ─── YouTube Work Mode ────────────────────────────────────────────────────────

def push_work_brief(brief: WorkBrief, video_url: str):
    """
    Push Work Mode output to Notion.

    Page structure:
    - Video bookmark
    - Watch/Skip callout (green or red based on verdict)
    - One-liner as quote block
    - Key Points as bullets
    - Tools Mentioned as inline code spans
    - Decisions to Make as checkbox (to_do) blocks — actually checkable
    - Next Actions as bullets
    """
    parent_page_id = clean_page_id(get_notion_page_id())

    # Determine watch/skip colour
    verdict = brief.watch_or_skip.strip()
    if verdict.lower().startswith("watch"):
        verdict_emoji = "🟢"
        verdict_color = "green_background"
    else:
        verdict_emoji = "🔴"
        verdict_color = "red_background"

    blocks = [
        make_bookmark(video_url),
        make_divider(),

        # Watch/Skip verdict — most important thing at the top
        make_callout(verdict, verdict_emoji, verdict_color),

        # One-liner as a quote
        make_quote(brief.one_liner),
        make_divider(),
    ]

    # Key points
    if brief.key_points:
        blocks.append(make_heading("💡 Key Points"))
        for point in brief.key_points:
            blocks.append(make_bullet(point))
        blocks.append(make_divider())

    # Tools mentioned — inline code spans in one paragraph
    if brief.tools_mentioned:
        blocks.append(make_heading("🛠️ Tools Mentioned"))
        blocks.append(make_tools_paragraph(brief.tools_mentioned))
        blocks.append(make_divider())

    # Decisions — actual Notion checkboxes
    if brief.decisions_to_make:
        blocks.append(make_heading("✅ Decisions to Make"))
        for decision in brief.decisions_to_make:
            blocks.append(make_todo(decision, checked=False))
        blocks.append(make_divider())

    # Next actions
    if brief.next_actions:
        blocks.append(make_heading("🚀 Next Actions"))
        for action in brief.next_actions:
            blocks.append(make_bullet(f"→ {action}"))

    _create_page(
        parent_page_id=parent_page_id,
        title=f"Work Brief: {brief.title}",
        emoji="💼",
        blocks=blocks
    )