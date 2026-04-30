#!/bin/bash
# AVA 3.0 — Start Script for Mac/Linux
# Run once: chmod +x START_AVA_MAC_LINUX.sh
# Then: ./START_AVA_MAC_LINUX.sh

DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "================================================"
echo "  A V A  3.0  —  NEURAL CORE STARTING..."
echo "================================================"
echo ""

# Install dependencies
echo "  Installing dependencies..."
pip3 install fastapi uvicorn psutil selenium webdriver-manager pyautogui --quiet 2>/dev/null

# Start backend in background
echo "  Starting AVA backend on port 8000..."
nohup python3 "$DIR/backend/ava_server.py" > "$DIR/ava.log" 2>&1 &
AVA_PID=$!
echo "  Backend PID: $AVA_PID"

# Save PID for later stopping
echo $AVA_PID > "$DIR/ava.pid"

# Wait then open browser
sleep 2
if [[ "$OSTYPE" == "darwin"* ]]; then
  open -a "Google Chrome" "http://localhost:8000" 2>/dev/null || open "http://localhost:8000"
else
  google-chrome "http://localhost:8000" 2>/dev/null || xdg-open "http://localhost:8000"
fi

echo "  AVA is ONLINE at http://localhost:8000"
echo "  Run ./STOP_AVA.sh to shut down."
echo ""
