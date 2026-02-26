import os
import wave
import tempfile
import whisper
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write as write_wav


# Load Whisper model once (using 'base' — fast and good enough for meetings)
# Options: tiny, base, small, medium, large  (larger = more accurate but slower)
WHISPER_MODEL = "base"

def load_whisper():
    print("  🔄 Loading Whisper model (first run downloads it ~150MB)...")
    model = whisper.load_model(WHISPER_MODEL)
    print("  ✅ Whisper ready")
    return model


def record_audio(duration_seconds: int = 300) -> str:
    """
    Records audio from the microphone.
    Default max: 5 minutes. User can press Ctrl+C to stop early.
    Returns path to the saved .wav file.
    """
    SAMPLE_RATE = 16000  # Whisper works best at 16kHz
    CHANNELS    = 1      # Mono is fine for speech

    print(f"\n🎙️  Recording started (max {duration_seconds // 60} min)")
    print("    Press Ctrl+C to stop recording early\n")

    frames = []

    try:
        # Stream audio in chunks so we can stop with Ctrl+C
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="int16") as stream:
            for _ in range(0, int(SAMPLE_RATE * duration_seconds / 1024)):
                chunk, _ = stream.read(1024)
                frames.append(chunk)

    except KeyboardInterrupt:
        print("\n  ⏹️  Recording stopped by user")

    # Combine all chunks into one array
    audio_data = np.concatenate(frames, axis=0)

    # Save to a temp .wav file
    temp_path = tempfile.mktemp(suffix=".wav")
    write_wav(temp_path, SAMPLE_RATE, audio_data)

    duration_recorded = len(audio_data) / SAMPLE_RATE
    print(f"  💾 Saved {duration_recorded:.1f}s of audio")
    return temp_path


def transcribe_audio(audio_path: str) -> tuple[str, float]:
    """
    Transcribes an audio file using Whisper.
    Works with .wav, .mp3, .m4a, .mp4, etc.
    Returns (transcript_text, duration_in_minutes).
    """
    print(f"  🔊 Transcribing: {os.path.basename(audio_path)}")

    model = load_whisper()
    result = model.transcribe(audio_path, language="en", verbose=False)

    text = result["text"].strip()
    duration_minutes = result.get("segments", [{}])[-1].get("end", 0) / 60 if result.get("segments") else 0.0

    word_count = len(text.split())
    print(f"  📝 Transcribed: {word_count:,} words | ~{duration_minutes:.1f} min audio")

    return text, duration_minutes