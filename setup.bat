@echo off
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo    🧠 Meeting Transcriber — Setup
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Install from python.org
    pause
    exit /b
)

echo 📦 Installing Python packages...
pip install -r requirements.txt

echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo ✅ Setup complete! Run run.bat to launch.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
pause