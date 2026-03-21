import os
import re
import time
import requests
import streamlit as st
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi

load_dotenv()
from gemini import extract_video_insights, extract_tasks, deduplicate_tasks, calculate_accuracy
from push_to_notion import push_youtube
from models import ActionItemList


# ─── API Key Helpers ──────────────────────────────────────────────────────────

def get_youtube_api_key():
    """YouTube Data API v3 key — Streamlit secrets first, then .env."""
    try:
        key = st.secrets.get("YOUTUBE_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return os.getenv("YOUTUBE_API_KEY", "")


def get_supadata_api_key():
    """Supadata API key — Streamlit secrets first, then .env."""
    try:
        key = st.secrets.get("SUPADATA_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return os.getenv("SUPADATA_API_KEY", "")


# ─── URL Parsing ──────────────────────────────────────────────────────────────

def extract_video_id(url_or_id: str) -> str:
    """
    Accepts any YouTube URL format or a raw video ID and returns just the ID.
      https://www.youtube.com/watch?v=abc123  → abc123
      https://youtu.be/abc123                → abc123
      abc123                                 → abc123
    """
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
        return url_or_id

    patterns = [
        r'[?&]v=([a-zA-Z0-9_-]{11})',
        r'youtu\.be/([a-zA-Z0-9_-]{11})',
        r'embed/([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)

    return url_or_id.strip()


# ─── Transcript Fetching — Three Methods ─────────────────────────────────────

def _fetch_via_youtube_api(video_id: str):
    """
    Method 1: YouTube Data API v3 (official).
    Reliable but limited to 100 quota units/day on free tier.
    Returns (text, duration_minutes) or None if unavailable/quota exceeded.
    """
    api_key = get_youtube_api_key()
    if not api_key:
        return None

    try:
        # Step 1: Get available caption tracks
        resp = requests.get(
            "https://www.googleapis.com/youtube/v3/captions",
            params={"part": "snippet", "videoId": video_id, "key": api_key},
            timeout=10
        )

        if resp.status_code == 403:
            print("  ⚠️  YouTube API quota exceeded — switching to fallback")
            return None
        if resp.status_code != 200:
            return None

        items = resp.json().get("items", [])
        if not items:
            return None

        # Prefer English captions
        caption_id = None
        for item in items:
            lang = item["snippet"].get("language", "")
            if lang.startswith("en"):
                caption_id = item["id"]
                break
        if not caption_id:
            caption_id = items[0]["id"]

        # Step 2: Download the caption track
        dl_resp = requests.get(
            f"https://www.googleapis.com/youtube/v3/captions/{caption_id}",
            params={"tfmt": "srt", "key": api_key},
            timeout=15
        )

        if dl_resp.status_code != 200:
            return None

        # Parse SRT — strip timestamps and sequence numbers
        lines = []
        for line in dl_resp.text.split("\n"):
            line = line.strip()
            if not line or line.isdigit() or "-->" in line:
                continue
            lines.append(line)
        text = " ".join(lines)

        # Get video duration
        v_resp = requests.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params={"part": "contentDetails", "id": video_id, "key": api_key},
            timeout=10
        )

        duration_minutes = 0.0
        if v_resp.status_code == 200:
            dur_str = v_resp.json().get("items", [{}])[0].get(
                "contentDetails", {}).get("duration", "PT0S")
            hours   = int(re.search(r'(\d+)H', dur_str).group(1)) if 'H' in dur_str else 0
            minutes = int(re.search(r'(\d+)M', dur_str).group(1)) if 'M' in dur_str else 0
            seconds = int(re.search(r'(\d+)S', dur_str).group(1)) if 'S' in dur_str else 0
            duration_minutes = hours * 60 + minutes + seconds / 60

        if not text.strip():
            return None

        print("  ✅ Transcript via YouTube Data API v3")
        return text, duration_minutes

    except Exception as e:
        print(f"  ⚠️  YouTube API error: {e}")
        return None


def _fetch_via_supadata(video_id: str):
    """
    Method 2: Supadata API.
    Scraping-based, works on most videos, more flexible than official API.
    Returns (text, duration_minutes) or None if unavailable.
    """
    api_key = get_supadata_api_key()
    if not api_key:
        return None

    try:
        resp = requests.get(
            "https://api.supadata.ai/v1/youtube/transcript",
            params={"videoId": video_id, "text": "true"},
            headers={"x-api-key": api_key},
            timeout=20
        )

        if resp.status_code == 429:
            print("  ⚠️  Supadata rate limit hit")
            return None
        if resp.status_code != 200:
            return None

        data = resp.json()
        content = data.get("content", "")
        if not content:
            return None

        text = content if isinstance(content, str) else " ".join(
            seg.get("text", "") for seg in content
        )

        # Estimate duration (~130 words per minute of speech)
        duration_minutes = len(text.split()) / 130

        print("  ✅ Transcript via Supadata")
        return text, duration_minutes

    except Exception as e:
        print(f"  ⚠️  Supadata error: {e}")
        return None


def _fetch_via_scraping(video_id: str):
    """
    Method 3: youtube-transcript-api (scraping fallback).
    Original method — works but gets rate-limited after a few requests
    on shared servers. Used as last resort.
    """
    try:
        data = YouTubeTranscriptApi().fetch(video_id).to_raw_data()
        text = " ".join([s["text"] for s in data])

        if data:
            last = data[-1]
            duration_minutes = (last["start"] + last.get("duration", 0)) / 60
        else:
            duration_minutes = 0.0

        if not text.strip():
            return None

        print("  ✅ Transcript via scraping (fallback)")
        return text, duration_minutes

    except Exception as e:
        print(f"  ⚠️  Scraping error: {e}")
        return None


# ─── Main Transcript Function ─────────────────────────────────────────────────

def get_youtube_transcript(video_id: str) -> tuple:
    """
    Fetch transcript using a 3-method fallback chain:
      1. YouTube Data API v3  (official, reliable, 100 req/day free)
      2. Supadata             (scraping-based, flexible)
      3. youtube-transcript-api (direct scraping, last resort)

    Raises Exception with clear message if all three methods fail.
    """
    print(f"  🎬 Fetching transcript for: {video_id}")

    result = _fetch_via_youtube_api(video_id)
    if result:
        text, duration = result
        print(f"  📝 {len(text.split()):,} words | ~{duration:.1f} min video")
        return text, duration

    print("  🔄 Trying Supadata...")
    result = _fetch_via_supadata(video_id)
    if result:
        text, duration = result
        print(f"  📝 {len(text.split()):,} words | ~{duration:.1f} min video")
        return text, duration

    print("  🔄 Trying direct scraping...")
    result = _fetch_via_scraping(video_id)
    if result:
        text, duration = result
        print(f"  📝 {len(text.split()):,} words | ~{duration:.1f} min video")
        return text, duration

    raise Exception(
        "Could not fetch transcript for this video.\n\n"
        "Possible reasons:\n"
        "• Video has no captions enabled\n"
        "• Video is private or age-restricted\n"
        "• Daily API quota exceeded (try again tomorrow)\n"
        "• Video is too new (captions not yet generated)"
    )


def get_transcript_source_info() -> str:
    """Returns which methods are configured — shown in Settings page."""
    methods = []
    if get_youtube_api_key():
        methods.append("YouTube API v3")
    if get_supadata_api_key():
        methods.append("Supadata")
    methods.append("Direct scraping")
    return " → ".join(methods)


# ─── CLI Version ──────────────────────────────────────────────────────────────

def print_youtube_results(insights, processing_time, duration_minutes):
    print("\n" + "═" * 65)
    print("  🎬  YOUTUBE MODE — RESULTS")
    print("═" * 65)
    print(f"  📌 Title     : {insights.title}")
    print(f"  ⚡ Processed : {processing_time:.1f}s for ~{duration_minutes:.0f}min of video")
    print("─" * 65)
    print(f"  💡 {insights.summary[:130]}")
    print("─" * 65)
    print("  📚 Topics Covered:")
    for t in insights.topics_covered:
        print(f"    • {t}")
    print("─" * 65)
    print("  🔑 Key Takeaways:")
    for i, t in enumerate(insights.key_takeaways, 1):
        print(f"    {i}. {t}")
    print("─" * 65)
    print("  ✅ Action Items:")
    for a in insights.action_items:
        print(f"    → {a}")
    print("═" * 65)


def run_youtube_mode():
    print("\n" + "─" * 65)
    print("  🎬   YOUTUBE MODE")
    print(f"  📡   Sources: {get_transcript_source_info()}")
    print("─" * 65)

    url_input = input("  Paste YouTube URL or video ID: ").strip()
    video_id  = extract_video_id(url_input)

    print("\n  What do you want to extract?")
    print("  [1] Key insights + takeaways")
    print("  [2] Action items + tasks")
    print("  [3] Both")
    extract_choice = input("\n  Enter choice (1/2/3): ").strip()

    try:
        transcript, duration = get_youtube_transcript(video_id)
    except Exception as e:
        print(f"\n  ❌ {e}")
        return

    start_time = time.time()
    print("\n🤖 Running AI extraction...")

    insights  = None
    task_list = None

    if extract_choice in ("1", "3"):
        insights = extract_video_insights(transcript)

    if extract_choice in ("2", "3"):
        raw_tasks = extract_tasks(transcript)
        task_list = deduplicate_tasks(raw_tasks)

    if extract_choice == "2" and task_list:
        from models import VideoInsights
        insights = VideoInsights(
            title=f"Video {video_id}",
            summary="Task extraction mode — see tasks database.",
            key_takeaways=[], topics_covered=[], action_items=[]
        )

    processing_time = time.time() - start_time

    if insights and extract_choice != "2":
        print_youtube_results(insights, processing_time, duration)

    if task_list:
        accuracy = calculate_accuracy(task_list)
        print(f"\n  📝 {len(task_list.items)} tasks extracted | Accuracy: {accuracy}%")
        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        sorted_tasks = sorted(task_list.items, key=lambda x: priority_order.get(x.priority, 1))
        for i, item in enumerate(sorted_tasks, 1):
            print(f"    {i}. [{item.priority}] {item.assignee} — {item.task[:50]}")

    push = input("\n  Push to Notion? (y/n): ").strip().lower()
    if push == "y":
        push_youtube(insights, url_input, task_list)
    else:
        print("  Skipped Notion push.")