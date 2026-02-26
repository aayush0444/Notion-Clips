#!/bin/bash
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   🧠 Meeting Transcriber — Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Install from python.org"
    exit 1
fi
echo "✅ Python found: $(python3 --version)"

# Check ffmpeg (required for Whisper)
if ! command -v ffmpeg &> /dev/null; then
    echo ""
    echo "⚠️  ffmpeg not found (needed for audio transcription)"
    echo "   Mac:   brew install ffmpeg"
    echo "   Linux: sudo apt install ffmpeg"
    echo ""
fi

# Install Python packages
echo ""
echo "📦 Installing Python packages..."
pip3 install -r requirements.txt

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Setup complete!"
echo ""
echo "Next: run ./run.sh to launch the app"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""