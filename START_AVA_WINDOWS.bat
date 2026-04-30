@echo off
title AVA 3.0 — Always Online
color 0B
echo.
echo  ================================================
echo    A V A  3.0  —  NEURAL CORE STARTING...
echo  ================================================
echo.

:: Install dependencies if needed
echo  Installing dependencies...
pip install fastapi uvicorn psutil selenium webdriver-manager pyautogui --quiet

echo  Starting AVA backend...
start /min python "%~dp0backend\ava_server.py"

:: Wait 2 seconds then open the UI
timeout /t 2 /nobreak >nul
start chrome "http://localhost:8000"

echo  AVA is ONLINE. Browser opened.
echo  Keep this window running for 24/7 operation.
echo.
pause
