# ◈ AVA 5.0 — Superior Edition
### Native Desktop App · Learning AI · Human-Like Female Voice · No Browser Needed

---

## ✦ WHAT'S NEW IN 5.0

| Feature | Details |
|---|---|
| 🖥 **Native Desktop App** | Real window on your desktop — no Chrome, no browser |
| 🧠 **Learning AI** | Builds a personality model from YOUR conversations |
| 👤 **Human-Like Speech** | Talks like a real person — adapts to your style (casual/technical/formal) |
| 🎭 **Mood Detection** | Detects if you're happy, stressed, excited — responds accordingly |
| 🗣 **Female Voice** | pyttsx3 female voice + ElevenLabs for cinematic quality |
| 📚 **Style Adaptation** | Learns if you prefer short/long answers, casual/formal tone, emoji or not |
| 🧬 **Persistent Learning** | Learning model saved to disk — grows smarter every session |

---

## ⚡ INSTANT START

### Windows
```
Double-click: START_WINDOWS.bat
```

### Mac / Linux
```bash
chmod +x START_MAC_LINUX.sh
./START_MAC_LINUX.sh
```

---

## 🔑 API KEYS (all free)

| Key | Required? | Get it at |
|---|---|---|
| **Groq** | ✅ Yes | console.groq.com |
| **ElevenLabs** | Optional | elevenlabs.io (10k chars/month free) |
| **Tavily** | Optional | tavily.com (1000 searches/month free) |
| **Picovoice** | Optional | picovoice.ai (always-on wake word) |

Add keys in the app → **⚙ Settings**

---

## 🧠 HOW THE LEARNING WORKS

AVA builds a model of YOU from every conversation:

- **Vocabulary tracking** — learns words you use most
- **Style detection** — casual / technical / formal
- **Length preference** — short answers or detailed explanations
- **Mood awareness** — detects positive/negative mood from your words
- **Interest mapping** — learns your topics from frequency analysis
- **Correction learning** — when you say "that's wrong", she remembers to be more careful
- **Project memory** — remembers what you're building, working on
- **Personal facts** — your name, preferences, habits

After 20+ messages AVA starts feeling noticeably personalised.
After 100+ messages she feels like she's known you for months.

---

## 🎙 VOICE COMMANDS

```
"AVA play [any song]"         → plays on YouTube, no touch
"AVA pause"                   → pauses
"AVA next song"               → skips
"AVA volume up / down"        → adjusts
"AVA open VS Code"            → launches app
"AVA take a screenshot"       → saves to desktop
"AVA search [anything]"       → live web search
"AVA build me a [project]"    → full code output
"AVA what do you remember"    → shows your memory
"AVA what's my style"         → shows learned communication style
```

---

## 🔁 AUTO-START AT LOGIN

### Windows Task Scheduler
1. Win+S → "Task Scheduler"
2. Action → Create Basic Task
3. Trigger: At log on
4. Action: Start a program → `START_WINDOWS.bat`

### Mac Login Items
1. System Settings → General → Login Items
2. Add `START_MAC_LINUX.sh`

### Linux Autostart
```bash
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/ava5.desktop << EOF
[Desktop Entry]
Type=Application
Name=AVA 5.0
Exec=/path/to/AVA5/START_MAC_LINUX.sh
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF
```

---

## 📁 FILE STRUCTURE

```
AVA5/
├── app/
│   ├── main.py              ← Desktop app (run this)
│   └── data/                ← Auto-created
│       ├── config.json      ← API keys
│       ├── memory.json      ← Long-term memory
│       ├── history.json     ← Conversation history
│       └── learning.json    ← Learning model
├── requirements.txt
├── START_WINDOWS.bat
├── START_MAC_LINUX.sh
└── README.md
```

---

## ❓ TROUBLESHOOTING

**"pyttsx3 no female voice found"**
→ Windows: install additional TTS voices in Settings → Time & Language → Speech
→ Mac: System Settings → Accessibility → Spoken Content → add Samantha voice
→ Linux: `sudo apt install espeak-ng`

**Microphone not working**
→ Allow microphone permission on first run
→ `pip install SpeechRecognition pyaudio`
→ Mac: `brew install portaudio && pip install pyaudio`
→ Linux: `sudo apt install portaudio19-dev python3-pyaudio`

**Wake word needs Picovoice key**
→ Free at picovoice.ai → Console → AccessKey

**YouTube not auto-playing**
→ `pip install selenium webdriver-manager`
→ Google Chrome must be installed

---

◈ AVA 5.0 — Always learning. Always improving. Always yours.
