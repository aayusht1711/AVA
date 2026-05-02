@echo off
title AVA 5.0 — Superior Edition
color 0B
cls
echo.
echo  ====================================================
echo    A V A  5.0  —  SUPERIOR EDITION  LAUNCHING...
echo  ====================================================
echo.
echo  [1/3] Checking Python...
python --version 2>nul || (echo Python not found! Install from python.org && pause && exit)

echo  [2/3] Installing dependencies...
pip install pyttsx3 SpeechRecognition selenium webdriver-manager psutil httpx ^
  elevenlabs pvporcupine pyaudio tavily-python pyautogui --quiet --upgrade

echo  [3/3] Launching AVA desktop app...
echo.
cd "%~dp0app"
python main.py
pause
