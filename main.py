from dotenv import load_dotenv
from meeting_mode import run_meeting_mode
from youtube_mode import run_youtube_mode

load_dotenv()


def print_banner():
    print("\n" + "═" * 65)
    print("   🧠  SMART MEETING TRANSCRIBER")
    print("   Powered by Whisper + Google Gemini + Notion API")
    print("═" * 65)
    print()
    print("   Choose a mode:")
    print()
    print("   [1] 🎙️  MEETING MODE")
    print("       Record or upload meeting audio → Whisper transcribes")
    print("       → Gemini extracts tasks + summary → Notion")
    print()
    print("   [2] 🎬  YOUTUBE MODE")
    print("       Paste any YouTube URL → Get key insights + tasks")
    print("       → Everything saved to your Notion workspace")
    print()
    print("   [q]  Quit")
    print("─" * 65)


if __name__ == "__main__":
    while True:
        print_banner()
        mode = input("   Enter mode (1/2/q): ").strip().lower()

        if mode == "1":
            run_meeting_mode()

        elif mode == "2":
            run_youtube_mode()

        elif mode in ("q", "quit", "exit"):
            print("\n  👋 Bye!\n")
            break

        else:
            print("\n  ❌ Invalid choice. Enter 1, 2, or q.")

        # After each run, ask if they want to go again
        again = input("\n  Run another? (y/n): ").strip().lower()
        if again != "y":
            print("\n  👋 Bye!\n")
            break