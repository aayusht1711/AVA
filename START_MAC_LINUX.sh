#!/bin/bash
# AVA 5.0 — Mac/Linux Desktop Launcher
DIR="$(cd "$(dirname "$0")" && pwd)"
echo ""
echo "======================================================"
echo "  A V A  5.0  —  SUPERIOR EDITION  LAUNCHING..."
echo "======================================================"
echo ""
echo "  [1/3] Installing dependencies..."
pip3 install pyttsx3 SpeechRecognition selenium webdriver-manager psutil httpx \
  elevenlabs pvporcupine pyaudio tavily-python pyautogui --quiet --upgrade 2>/dev/null
# Mac: need portaudio for pyaudio
if [[ "$OSTYPE" == "darwin"* ]]; then
  which brew &>/dev/null && brew install portaudio 2>/dev/null || true
fi
echo "  [2/3] Launching AVA desktop app..."
cd "$DIR/app"
python3 main.py
