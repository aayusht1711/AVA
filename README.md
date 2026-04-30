# ◈ AVA — Advanced Virtual Assistant
### Iron Man JARVIS-level AI for your Laptop & Phone

---

## WHAT AVA CAN DO

| Capability | How |
|---|---|
| 🧠 **AI Brain** | Powered by Claude — answers anything, builds projects, writes code |
| 🎙 **Wake Word** | Say "AVA [command]" — she activates and responds |
| 🔊 **Voice Reply** | Speaks back using your device's best available voice |
| 💻 **Open Apps** | "AVA open VS Code" → launches it on your machine |
| 🌐 **Open Websites** | "AVA open YouTube" → opens in browser |
| 🔍 **Web Search** | "AVA search for Python tutorials" → searches Google |
| 📊 **System Stats** | Live CPU, RAM, Disk, Battery monitoring |
| 📸 **Screenshot** | "AVA take a screenshot" → saves to your desktop |
| ⚡ **Volume Control** | "AVA volume up/down/mute" |

---

## QUICK START (5 MINUTES)

### Step 1 — Get your API Key
1. Go to https://console.anthropic.com
2. Sign up / log in
3. Go to **API Keys** → **Create Key**
4. Copy your key (starts with `sk-ant-...`)

### Step 2 — Open the UI
Simply open `frontend/index.html` in **Chrome** or **Edge**  
(Firefox works but voice synthesis is better in Chrome)

Enter your API key when prompted → **AVA is ready!**

### Step 3 — Enable System Control (Optional but POWERFUL)
This lets AVA actually open apps, take screenshots, control volume.

```bash
# Install Python dependencies
cd backend
pip install -r requirements.txt

# Start the backend server
python server.py
```

Leave this terminal running. AVA will auto-detect it.

---

## VOICE COMMANDS

AVA listens for her name, then executes your command:

```
"AVA open VS Code"
"AVA take a screenshot"  
"AVA open YouTube"
"AVA search for machine learning tutorials"
"AVA volume up"
"AVA mute"
"AVA open terminal"
"AVA open GitHub"
```

AI Commands (she actually does these):
```
"AVA make me a Python web scraper"
"AVA explain how neural networks work"
"AVA write me a REST API in FastAPI"
"AVA what are the latest trends in AI"
"AVA help me build a todo app in React"
"AVA debug this code: [paste your code]"
"AVA give me 10 startup ideas for 2025"
```

---

## RUNNING ON YOUR PHONE

AVA's frontend works on mobile too!

**Option 1 — Local Network:**
1. Run the backend on your laptop: `python backend/server.py`
2. Open `frontend/index.html` — note your laptop's IP (e.g. 192.168.1.5)
3. On your phone browser: go to `http://192.168.1.5:8000` (if you serve it)

**Option 2 — GitHub Pages (easiest):**
1. Create a free GitHub account
2. Create a new repo, upload `frontend/index.html`  
3. Enable GitHub Pages in Settings
4. Access from any device via the URL

**Option 3 — Netlify (instant):**
1. Go to netlify.com → drag & drop the `frontend/` folder
2. Get a URL like `ava-yourname.netlify.app`
3. Open on any phone, tablet, or computer worldwide

---

## ALWAYS-ON (RUNS AT STARTUP)

### Windows — Auto-start Backend:
1. Press `Win + R` → type `shell:startup`
2. Create a file `start_ava.bat`:
```batch
@echo off
cd C:\path\to\AVA\backend
python server.py
```
3. Shortcut this file into the Startup folder

### Mac — Auto-start Backend:
Create `~/Library/LaunchAgents/com.ava.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "...">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.ava.backend</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>/path/to/AVA/backend/server.py</string>
  </array>
  <key>RunAtLoad</key><true/>
</dict>
</plist>
```
Then: `launchctl load ~/Library/LaunchAgents/com.ava.plist`

### Linux — Systemd Service:
Create `/etc/systemd/system/ava.service`:
```ini
[Unit]
Description=AVA Backend

[Service]
ExecStart=/usr/bin/python3 /path/to/AVA/backend/server.py
Restart=always

[Install]
WantedBy=multi-user.target
```
Then: `sudo systemctl enable ava && sudo systemctl start ava`

---

## UPGRADE: REAL WAKE WORD (No button press needed!)

For true always-listening like JARVIS, add Picovoice:

```bash
pip install pvporcupine pyaudio
```

Add this to `backend/server.py`:
```python
import pvporcupine
import pyaudio
import struct

# Create a custom "AVA" wake word at console.picovoice.ai (free)
porcupine = pvporcupine.create(keywords=["jarvis"])  # or custom "ava"
pa = pyaudio.PyAudio()
stream = pa.open(rate=porcupine.sample_rate, channels=1,
                  format=pyaudio.paInt16, input=True,
                  frames_per_buffer=porcupine.frame_length)

while True:
    pcm = stream.read(porcupine.frame_length)
    pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
    if porcupine.process(pcm) >= 0:
        print("Wake word detected!")
        # Trigger recording + send to AVA
```

---

## UPGRADE: REAL AVA VOICE (ElevenLabs)

For a custom, cinematic AI voice instead of browser TTS:

```bash
pip install elevenlabs
```

In `backend/server.py`, add:
```python
from elevenlabs import generate, play
from elevenlabs import set_api_key

set_api_key("YOUR_ELEVENLABS_KEY")  # elevenlabs.io — free tier available

@app.post("/speak")
async def speak_text(payload: dict):
    text = payload.get("text","")
    audio = generate(text=text, voice="Rachel", model="eleven_monolingual_v1")
    play(audio)
    return {"success": True}
```

Then in the frontend, call `/speak` instead of browser TTS.

---

## FILE STRUCTURE

```
AVA/
├── frontend/
│   └── index.html          ← Open this in your browser
├── backend/
│   ├── server.py           ← Python backend (optional)
│   └── requirements.txt    ← pip install -r requirements.txt
└── README.md               ← This file
```

---

## TROUBLESHOOTING

**Voice not working?**  
→ Use Chrome or Edge. Firefox has limited TTS.

**Backend not connecting?**  
→ Make sure `python server.py` is running, and look for "SYSTEM ONLINE" in the UI's backend status dot (turns green).

**"Neural link disrupted" error?**  
→ Check your API key. Get one at console.anthropic.com.

**App not launching?**  
→ Make sure the app is installed. VS Code: `code` must be in PATH. On Mac/Linux run `which code` to check.

---

Made with ◈ — AVA is always watching, always ready.
