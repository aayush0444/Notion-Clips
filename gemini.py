import os
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from models import ActionItemList, MeetingSummary, VideoInsights

# ─── Model Selection ──────────────────────────────────────────────────────────
#
# Priority order for API keys:
#   1. User's own key from .env / Settings page  (they entered it themselves)
#   2. App's shared OpenRouter key from Streamlit secrets  (your key, pre-provided)
#
# This means:
#   - Most users just enter Notion credentials and go — AI is handled for them
#   - Power users can override with their own key if they want

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL    = "openai/gpt-4o-mini"


def get_openrouter_key():
    """
    Get OpenRouter key — user's own first, then fall back to app's shared key.
    Checks Streamlit secrets safely (won't crash if secret doesn't exist).
    """
    # 1. User's own key from .env
    user_key = os.getenv("OPENROUTER_API_KEY")
    if user_key:
        return user_key

    # 2. App's shared key from Streamlit Cloud secrets
    try:
        app_key = st.secrets.get("OPENROUTER_API_KEY", "")
        if app_key:
            return app_key
    except Exception:
        pass  # Running locally without secrets — that's fine

    return None


def get_google_key():
    """Get Google Gemini key from .env or Streamlit secrets."""
    user_key = os.getenv("GOOGLE_API_KEY")
    if user_key:
        return user_key
    try:
        return st.secrets.get("GOOGLE_API_KEY", "")
    except Exception:
        return None


def get_model():
    """
    Returns the best available model.
    OpenRouter is preferred (cheaper, more flexible).
    Falls back to Gemini if OpenRouter key not available.
    """
    or_key = get_openrouter_key()
    if or_key:
        return ChatOpenAI(
            model=OPENROUTER_MODEL,
            api_key=or_key,
            base_url=OPENROUTER_BASE_URL,
            temperature=0
        )

    g_key = get_google_key()
    if g_key:
        return ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)

    # No key found at all
    raise ValueError(
        "No AI API key found. Please add your Gemini or OpenRouter key in Settings, "
        "or contact support if you're using the hosted version."
    )


# ─── Meeting Mode Extraction ──────────────────────────────────────────────────

def extract_tasks(transcript: str) -> ActionItemList:
    """Extract all action items and tasks from a meeting transcript."""
    structured_llm = get_model().with_structured_output(ActionItemList)

    prompt = f"""
    You are an expert meeting analyst.
    Extract ALL action items and tasks from this transcript.

    For each task identify:
    - The specific task to be done
    - Who is responsible (use "Team" if unclear)
    - Due date in YYYY-MM-DD format, or "TBD"
    - Priority: High (urgent), Medium (important), Low (nice to have)

    Be thorough — capture every commitment, follow-up, and deliverable mentioned.

    TRANSCRIPT:
    {transcript}
    """
    return structured_llm.invoke(prompt)


def extract_meeting_summary(transcript: str) -> MeetingSummary:
    """Generate a structured summary of a meeting."""
    structured_llm = get_model().with_structured_output(MeetingSummary)

    prompt = f"""
    You are an expert meeting analyst.
    Analyze this meeting transcript and provide:
    - A concise meeting title (max 8 words)
    - An executive summary (3-4 sentences: what was discussed and decided)
    - Key decisions made (up to 5)
    - Clear next steps agreed upon (up to 5)

    TRANSCRIPT:
    {transcript}
    """
    return structured_llm.invoke(prompt)


# ─── YouTube Mode Extraction ──────────────────────────────────────────────────

def extract_video_insights(transcript: str) -> VideoInsights:
    """Extract key insights and takeaways from a YouTube video transcript."""
    structured_llm = get_model().with_structured_output(VideoInsights)

    prompt = f"""
    You are an expert content analyst.
    Someone doesn't have time to watch this video — give them everything they need to know.

    Provide:
    - A short title describing what the video is about
    - A 3-4 sentence summary of the content
    - The most important takeaways (up to 7 key points worth remembering)
    - Main topics or sections covered (up to 5)
    - Action items: things the viewer should do or explore after watching (up to 5)

    VIDEO TRANSCRIPT:
    {transcript}
    """
    return structured_llm.invoke(prompt)


# ─── Shared Utilities ─────────────────────────────────────────────────────────

def deduplicate_tasks(task_data: ActionItemList) -> ActionItemList:
    """Remove duplicate tasks using a (task, assignee) fingerprint."""
    seen = set()
    unique = []
    for item in task_data.items:
        fingerprint = (item.task.lower().strip(), item.assignee.lower().strip())
        if fingerprint not in seen:
            seen.add(fingerprint)
            unique.append(item)
    task_data.items = unique
    return task_data


def calculate_accuracy(task_list: ActionItemList) -> float:
    """
    Score task extraction quality based on completeness.
    - 40pts: meaningful task description (3+ words)
    - 25pts: specific assignee (not just "Team")
    - 20pts: actual due date (not TBD)
    - 15pts: valid priority value
    """
    if not task_list.items:
        return 0.0

    scores = []
    for item in task_list.items:
        score = 0
        if item.task and len(item.task.split()) >= 3:   score += 40
        if item.assignee and item.assignee != "Team":   score += 25
        if item.due_date and item.due_date != "TBD":    score += 20
        if item.priority in ("High", "Medium", "Low"):  score += 15
        scores.append(score)

    return round(sum(scores) / len(scores), 1)