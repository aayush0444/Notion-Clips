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

def get_supadata_api_key():
    try:
        key = st.secrets.get("SUPADATA_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return os.getenv("SUPADATA_API_KEY", "")


def _is_cloud_runtime() -> bool:
    return bool(
        os.getenv("RENDER")
        or os.getenv("VERCEL")
        or os.getenv("K_SERVICE")
        or os.getenv("FLY_APP_NAME")
        or os.getenv("DYNO")
    )


def _transcript_priority() -> str:
    """
    Returns "scraping_first" or "supadata_first".
    Override via TRANSCRIPT_PRIORITY env:
      - scraping_first
      - supadata_first
    """
    override = (os.getenv("TRANSCRIPT_PRIORITY") or "").strip().lower()
    if override in {"scraping_first", "supadata_first"}:
        return override
    return "supadata_first" if _is_cloud_runtime() else "scraping_first"


# ─── URL Parsing ──────────────────────────────────────────────────────────────

def extract_video_id(url_or_id: str) -> str:
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
        return url_or_id
    patterns = [
        r'[?&]v=([a-zA-Z0-9_-]{11})',
        r'youtu\.be/([a-zA-Z0-9_-]{11})',
        r'embed/([a-zA-Z0-9_-]{11})',
        r'/shorts/([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return url_or_id.strip()


# ─── Timestamp Helpers ────────────────────────────────────────────────────────

def _format_transcript_with_timestamps(segments: list) -> tuple[str, float]:
    """
    Builds a transcript string from raw segments with [MM:SS] markers
    injected every ~30 seconds. Used when scraping succeeds directly.
    """
    if not segments:
        return "", 0.0

    result = []
    last_marker_time = -31.0

    for seg in segments:
        start = seg.get("start", 0)
        text  = seg.get("text", "").strip()
        if not text:
            continue
        if start - last_marker_time >= 30:
            minutes = int(start // 60)
            seconds = int(start % 60)
            result.append(f"[{minutes:02d}:{seconds:02d}]")
            last_marker_time = start
        result.append(text)

    last_seg = segments[-1]
    duration_minutes = (
        last_seg.get("start", 0) + last_seg.get("duration", 0)
    ) / 60

    return " ".join(result), duration_minutes


def _inject_timestamps_into_plain_text(plain_text: str, segments: list) -> str:
    """
    Injects [MM:SS] markers from scraped segments into a plain-text transcript
    (from Supadata) at approximate word-position ratios.
    Accurate to within ~10-15 seconds — enough for navigation.
    """
    if not segments or not plain_text.strip():
        return plain_text

    total_seg_words = sum(len(s.get("text", "").split()) for s in segments)
    if total_seg_words == 0:
        return plain_text

    markers = []
    running_words = 0
    last_marker_time = -31.0

    for seg in segments:
        start     = seg.get("start", 0)
        seg_words = len(seg.get("text", "").split())
        running_words += seg_words
        fraction = running_words / total_seg_words

        if start - last_marker_time >= 30:
            minutes = int(start // 60)
            seconds = int(start % 60)
            markers.append((fraction, f"[{minutes:02d}:{seconds:02d}]"))
            last_marker_time = start

    if not markers:
        return plain_text

    words       = plain_text.split()
    total_words = len(words)
    result      = []
    marker_idx  = 0

    for i, word in enumerate(words):
        while marker_idx < len(markers):
            frac, marker = markers[marker_idx]
            if i >= int(frac * total_words):
                result.append(marker)
                marker_idx += 1
            else:
                break
        result.append(word)

    return " ".join(result)


# ─── Transcript Fetching — 2-Method Chain ─────────────────────────────────────

def _fetch_via_supadata(video_id: str) -> tuple | None:
    """
    Method 2 — FALLBACK: Supadata API.
    Reliable on cloud when scraping is blocked/rate-limited.
    Returns (plain_text, duration_minutes) or None on failure.
    """
    api_key = get_supadata_api_key()
    if not api_key:
        return None

    try:
        resp = requests.get(
            "https://api.supadata.ai/v1/youtube/transcript",
            params={"videoId": video_id, "text": "true"},
            headers={"x-api-key": api_key},
            timeout=15,
        )

        if resp.status_code == 429:
            print("  ⚠️  Supadata rate limit hit")
            return None
        if resp.status_code != 200:
            print(f"  ⚠️  Supadata returned {resp.status_code}")
            return None

        data    = resp.json()
        content = data.get("content", "")
        if not content:
            return None

        text = (
            content if isinstance(content, str)
            else " ".join(seg.get("text", "") for seg in content)
        )
        if not text.strip():
            return None

        duration_minutes = len(text.split()) / 130
        print("  ✅ Transcript via Supadata")
        return text, duration_minutes

    except Exception as e:
        print(f"  ⚠️  Supadata error: {e}")
        return None


def _fetch_via_scraping(video_id: str) -> tuple | None:
    """
    Method 1 — PRIMARY: youtube-transcript-api (scraping).
    Gets per-segment timestamps so we return a timestamped transcript.
    Returns (timestamped_text, duration_minutes) or None on failure.
    """
    try:
        data = YouTubeTranscriptApi().fetch(video_id).to_raw_data()
        if not data:
            return None

        text, duration = _format_transcript_with_timestamps(data)
        if not text.strip():
            return None

        print("  ✅ Transcript via scraping (with timestamps)")
        return text, duration

    except Exception as e:
        print(f"  ⚠️  Scraping error: {e}")
        return None


# ─── Main Transcript Function ─────────────────────────────────────────────────

def get_youtube_transcript(video_id: str, allow_supadata: bool = True) -> tuple[str, float]:
    """
    Fetch transcript using environment-aware priority:
      Local/dev  -> scraping_first
      Cloud/prod -> supadata_first
    Can be overridden using TRANSCRIPT_PRIORITY env var.

    Raises Exception with clear message if both methods fail.
    """
    print(f"  🎬 Fetching transcript for: {video_id}")

    strategy = _transcript_priority()
    print(f"  ⚙️  Transcript strategy: {strategy}")

    def _return_supadata_with_optional_timestamps() -> tuple[str, float] | None:
        if not allow_supadata:
            return None
        supadata_result = _fetch_via_supadata(video_id)
        if not supadata_result:
            return None
        plain_text, duration = supadata_result
        try:
            raw_segments = YouTubeTranscriptApi().fetch(video_id).to_raw_data()
            if raw_segments:
                enriched = _inject_timestamps_into_plain_text(plain_text, raw_segments)
                has_ts = "[" in enriched and ":" in enriched
                label = "Supadata + timestamps" if has_ts else "Supadata (no timestamps)"
                print(f"  📝 {len(enriched.split()):,} words | ~{duration:.1f} min | ✅ {label}")
                return enriched, duration
        except Exception:
            pass
        print(f"  📝 {len(plain_text.split()):,} words | ~{duration:.1f} min | Supadata (no timestamps)")
        return plain_text, duration

    if strategy == "supadata_first" and allow_supadata:
        primary = _return_supadata_with_optional_timestamps()
        if primary:
            return primary
        print("  🔄 Supadata unavailable — trying scraping fallback...")
        scrape_result = _fetch_via_scraping(video_id)
        if scrape_result:
            text, duration = scrape_result
            print(f"  📝 {len(text.split()):,} words | ~{duration:.1f} min | ✅ scraping fallback")
            return text, duration
    else:
        scrape_result = _fetch_via_scraping(video_id)
        if scrape_result:
            text, duration = scrape_result
            print(f"  📝 {len(text.split()):,} words | ~{duration:.1f} min | ✅ scraping primary")
            return text, duration
        print("  🔄 Scraping unavailable — trying Supadata fallback...")
        fallback = _return_supadata_with_optional_timestamps()
        if fallback:
            return fallback

    error_reasons = [
        "Could not fetch transcript for this video.",
        "",
        "Possible reasons:",
        "• Video has no captions enabled",
        "• Video is private or age-restricted",
        "• YouTube transcript endpoint blocked for this request",
    ]
    if allow_supadata:
        error_reasons.append("• Supadata fallback unavailable/quota exceeded")
    error_reasons.append("• Video is too new (captions not yet generated)")

    raise Exception("\n".join(error_reasons))


def get_transcript_source_info() -> str:
    """Returns which sources are configured — shown in the YouTube Mode UI."""
    strategy = _transcript_priority()
    if strategy == "supadata_first":
        first = "Supadata (primary)"
        second = "youtube-transcript-api (fallback)"
    else:
        first = "youtube-transcript-api (primary)"
        second = "Supadata (fallback)"
    if "Supadata" in first or "Supadata" in second:
        if not get_supadata_api_key():
            second = "Supadata (fallback unavailable)"
            if first.startswith("Supadata"):
                first = "youtube-transcript-api (primary)"
    parts = [first, second]
    return " → ".join(parts)


# ─── CLI ──────────────────────────────────────────────────────────────────────

def print_youtube_results(insights, processing_time, duration_minutes):
    print("\n" + "═" * 65)
    print("  🎬  YOUTUBE MODE — RESULTS")
    print("═" * 65)
    print(f"  📌 Title     : {insights.title}")
    print(f"  ⚡ Processed : {processing_time:.1f}s for ~{duration_minutes:.0f}min of video")
    print("─" * 65)

    if hasattr(insights, 'core_concept'):
        print(f"  📐 Core Concept: {insights.core_concept}")
        print(f"  📋 Formulas    : {len(insights.formula_sheet)}")
        print(f"  ⚡ Key Facts   : {len(insights.key_facts)}")
        print(f"  🧪 Self-Test   : {len(insights.self_test)} questions")
    elif hasattr(insights, 'watch_or_skip'):
        print(f"  📺 Verdict     : {insights.watch_or_skip}")
        print(f"  🛠️  Tools       : {', '.join(insights.tools_mentioned[:5])}")
        print(f"  💡 Key Points  : {len(insights.key_points)}")
    else:
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

    insights  = extract_video_insights(transcript, mode=mode, duration_minutes=duration)
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
