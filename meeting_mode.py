import os
import time
from transcriber import record_audio, transcribe_audio
from gemini import extract_tasks, extract_meeting_summary, deduplicate_tasks, calculate_accuracy
from push_to_notion import push_meeting


def print_meeting_results(summary, tasks, accuracy, processing_time, duration_minutes):
    """Clean terminal output for meeting mode."""
    print("\n" + "═" * 65)
    print("  📋  MEETING MODE — RESULTS")
    print("═" * 65)
    print(f"  📌 Title     : {summary.title}")
    print(f"  🎯 Accuracy  : {accuracy}%")
    print(f"  ⚡ Processed : {processing_time:.1f}s for ~{duration_minutes:.0f}min of audio")
    print(f"  📝 Tasks     : {len(tasks.items)} unique action items")
    print("─" * 65)
    print(f"  💡 {summary.summary[:130]}")
    print("─" * 65)
    print(f"  Key Decisions:")
    for d in summary.key_decisions:
        print(f"    • {d}")
    print("─" * 65)

    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    sorted_tasks = sorted(tasks.items, key=lambda x: priority_order.get(x.priority, 1))

    print(f"  {'#':<3} {'PRIORITY':<8} {'ASSIGNEE':<15} {'DUE DATE':<12} TASK")
    print("─" * 65)
    for i, item in enumerate(sorted_tasks, 1):
        due = item.due_date if item.due_date != "TBD" else "TBD"
        print(f"  {i:<3} {item.priority:<8} {item.assignee[:14]:<15} {due:<12} {item.task[:38]}")
    print("═" * 65)


def run_meeting_mode():
    print("\n" + "─" * 65)
    print("  🎙️   MEETING MODE")
    print("─" * 65)
    print("  How do you want to provide the audio?")
    print("  [1] Record now (live microphone)")
    print("  [2] Use an existing audio file (.wav / .mp3 / .m4a)")
    print("  [3] Paste transcript text directly")

    choice = input("\n  Enter choice (1/2/3): ").strip()

    audio_path  = None
    transcript  = None
    duration    = 0.0

    if choice == "1":
        # Live recording
        try:
            minutes = int(input("  Max recording duration in minutes (default 5): ").strip() or "5")
        except ValueError:
            minutes = 5
        audio_path = record_audio(duration_seconds=minutes * 60)
        transcript, duration = transcribe_audio(audio_path)

    elif choice == "2":
        # Existing file
        file_path = input("  Enter full path to audio file: ").strip().strip('"')
        if not os.path.exists(file_path):
            print(f"  ❌ File not found: {file_path}")
            return
        transcript, duration = transcribe_audio(file_path)

    elif choice == "3":
        # Direct text paste
        print("  Paste the transcript text below.")
        print("  When done, type END on a new line and press Enter:\n")
        lines = []
        while True:
            line = input()
            if line.strip().upper() == "END":
                break
            lines.append(line)
        transcript = " ".join(lines)
        duration   = len(transcript.split()) / 130  # rough estimate: ~130 words/min

    else:
        print("  ❌ Invalid choice")
        return

    if not transcript or len(transcript.strip()) < 50:
        print("  ❌ Transcript is too short or empty. Nothing to process.")
        return

    start_time = time.time()

    print("\n🤖 Running Gemini AI extraction...")
    raw_tasks = extract_tasks(transcript)
    summary   = extract_meeting_summary(transcript)

    clean_tasks      = deduplicate_tasks(raw_tasks)
    accuracy         = calculate_accuracy(clean_tasks)
    processing_time  = time.time() - start_time

    print_meeting_results(summary, clean_tasks, accuracy, processing_time, duration)

    # Ask before pushing
    push = input("\n  Push to Notion? (y/n): ").strip().lower()
    if push == "y":
        push_meeting(clean_tasks, summary)
    else:
        print("  Skipped Notion push.")