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
    try:
        key = st.secrets.get("YOUTUBE_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return os.getenv("YOUTUBE_API_KEY", "")


def get_supadata_api_key():
    try:
        key = st.secrets.get("SUPADATA_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return os.getenv("SUPADATA_API_KEY", "")


# ─── URL Parsing ──────────────────────────────────────────────────────────────

def extract_video_id(url_or_id: str) -> str:
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


# ─── Timestamp Formatting ─────────────────────────────────────────────────────
#
# This is the key upgrade from v2.
# Instead of discarding timestamps, we embed [MM:SS] markers in the transcript
# every ~30 seconds. This lets the AI reference approximate video positions
# in every extracted fact, so users can jump back to the source.

def _format_transcript_with_timestamps(segments: list) -> tuple[str, float]:
    """
    Takes raw transcript segments (from youtube-transcript-api).
    Returns (formatted_transcript_with_timestamp_markers, duration_minutes).

    Timestamp markers are inserted every ~30 seconds.
    Format: [MM:SS] text text text [MM:SS] more text...
    """
    if not segments:
        return "", 0.0

    result = []
    last_marker_time = -31.0  # force a marker at the very start

    for seg in segments:
        start = seg.get("start", 0)
        text  = seg.get("text", "").strip()

        if not text:
            continue

        # Insert a timestamp marker every ~30 seconds
        if start - last_marker_time >= 30:
            minutes = int(start // 60)
            seconds = int(start % 60)
            result.append(f"[{minutes:02d}:{seconds:02d}]")
            last_marker_time = start

        result.append(text)

    # Calculate duration from last segment
    last_seg = segments[-1]
    duration_minutes = (
        last_seg.get("start", 0) + last_seg.get("duration", 0)
    ) / 60

    return " ".join(result), duration_minutes


def _plain_text_from_segments(segments: list) -> tuple[str, float]:
    """Fallback: plain text without timestamps (for Supadata / YouTube API)."""
    text = " ".join(s.get("text", "") for s in segments if s.get("text", "").strip())
    if segments:
        last = segments[-1]
        duration = (last.get("start", 0) + last.get("duration", 0)) / 60
    else:
        duration = 0.0
    return text.strip(), duration


# ─── Transcript Fetching Methods ──────────────────────────────────────────────

def _fetch_via_youtube_api(video_id: str) -> tuple | None:
    """
    Method 1: YouTube Data API v3 (official).
    Returns plain text (no per-segment timestamps available this way).
    """
    api_key = get_youtube_api_key()
    if not api_key:
        return None

    try:
        resp = requests.get(
            "https://www.googleapis.com/youtube/v3/captions",
            params={"part": "snippet", "videoId": video_id, "key": api_key},
            timeout=10
        )
        if resp.status_code == 403:
            print("  ⚠️  YouTube API quota exceeded")
            return None
        if resp.status_code != 200:
            return None

        items = resp.json().get("items", [])
        if not items:
            return None

        caption_id = None
        for item in items:
            if item["snippet"].get("language", "").startswith("en"):
                caption_id = item["id"]
                break
        if not caption_id:
            caption_id = items[0]["id"]

        dl_resp = requests.get(
            f"https://www.googleapis.com/youtube/v3/captions/{caption_id}",
            params={"tfmt": "srt", "key": api_key},
            timeout=15
        )
        if dl_resp.status_code != 200:
            return None

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


def _fetch_via_supadata(video_id: str) -> tuple | None:
    """
    Method 2: Supadata API.
    Returns plain text (no per-segment timestamps).
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

        data    = resp.json()
        content = data.get("content", "")
        if not content:
            return None

        text = content if isinstance(content, str) else " ".join(
            seg.get("text", "") for seg in content
        )
        duration_minutes = len(text.split()) / 130

        print("  ✅ Transcript via Supadata")
        return text, duration_minutes

    except Exception as e:
        print(f"  ⚠️  Supadata error: {e}")
        return None


def _fetch_via_scraping(video_id: str) -> tuple | None:
    """
    Method 3: youtube-transcript-api (scraping).
    This is the only method that gives us per-segment timestamps.
    Returns transcript WITH timestamp markers embedded.
    """
    try:
        data = YouTubeTranscriptApi().fetch(video_id).to_raw_data()

        if not data:
            return None

        # Use timestamp-formatted version — this is the upgrade
        text, duration = _format_transcript_with_timestamps(data)

        if not text.strip():
            return None

        print("  ✅ Transcript via scraping (with timestamps)")
        return text, duration

    except Exception as e:
        print(f"  ⚠️  Scraping error: {e}")
        return None


# ─── Main Transcript Function ─────────────────────────────────────────────────

def _inject_timestamps_into_plain_text(plain_text: str, segments: list) -> str:
    """
    Takes a plain-text transcript (from Supadata / YouTube API) and a list
    of raw timed segments (from scraping), and injects [MM:SS] markers into
    the plain text at approximately the right positions by word-count ratio.

    This is an approximation — the two sources may have slightly different
    word counts due to auto-caption cleaning. The result is accurate to
    within ~10-15 seconds, which is enough for users to navigate to the
    right spot in the video.
    """
    if not segments or not plain_text.strip():
        return plain_text

    # Build a list of (word_position_fraction, timestamp_string) from segments
    total_seg_words = sum(len(s.get("text", "").split()) for s in segments)
    if total_seg_words == 0:
        return plain_text

    markers = []  # (fraction_through_video, "[MM:SS]")
    running_words = 0
    last_marker_time = -31.0

    for seg in segments:
        start = seg.get("start", 0)
        seg_words = len(seg.get("text", "").split())
        running_words += seg_words
        fraction = running_words / total_seg_words

        # Only insert a marker every ~30 seconds
        if start - last_marker_time >= 30:
            minutes = int(start // 60)
            seconds = int(start % 60)
            markers.append((fraction, f"[{minutes:02d}:{seconds:02d}]"))
            last_marker_time = start

    if not markers:
        return plain_text

    # Inject markers into the plain text at the matching word positions
    words = plain_text.split()
    total_words = len(words)
    result = []
    marker_idx = 0

    for i, word in enumerate(words):
        # Check if we should insert the next marker here
        while marker_idx < len(markers):
            frac, marker = markers[marker_idx]
            if i >= int(frac * total_words):
                result.append(marker)
                marker_idx += 1
            else:
                break
        result.append(word)

    return " ".join(result)


def get_youtube_transcript(video_id: str) -> tuple[str, float]:
    """
    Fetch transcript with a reliability-first strategy that still gets
    real timestamps whenever possible.

    Strategy:
      1. Supadata PRIMARY — reliable on Streamlit Cloud, plain text only.
      2. Scraping TIMESTAMP LAYER — attempted silently alongside Supadata.
         If it works, timestamps from the scraping segments are injected
         into the Supadata text at approximate word positions.
         If scraping is rate-limited (which happens after 2-3 requests on
         shared servers), the Supadata transcript is returned as-is.
      3. YouTube Data API v3 FALLBACK — if Supadata also fails.
      4. Scraping FULL FALLBACK — last resort if both above fail.

    This means:
      - Reliability comes from Supadata (no IP-based rate limits)
      - Timestamps appear when scraping works (local dev, first daily uses)
      - When scraping is blocked, transcript is still complete — just no timestamps
      - The AI is told explicitly whether timestamps exist (no hallucination)
    """
    print(f"  🎬 Fetching transcript for: {video_id}")

    # ── Step 1: Get reliable transcript from Supadata ────────────────────────
    supadata_result = _fetch_via_supadata(video_id)

    if supadata_result:
        plain_text, duration = supadata_result

        # ── Step 2: Silently try scraping just for timestamps ────────────────
        # This is a best-effort attempt. If it fails, we don't care —
        # Supadata already gave us the complete transcript.
        try:
            raw_segments = YouTubeTranscriptApi().fetch(video_id).to_raw_data()
            if raw_segments:
                enriched_text = _inject_timestamps_into_plain_text(plain_text, raw_segments)
                has_ts = "[" in enriched_text and ":" in enriched_text
                label  = "✅ Supadata + timestamps injected" if has_ts else "✅ Supadata (no timestamps)"
                print(f"  📝 {len(enriched_text.split()):,} words | ~{duration:.1f} min | {label}")
                return enriched_text, duration
        except Exception:
            # Scraping blocked or failed — fine, continue with plain text
            pass

        print(f"  📝 {len(plain_text.split()):,} words | ~{duration:.1f} min | ⚠️ no timestamps (scraping blocked)")
        return plain_text, duration

    # ── Step 3: YouTube Data API v3 ──────────────────────────────────────────
    print("  🔄 Supadata failed, trying YouTube Data API v3...")
    yt_result = _fetch_via_youtube_api(video_id)
    if yt_result:
        text, duration = yt_result
        print(f"  📝 {len(text.split()):,} words | ~{duration:.1f} min | ⚠️ no timestamps")
        return text, duration

    # ── Step 4: Scraping full fallback ───────────────────────────────────────
    print("  🔄 Trying direct scraping as last resort...")
    scrape_result = _fetch_via_scraping(video_id)
    if scrape_result:
        text, duration = scrape_result
        print(f"  📝 {len(text.split()):,} words | ~{duration:.1f} min | ✅ timestamps (scraping worked)")
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
    """
    Returns a human-readable description of which transcript sources are configured.
    Shown in the YouTube Mode UI so users know what's available.
    """
    parts = []
    if get_supadata_api_key():
        parts.append("Supadata (primary)")
    if get_youtube_api_key():
        parts.append("YouTube API v3 (fallback)")
    parts.append("Scraping (timestamps + last resort)")
    return " · ".join(parts)


# ─── CLI ──────────────────────────────────────────────────────────────────────

def print_youtube_results(insights, processing_time, duration_minutes):
    print("\n" + "═" * 65)
    print("  🎬  YOUTUBE MODE — RESULTS")
    print("═" * 65)
    print(f"  📌 Title     : {insights.title}")
    print(f"  ⚡ Processed : {processing_time:.1f}s for ~{duration_minutes:.0f}min of video")
    print("─" * 65)

    if hasattr(insights, 'core_concept'):
        # StudyNotes
        print(f"  📐 Core Concept: {insights.core_concept}")
        print(f"  📋 Formulas    : {len(insights.formula_sheet)}")
        print(f"  ⚡ Key Facts   : {len(insights.key_facts)}")
        print(f"  🧪 Self-Test   : {len(insights.self_test)} questions")
    elif hasattr(insights, 'watch_or_skip'):
        # WorkBrief
        print(f"  📺 Verdict     : {insights.watch_or_skip}")
        print(f"  🛠️  Tools       : {', '.join(insights.tools_mentioned[:5])}")
        print(f"  💡 Key Points  : {len(insights.key_points)}")
    else:
        # VideoInsights (Quick)
        print(f"  💡 {insights.summary[:130]}")
    print("═" * 65)


def run_youtube_mode():
    print("\n" + "─" * 65)
    print("  🎬   YOUTUBE MODE")
    print(f"  📡   Sources: {get_transcript_source_info()}")
    print("─" * 65)

    url_input = input("  Paste YouTube URL or video ID: ").strip()
    video_id  = extract_video_id(url_input)

    print("\n  Output mode?")
    print("  [1] Study Mode  — technical depth, formulas, self-test")
    print("  [2] Work Mode   — professional brief, tools, decisions")
    print("  [3] Quick Mode  — conversational summary")
    mode_choice = input("\n  Enter choice (1/2/3): ").strip()
    mode = {"1": "study", "2": "work", "3": "quick"}.get(mode_choice, "quick")

    try:
        transcript, duration = get_youtube_transcript(video_id)
    except Exception as e:
        print(f"\n  ❌ {e}")
        return

    start_time = time.time()
    print(f"\n🤖 Running AI extraction in {mode} mode...")
    print(f"   Transcript: {len(transcript.split()):,} words (~{duration:.0f} min video)")

    insights = extract_video_insights(transcript, mode=mode, duration_minutes=duration)
    proc_time = time.time() - start_time

    print_youtube_results(insights, proc_time, duration)

    push = input("\n  Push to Notion? (y/n): ").strip().lower()
    if push == "y":
        from push_to_notion import push_study_notes, push_work_brief, push_youtube
        if mode == "study":
            push_study_notes(insights, url_input)
        elif mode == "work":
            push_work_brief(insights, url_input)
        else:
            push_youtube(insights, url_input)
    else:
        print("  Skipped Notion push.")