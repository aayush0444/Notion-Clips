import os
import requests
from dotenv import load_dotenv
from models import ActionItemList, MeetingSummary, VideoInsights

load_dotenv()

NOTION_VERSION   = "2022-06-28"
PRIORITY_COLORS  = {"High": "red", "Medium": "yellow", "Low": "green"}


# ─── Shared Helpers ───────────────────────────────────────────────────────────

def get_headers():
    return {
        "Authorization": f"Bearer {os.getenv('NOTION_TOKEN')}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }

def clean_page_id(page_id: str) -> str:
    """Handle full Notion URLs or raw IDs."""
    if "/" in page_id:
        page_id = page_id.split("/")[-1].split("?")[0]
    return page_id.replace("-", "")[-32:]

def make_bullet(text: str) -> dict:
    """Shortcut to create a Notion bulleted list block."""
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [{"type": "text", "text": {"content": text}}]
        }
    }

def make_heading(text: str) -> dict:
    """Shortcut to create a Notion heading_2 block."""
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
            "rich_text": [{"type": "text", "text": {"content": text}}],
            "icon": {"emoji": emoji},
            "color": color
        }
    }

def create_tasks_database(title: str, parent_page_id: str) -> str | None:
    """Creates a tasks database inside a Notion page. Returns database ID."""
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

    response = requests.post("https://api.notion.com/v1/databases", json=payload, headers=get_headers())
    if response.status_code == 200:
        print(f"  ✅ Tasks database created")
        return response.json().get("id")
    else:
        print(f"  ❌ Database failed: {response.json().get('message')}")
        return None

def push_tasks_to_database(task_list: ActionItemList, database_id: str):
    """Push each task as a row into a Notion database."""
    success = 0
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

        response = requests.post("https://api.notion.com/v1/pages", json=payload, headers=get_headers())
        if response.status_code == 200:
            success += 1
            print(f"  ➕ [{priority:6}] {item.assignee[:12]:12} | {item.task[:45]}")
        else:
            print(f"  ❌ Failed to add: {item.task[:40]}")

    print(f"\n  📊 {success}/{len(task_list.items)} tasks added")


# ─── Meeting Mode ─────────────────────────────────────────────────────────────

def push_meeting(task_list: ActionItemList, summary: MeetingSummary):
    """
    Creates in Notion:
      Hub Page
        └── Meeting Notes: <title>   (summary page)
              └── Tasks: <title>     (tasks database)
    """
    parent_page_id = clean_page_id(os.getenv("NOTION_PAGE_ID"))
    print("\n📤 Pushing to Notion (Meeting Mode)...")

    # Build the summary page content
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

    response = requests.post("https://api.notion.com/v1/pages", json=payload, headers=get_headers())
    if response.status_code != 200:
        print(f"  ❌ Page creation failed: {response.json().get('message')}")
        return

    summary_page_id = response.json().get("id")
    print(f"  ✅ Meeting notes page created: {summary.title}")

    # Create tasks database inside the summary page
    db_id = create_tasks_database(summary.title, summary_page_id)
    if not db_id:
        return

    push_tasks_to_database(task_list, db_id)
    print(f"\n✅ Meeting '{summary.title}' is live in Notion!")


# ─── YouTube Mode ─────────────────────────────────────────────────────────────

def push_youtube(insights: VideoInsights, video_url: str, task_list: ActionItemList = None):
    """
    Creates in Notion:
      Hub Page
        └── YouTube: <title>   (insights page with all key points)
    """
    parent_page_id = clean_page_id(os.getenv("NOTION_PAGE_ID"))
    print("\n📤 Pushing to Notion (YouTube Mode)...")

    page_blocks = [
        # Video URL as a clickable link
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

    response = requests.post("https://api.notion.com/v1/pages", json=payload, headers=get_headers())
    if response.status_code == 200:
        notes_page_id = response.json().get("id")
        print(f"  ✅ YouTube notes page created: {insights.title}")

        # If tasks were also extracted, add a tasks database inside the page
        if task_list and task_list.items:
            db_id = create_tasks_database(insights.title, notes_page_id)
            if db_id:
                push_tasks_to_database(task_list, db_id)

        print(f"\n✅ Video notes are live in Notion!")
    else:
        print(f"  ❌ Failed: {response.json().get('message')}")