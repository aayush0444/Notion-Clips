import re
import time
from youtube_transcript_api import YouTubeTranscriptApi
from gemini import extract_video_insights, extract_tasks, deduplicate_tasks, calculate_accuracy
from push_to_notion import push_youtube
from models import ActionItemList


def extract_video_id(url_or_id: str) -> str:
    """
    Accepts any YouTube URL format or a raw video ID and returns just the ID.
    Examples:
      https://www.youtube.com/watch?v=abc123  → abc123
      https://youtu.be/abc123               → abc123
      abc123                                 → abc123
    """
    # Already a plain ID (no slashes or dots)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
        return url_or_id

    # Try to extract from URL
    patterns = [
        r'[?&]v=([a-zA-Z0-9_-]{11})',   # youtube.com/watch?v=ID
        r'youtu\.be/([a-zA-Z0-9_-]{11})', # youtu.be/ID
        r'embed/([a-zA-Z0-9_-]{11})',     # youtube.com/embed/ID
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)

    # Give up and return as-is (API will throw a clear error if wrong)
    return url_or_id.strip()


def get_youtube_transcript(video_id: str) -> tuple[str, float]:
    """Fetch YouTube transcript. Returns (text, duration_in_minutes)."""
    print(f"  🎬 Fetching transcript for: {video_id}")

    data = YouTubeTranscriptApi().fetch(video_id).to_raw_data()
    text = " ".join([s["text"] for s in data])

    # Estimate duration from last caption's timestamp
    if data:
        last_segment = data[-1]
        duration_minutes = (last_segment["start"] + last_segment.get("duration", 0)) / 60
    else:
        duration_minutes = 0.0

    word_count = len(text.split())
    print(f"  📝 {word_count:,} words | ~{duration_minutes:.1f} min video")
    return text, duration_minutes


def print_youtube_results(insights, processing_time, duration_minutes):
    """Clean terminal output for YouTube mode."""
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
    print("─" * 65)

    url_input  = input("  Paste YouTube URL or video ID: ").strip()
    video_id   = extract_video_id(url_input)

    # Ask what they want out of the video
    print("\n  What do you want to extract?")
    print("  [1] Key insights + takeaways (good for talks, tutorials, lectures)")
    print("  [2] Action items + tasks (good for team meetings recorded on YouTube)")
    print("  [3] Both")

    extract_choice = input("\n  Enter choice (1/2/3): ").strip()

    try:
        transcript, duration = get_youtube_transcript(video_id)
    except Exception as e:
        print(f"\n  ❌ Could not fetch transcript: {e}")
        print("  Make sure the video has captions enabled.")
        return

    start_time = time.time()
    print("\n🤖 Running Gemini AI extraction...")

    insights   = None
    task_list  = None

    if extract_choice in ("1", "3"):
        insights = extract_video_insights(transcript)

    if extract_choice in ("2", "3"):
        raw_tasks  = extract_tasks(transcript)
        task_list  = deduplicate_tasks(raw_tasks)

    # If only tasks were requested, create a fake insights obj for Notion title
    if extract_choice == "2" and task_list:
        from models import VideoInsights
        insights = VideoInsights(
            title=f"Video {video_id}",
            summary="Task extraction mode — see tasks database.",
            key_takeaways=[],
            topics_covered=[],
            action_items=[]
        )

    processing_time = time.time() - start_time

    # Print results
    if insights and extract_choice != "2":
        print_youtube_results(insights, processing_time, duration)

    if task_list:
        accuracy = calculate_accuracy(task_list)
        print(f"\n  📝 {len(task_list.items)} tasks extracted | Accuracy: {accuracy}%")
        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        sorted_tasks = sorted(task_list.items, key=lambda x: priority_order.get(x.priority, 1))
        for i, item in enumerate(sorted_tasks, 1):
            print(f"    {i}. [{item.priority}] {item.assignee} — {item.task[:50]}")

    # Ask before pushing
    push = input("\n  Push to Notion? (y/n): ").strip().lower()
    if push == "y":
        push_youtube(insights, url_input, task_list)
    else:
        print("  Skipped Notion push.")