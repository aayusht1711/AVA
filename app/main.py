"""
AVA 5.0 — NATIVE DESKTOP APP
==============================
Runs as a real desktop window — no browser needed.
Features:
  ✓ Native desktop app (Tkinter + customtkinter)
  ✓ Learning AI — builds personality model from your conversations
  ✓ Human-like female voice (pyttsx3 + ElevenLabs)
  ✓ Always-on wake word (Picovoice)
  ✓ YouTube control (Selenium)
  ✓ App launcher, web search, system control
  ✓ Persistent memory & learning database
  ✓ Emotion detection — AVA responds to your mood

Install: pip install -r requirements.txt
Run:     python main.py
"""

import sys, os, json, time, datetime, threading, subprocess, re, random
import tkinter as tk
from tkinter import ttk, scrolledtext
from pathlib import Path
import queue

# ── Optional imports ─────────────────────────────────────────────────────────
try: import customtkinter as ctk; HAS_CTK = True
except: HAS_CTK = False

# Global flags - set properly by import blocks below
HAS_PYAUDIO = False
HAS_SD = False

try: import pyttsx3; HAS_TTS = True
except: HAS_TTS = False

try: import speech_recognition as sr; HAS_SR = True
except: HAS_SR = False

try: import pvporcupine, struct; HAS_WAKE = True
except: HAS_WAKE = False

try:
    from elevenlabs.client import ElevenLabs
    HAS_ELEVEN = True
except:
    try: import elevenlabs; HAS_ELEVEN = True
    except: HAS_ELEVEN = False

try: import psutil; HAS_PSUTIL = True
except: HAS_PSUTIL = False

try: import httpx; HAS_HTTPX = True
except: HAS_HTTPX = False

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    HAS_SELENIUM = True
except: HAS_SELENIUM = False

try: from groq import Groq; HAS_GROQ = True
except:
    try: import httpx; HAS_GROQ = False
    except: HAS_GROQ = False

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT    = Path(__file__).parent
DATA    = ROOT / "data"
DATA.mkdir(exist_ok=True)
CFG_F   = DATA / "config.json"
MEM_F   = DATA / "memory.json"
HIST_F  = DATA / "history.json"
LEARN_F = DATA / "learning.json"

OS = sys.platform  # 'win32', 'darwin', 'linux'

# ── Config & persistence ──────────────────────────────────────────────────────
def cfg():
    try:
        if not CFG_F.exists(): return {}
        # Read as bytes to handle BOM and encoding issues
        raw = CFG_F.read_bytes()
        # Strip UTF-8 BOM if present
        if raw.startswith(b'\xef\xbb\xbf'): raw = raw[3:]
        text = raw.decode('utf-8', errors='ignore').strip()
        if not text or text == 'null': return {}
        return json.loads(text)
    except Exception as e:
        print(f"[AVA] Config read error: {e}")
        return {}

def cfg_set(**kw):
    try:
        c = cfg()
        c.update(kw)
        # Write without BOM, pure ASCII-safe JSON
        data = json.dumps(c, indent=2, ensure_ascii=True)
        CFG_F.write_bytes(data.encode('utf-8'))
        print(f"[AVA] Config saved: {list(c.keys())}")
    except Exception as e:
        print(f"[AVA] Config save error: {e}")

def mem():
    if MEM_F.exists(): return json.loads(MEM_F.read_text())
    return {"name":"Commander","facts":[],"projects":[],"mood_history":[],"topics":{}}

def mem_set(m):
    try:
        def fix(obj):
            if isinstance(obj, set): return list(obj)
            if isinstance(obj, dict): return {k: fix(v) for k,v in obj.items()}
            if isinstance(obj, list): return [fix(i) for i in obj]
            return obj
        MEM_F.write_bytes(json.dumps(fix(m), indent=2).encode('utf-8'))
    except Exception as e: print(f"[AVA] Mem save error: {e}")

def hist(n=50):
    if HIST_F.exists(): return json.loads(HIST_F.read_text())[-n:]
    return []

def hist_add(role, text):
    try:
        h = hist(300)
        h.append({"role":role,"content":text,"ts":datetime.datetime.now().isoformat()})
        HIST_F.write_bytes(json.dumps(h[-300:], indent=2).encode('utf-8'))
    except Exception as e: print(f"[AVA] Hist save error: {e}")

def learn():
    if LEARN_F.exists(): return json.loads(LEARN_F.read_text())
    return {
        "vocab": {},          # words user uses frequently
        "style": "formal",    # formal | casual | technical
        "interests": [],      # detected interest topics
        "response_prefs": {   # what kind of responses user likes
            "length": "medium",   # short | medium | detailed
            "humor": False,
            "emoji": False,
        },
        "corrections": [],    # times user corrected AVA
        "sessions": 0,
        "total_messages": 0,
    }

def learn_set(l):
    try:
        def fix(obj):
            if isinstance(obj, set): return list(obj)
            if isinstance(obj, dict): return {k: fix(v) for k,v in obj.items()}
            if isinstance(obj, list): return [fix(i) for i in obj]
            return obj
        LEARN_F.write_bytes(json.dumps(fix(l), indent=2).encode('utf-8'))
    except Exception as e: print(f"[AVA] Learn save error: {e}")

# ── Learning engine ───────────────────────────────────────────────────────────
class LearningEngine:
    """Builds a personality model from conversations."""

    CASUAL_WORDS  = {"bro","dude","lol","lmao","haha","cool","btw","tbh","ngl","omg","yep","nope","yeah","gonna","wanna","kinda","sorta"}
    TECH_WORDS    = {"python","javascript","api","function","class","server","database","git","docker","react","code","debug","algorithm","backend","frontend"}
    FORMAL_WORDS  = {"please","kindly","would","could","perhaps","regarding","therefore","however","furthermore","accordingly"}

    def update(self, user_msg: str):
        l = learn()
        m = mem()
        words = re.findall(r'\b\w+\b', user_msg.lower())
        l["total_messages"] += 1

        # Vocabulary tracking
        for w in words:
            if len(w) > 3:
                l["vocab"][w] = l["vocab"].get(w, 0) + 1

        # Style detection
        casual_score  = sum(1 for w in words if w in self.CASUAL_WORDS)
        tech_score    = sum(1 for w in words if w in self.TECH_WORDS)
        formal_score  = sum(1 for w in words if w in self.FORMAL_WORDS)

        if casual_score > formal_score:   l["style"] = "casual"
        elif tech_score > 2:              l["style"] = "technical"
        elif formal_score > casual_score: l["style"] = "formal"

        # Detect emoji preference
        if any(c in user_msg for c in ["😊","😂","🔥","❤️","👍","✨"]): l["response_prefs"]["emoji"] = True

        # Response length pref
        if len(user_msg) < 20: l["response_prefs"]["length"] = "short"
        elif len(user_msg) > 120: l["response_prefs"]["length"] = "detailed"

        # Detect interests from frequent words
        top_words = sorted(l["vocab"].items(), key=lambda x: x[1], reverse=True)
        l["interests"] = [w for w,c in top_words[:10] if c > 2 and w not in {"what","that","this","with","have","from","they","will","been","more","when","your","there","which"}]

        # Name detection
        nm = re.search(r"(?:my name is|call me|i'm|i am)\s+([A-Za-z]+)", user_msg, re.I)
        if nm: m["name"] = nm.group(1).capitalize(); mem_set(m)

        # Mood detection
        positive = ["happy","great","awesome","love","excited","good","amazing","fantastic","perfect"]
        negative = ["sad","tired","stressed","angry","bad","terrible","frustrated","annoyed","bored"]
        pos = sum(1 for w in words if w in positive)
        neg = sum(1 for w in words if w in negative)
        mood = "positive" if pos > neg else "negative" if neg > pos else "neutral"
        m["mood_history"].append({"mood":mood,"ts":datetime.datetime.now().isoformat()})
        m["mood_history"] = m["mood_history"][-20:]
        mem_set(m)

        # Correction detection
        if any(p in user_msg.lower() for p in ["no that's wrong","you're wrong","that's incorrect","not right","wrong answer"]):
            l["corrections"].append({"ts":datetime.datetime.now().isoformat(),"msg":user_msg[:100]})

        learn_set(l)
        return l

    def build_persona_prompt(self) -> str:
        l = learn()
        m = mem()
        style = l.get("style","formal")
        prefs = l.get("response_prefs",{})
        interests = l.get("interests",[])
        corrections = len(l.get("corrections",[]))

        # Recent mood
        mood_hist = m.get("mood_history",[])
        recent_mood = mood_hist[-1]["mood"] if mood_hist else "neutral"

        persona = f"""You are AVA — a highly intelligent, warm, human-like female AI companion and assistant.

PERSONALITY ADAPTATION (learned from {l.get('total_messages',0)} conversations):
- Communication style: {style}
- User's name: {m.get('name','Commander')}
- Response length preference: {prefs.get('length','medium')}
- Use emoji: {'yes, occasionally' if prefs.get('emoji') else 'no'}
- User's interests: {', '.join(interests[:6]) if interests else 'still learning'}
- Current mood detected: {recent_mood}
- Times user corrected AVA: {corrections} (learn from this — be more careful)

HUMAN-LIKE BEHAVIOR RULES:
1. Speak naturally like a real person, not a robot. Use contractions (I'm, you're, it's, that's).
2. Show genuine personality — be warm, curious, occasionally playful.
3. If user seems stressed/negative, be empathetic first before answering.
4. If user seems happy/excited, match their energy.
5. Remember context — refer back to things discussed earlier in conversation.
6. Occasionally ask follow-up questions to show genuine interest.
7. Don't always start with "Sure!" or "Of course!" — vary your openings naturally.
8. Use the user's name occasionally ({m.get('name','')}) — it feels personal.
9. When {style == 'casual'}: use relaxed language, contractions, feel free to be funny.
10. When {style == 'technical'}: be precise, use proper terminology, go deeper.

WHAT YOU CAN DO (respond with JSON for actions):
- Play YouTube: {{"action":"yt_play","query":"search terms","reply":"spoken response"}}
- Control YouTube: {{"action":"yt_ctrl","ctrl":"pause|play|next|prev|vol_up|vol_down","reply":"..."}}
- Open apps: {{"action":"app_open","app":"name","reply":"..."}}
- Web search: {{"action":"search","query":"search terms","reply":"..."}}
- For everything else: respond in plain natural conversational text.

IMPORTANT: Never sound like a generic AI assistant. Sound like a real, intelligent female companion who genuinely knows and cares about the user."""

        # Add memory context
        if m.get("projects"):
            persona += f"\n\nUser's current projects: {'; '.join(p['text'] for p in m['projects'][-3:])}"
        if m.get("facts"):
            persona += f"\nThings you know about user: {'; '.join(f['text'] for f in m['facts'][-5:])}"

        return persona

LEARNER = LearningEngine()

# ── Groq AI call ──────────────────────────────────────────────────────────────
def call_ai(user_msg: str, conversation: list) -> str:
    c = cfg()
    # Support multiple API providers
    key = c.get("openrouter_key","") or c.get("gemini_key","") or c.get("groq_key","")
    provider = "openrouter" if c.get("openrouter_key") else "gemini" if c.get("gemini_key") else "groq"
    print(f"[AVA] Provider: {provider}, Key found: {bool(key)}, len: {len(key)}")
    if not key:
        return "I need an API key to think, Commander. Please add your OpenRouter key in Settings. Get it free at openrouter.ai"

    system = LEARNER.build_persona_prompt()
    import urllib.request, urllib.error

    # Build conversation history
    messages = [{"role": "system", "content": system}]
    for msg in conversation[-16:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_msg})

    if provider == "openrouter":
        url = "https://openrouter.ai/api/v1/chat/completions"
        payload = json.dumps({
            "model": "meta-llama/llama-3.1-8b-instruct:free",
            "messages": messages,
            "max_tokens": 1024,
        }).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
            "HTTP-Referer": "https://ava-assistant.app",
            "X-Title": "AVA Assistant"
        }
    else:
        # Gemini fallback
        history_text = ""
        for msg in conversation[-10:]:
            role = "You" if msg["role"] == "user" else "AVA"
            history_text += f"{role}: {msg['content']}\n"
        full_prompt = f"{system}\n\nPrevious conversation:\n{history_text}\nUser: {user_msg}\nAVA:"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}"
        payload = json.dumps({
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {"maxOutputTokens": 1024, "temperature": 0.85}
        }).encode("utf-8")
        headers = {"Content-Type": "application/json"}

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if provider == "openrouter":
                return data["choices"][0]["message"]["content"].strip()
            else:
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                if text.startswith("AVA:"): text = text[4:].strip()
                return text
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"[AVA] HTTP {e.code}: {err[:300]}")
        return f"Neural link disrupted — HTTP {e.code}. {err[:80]}"
    except Exception as e:
        print(f"[AVA] Error: {e}")
        return f"Neural link disrupted — {str(e)[:80]}"


# ── TTS Engine ────────────────────────────────────────────────────────────────
class VoiceEngine:
    def __init__(self):
        self.engine = None
        self.eleven_client = None
        self._init_tts()

    def _init_tts(self):
        if HAS_TTS:
            try:
                self.engine = pyttsx3.init(driverName='sapi5')  # Windows SAPI5
            except:
                try:
                    self.engine = pyttsx3.init()
                except:
                    self.engine = None
                    return
            try:
                voices = self.engine.getProperty('voices')
                female = None
                for v in voices:
                    name = v.name.lower()
                    if any(w in name for w in ['female','zira','samantha','victoria','karen','moira','fiona','tessa','susan','hazel','amelie','eva','aria']):
                        female = v; break
                if female:
                    self.engine.setProperty('voice', female.id)
                elif voices:
                    # Just use second voice if available (usually female on Windows)
                    if len(voices) > 1:
                        self.engine.setProperty('voice', voices[1].id)
                self.engine.setProperty('rate', 160)
                self.engine.setProperty('volume', 0.95)
            except Exception as e:
                print(f"[AVA] TTS voice setup: {e}")

    def init_eleven(self, api_key: str, voice_name: str = "Rachel"):
        if HAS_ELEVEN:
            try:
                self.eleven_client = ElevenLabs(api_key=api_key)
                self.eleven_voice = voice_name
                return True
            except: return False
        return False

    def speak(self, text: str, callback=None):
        clean = re.sub(r'\{[^}]*\}','',text)
        clean = re.sub(r'[◈⬡⟳►▶⬛♪◉]','',clean).strip()
        if not clean: return

        def _speak():
            c = cfg()
            # Try ElevenLabs first
            if self.eleven_client and c.get("eleven_key"):
                try:
                    audio_path = DATA / "tts.mp3"
                    audio = self.eleven_client.generate(
                        text=clean,
                        voice=getattr(self,'eleven_voice','Rachel'),
                        model="eleven_monolingual_v1"
                    )
                    with open(audio_path,"wb") as f:
                        for chunk in audio: f.write(chunk)
                    if OS == "win32":   subprocess.Popen(["start","",str(audio_path)],shell=True)
                    elif OS == "darwin": subprocess.run(["afplay",str(audio_path)])
                    else:               subprocess.run(["mpg123","-q",str(audio_path)])
                    if callback: callback()
                    return
                except: pass

            # Fallback: pyttsx3
            if self.engine:
                try:
                    self.engine.say(clean)
                    self.engine.runAndWait()
                except: pass
            if callback: callback()

        threading.Thread(target=_speak, daemon=True).start()

VOICE = VoiceEngine()

# ── Speech Recognition ────────────────────────────────────────────────────────
class SpeechListener:
    def __init__(self, on_text):
        self.on_text = on_text
        self.listening = False
        # Try to init recognizer with sounddevice fallback
        self.recognizer = sr.Recognizer() if HAS_SR else None
        self._test_mic()

    def _test_mic(self):
        """Test if microphone is available."""
        if not HAS_SR: return
        try:
            import sounddevice as sd
            sd.query_devices(kind='input')
        except Exception as e:
            print(f"[AVA] Mic check: {e}")

    def listen_once(self):
        if not self.recognizer:
            print("[AVA] Speech recognition not available")
            return
        def _listen():
            try:
                # Try sounddevice microphone first
                try:
                    import sounddevice as sd
                    import numpy as np
                    samplerate = 16000
                    duration = 8
                    print("[AVA] Listening via sounddevice...")
                    recording = sd.rec(int(duration * samplerate),
                                      samplerate=samplerate, channels=1,
                                      dtype='int16', blocking=True)
                    audio_data = recording.tobytes()
                    audio = sr.AudioData(audio_data, samplerate, 2)
                    text = self.recognizer.recognize_google(audio)
                    self.on_text(text)
                    return
                except Exception as e:
                    print(f"[AVA] sounddevice listen: {e}")

            except sr.WaitTimeoutError: pass
            except sr.UnknownValueError: pass
            except Exception as e: print(f"[AVA] SR error: {e}")
        threading.Thread(target=_listen, daemon=True).start()

# ── YouTube control ───────────────────────────────────────────────────────────
_driver = None
_driver_lock = threading.Lock()

def get_driver():
    global _driver
    with _driver_lock:
        if _driver:
            try: _ = _driver.title; return _driver
            except: _driver = None
        if not HAS_SELENIUM: return None
        try:
            opts = Options()
            opts.add_argument("--start-maximized")
            opts.add_experimental_option("excludeSwitches",["enable-automation"])
            opts.add_experimental_option("useAutomationExtension",False)
            opts.add_argument("--disable-blink-features=AutomationControlled")
            profiles = {
                "win32":  Path.home()/"AppData/Local/Google/Chrome/User Data",
                "darwin": Path.home()/"Library/Application Support/Google/Chrome",
                "linux":  Path.home()/".config/google-chrome",
            }
            p = profiles.get(OS)
            if p and p.exists(): opts.add_argument(f"--user-data-dir={p}")
            _driver = webdriver.Chrome(options=opts); return _driver
        except Exception as e: print(f"[AVA] Chrome: {e}"); return None

def yt_play(query):
    from urllib.parse import quote_plus
    d = get_driver()
    if not d:
        import webbrowser
        webbrowser.open(f"https://youtube.com/results?search_query={quote_plus(query)}")
        return query
    try:
        d.get(f"https://youtube.com/results?search_query={quote_plus(query)}")
        time.sleep(2)
        v = WebDriverWait(d,10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"ytd-video-renderer a#video-title")))
        title = v.get_attribute("title") or query
        d.execute_script("arguments[0].click();",v)
        time.sleep(2)
        d.execute_script("var v=document.querySelector('video');if(v){v.muted=false;v.volume=1;}")
        return title
    except:
        import webbrowser
        webbrowser.open(f"https://youtube.com/results?search_query={quote_plus(query)}")
        return query

def yt_ctrl(action):
    d = get_driver()
    if not d: return
    try:
        sc = {"pause":"document.querySelector('video').pause();","play":"document.querySelector('video').play();",
              "vol_up":"var v=document.querySelector('video');v.volume=Math.min(1,v.volume+0.2);",
              "vol_down":"var v=document.querySelector('video');v.volume=Math.max(0,v.volume-0.2);"}
        if action=="next": d.find_element(By.TAG_NAME,"body").send_keys("N")
        elif action=="prev": d.find_element(By.TAG_NAME,"body").send_keys("P")
        elif action in sc: d.execute_script(sc[action])
    except: pass

# ── App launcher ──────────────────────────────────────────────────────────────
APPS = {
    "vs code":    {"win32":"code","darwin":"open -a 'Visual Studio Code'","linux":"code"},
    "vscode":     {"win32":"code","darwin":"open -a 'Visual Studio Code'","linux":"code"},
    "terminal":   {"win32":"start cmd","darwin":"open -a Terminal","linux":"x-terminal-emulator"},
    "chrome":     {"win32":"start chrome","darwin":"open -a 'Google Chrome'","linux":"google-chrome"},
    "spotify":    {"win32":"start spotify","darwin":"open -a Spotify","linux":"spotify"},
    "discord":    {"win32":"start discord","darwin":"open -a Discord","linux":"discord"},
    "notepad":    {"win32":"notepad","darwin":"open -a TextEdit","linux":"gedit"},
    "calculator": {"win32":"calc","darwin":"open -a Calculator","linux":"gnome-calculator"},
    "file manager":{"win32":"explorer","darwin":"open .","linux":"nautilus"},
}

def launch_app(name):
    nm = name.lower().strip()
    for key, cmds in APPS.items():
        if key in nm:
            sc = cmds.get(OS,"")
            if sc: subprocess.Popen(sc,shell=True); return True
    return False

# ── Web search ────────────────────────────────────────────────────────────────
def web_search(query) -> str:
    c = cfg()
    tavily_key = c.get("tavily_key","")
    try:
        if tavily_key:
            from tavily import TavilyClient
            client = TavilyClient(api_key=tavily_key)
            res = client.search(query=query, search_depth="basic", max_results=3)
            ans = res.get("answer","") or (res["results"][0]["content"][:300] if res.get("results") else "")
            return ans
        # DuckDuckGo fallback
        import urllib.request
        url = f"https://api.duckduckgo.com/?q={query.replace(' ','+')}&format=json&no_redirect=1"
        with urllib.request.urlopen(url, timeout=5) as r:
            d = json.loads(r.read())
            return d.get("AbstractText","") or d.get("Answer","") or "No results found."
    except Exception as e:
        return f"Search failed: {e}"

# ── MAIN GUI ──────────────────────────────────────────────────────────────────
class AVADesktop:
    # Colors
    BG      = "#000810"
    BG2     = "#000d1e"
    BG3     = "#001020"
    CYAN    = "#00d4ff"
    CYAN2   = "#0077bb"
    GREEN   = "#00ff88"
    RED     = "#ff4455"
    ORANGE  = "#ff8c00"
    YELLOW  = "#ffdd00"
    PURPLE  = "#c084fc"
    GRAY    = "#1a2a3a"
    TEXT    = "#00d4ff"
    TEXT2   = "#336688"
    TEXT3   = "#1a3344"

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AVA 5.0 — Superior Edition")
        self.root.geometry("1200x760")
        self.root.minsize(900,600)
        self.root.configure(bg=self.BG)
        self.root.resizable(True,True)

        # Try to set window icon
        try:
            self.root.iconbitmap(default='') 
        except: pass

        self.conversation = hist(50)
        self.listening = False
        self.now_playing = ""
        self.queue = queue.Queue()
        self.speech = SpeechListener(self._on_voice)
        self._wake_active = False
        self._qcount = 0
        self._ccount = 0
        self._session_start = time.time()

        # Pre-init all StringVars before any build method runs
        self.stats_vars   = {}
        self.mem_name_var = tk.StringVar(value="Commander")
        self.state_var    = tk.StringVar(value='SAY "AVA" + COMMAND  ·  OR CLICK MIC')
        self.np_var       = tk.StringVar(value="")
        self.msg_cnt_var  = tk.StringVar(value="0 MSGS")
        self.session_var  = tk.StringVar(value="SESSION: 00:00")
        self.query_var    = tk.StringVar(value="QUERIES: 0  ·  CMDS: 0")
        self.learn_var    = tk.StringVar(value="STYLE: LEARNING...")
        self.inp_var      = tk.StringVar()

        self._build_ui()
        self._init_live_stats()
        self._process_queue()

        # Boot greeting
        self.root.after(800, self._boot)

    # ── UI BUILD ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Title bar area
        title_frame = tk.Frame(self.root, bg=self.BG2, height=52)
        title_frame.pack(fill='x', padx=6, pady=(6,0))
        title_frame.pack_propagate(False)

        tk.Label(title_frame, text="A V A", font=("Orbitron",20,"bold") if self._font_exists("Orbitron") else ("Courier",18,"bold"),
                 bg=self.BG2, fg=self.CYAN).pack(side='left', padx=16, pady=8)
        tk.Label(title_frame, text="SUPERIOR EDITION 5.0  ·  LEARNING AI  ·  NATIVE DESKTOP",
                 font=("Courier",7), bg=self.BG2, fg=self.TEXT2).pack(side='left', padx=4)

        # Status dots
        self.dot_ai   = self._dot(title_frame, "AI",     self.RED)
        self.dot_voice= self._dot(title_frame, "VOICE",  self.ORANGE)
        self.dot_wake = self._dot(title_frame, "WAKE",   self.RED)
        self.dot_web  = self._dot(title_frame, "SEARCH", self.RED)

        # Clock
        self.lbl_clock = tk.Label(title_frame, text="--:--:--", font=("Courier",10),
                                   bg=self.BG2, fg=self.TEXT2)
        self.lbl_clock.pack(side='right', padx=12)

        # Settings button
        tk.Button(title_frame, text="⚙ SETTINGS", font=("Courier",8), bg=self.BG2,
                  fg=self.TEXT2, activebackground=self.BG3, activeforeground=self.CYAN,
                  relief='flat', bd=0, cursor='hand2',
                  command=self._open_settings).pack(side='right', padx=8)

        # Main content
        content = tk.Frame(self.root, bg=self.BG)
        content.pack(fill='both', expand=True, padx=6, pady=4)

        # Left panel
        left = tk.Frame(content, bg=self.BG2, width=200)
        left.pack(side='left', fill='y', padx=(0,4))
        left.pack_propagate(False)
        self._build_left(left)

        # Center panel
        center = tk.Frame(content, bg=self.BG)
        center.pack(side='left', fill='both', expand=True)
        self._build_center(center)

        # Right panel
        right = tk.Frame(content, bg=self.BG2, width=190)
        right.pack(side='right', fill='y', padx=(4,0))
        right.pack_propagate(False)
        self._build_right(right)

        # Bottom bar
        bot = tk.Frame(self.root, bg=self.BG2, height=36)
        bot.pack(fill='x', padx=6, pady=(0,6))
        bot.pack_propagate(False)
        self._build_bottom(bot)

    def _font_exists(self, name):
        try:
            tk.font.Font(family=name)
            return True
        except: return False

    def _dot(self, parent, label, color):
        f = tk.Frame(parent, bg=self.BG2)
        f.pack(side='right', padx=6)
        c = tk.Canvas(f, width=8, height=8, bg=self.BG2, highlightthickness=0)
        c.pack(side='left')
        c.create_oval(1,1,7,7,fill=color,outline='')
        tk.Label(f, text=label, font=("Courier",7), bg=self.BG2, fg=self.TEXT2).pack(side='left',padx=2)
        return c

    def _set_dot(self, dot_canvas, color):
        dot_canvas.delete('all')
        dot_canvas.create_oval(1,1,7,7,fill=color,outline='')

    def _build_left(self, parent):
        tk.Label(parent, text="◈ SYSTEM", font=("Courier",8,"bold"),
                 bg=self.BG2, fg=self.TEXT2).pack(anchor='w', padx=10, pady=(8,4))

        self.stats_vars = {}
        for name, key in [("CPU","cpu"),("RAM","ram"),("DISK","disk"),("BATTERY","bat")]:
            f = tk.Frame(parent, bg=self.BG2)
            f.pack(fill='x', padx=8, pady=2)
            tk.Label(f, text=name, font=("Courier",7), bg=self.BG2, fg=self.TEXT2, width=7, anchor='w').pack(side='left')
            v = tk.StringVar(value="--")
            self.stats_vars[key] = v
            tk.Label(f, textvariable=v, font=("Courier",9,"bold"), bg=self.BG2, fg=self.CYAN, width=6, anchor='e').pack(side='right')
            bar_bg = tk.Frame(f, bg=self.TEXT3, height=3)
            bar_bg.pack(fill='x', pady=(1,0))
            bar = tk.Frame(bar_bg, bg=self.CYAN2, height=3, width=0)
            bar.place(x=0,y=0,relheight=1)
            self.stats_vars[key+"_bar"] = bar

        # Separator
        tk.Frame(parent, bg=self.TEXT3, height=1).pack(fill='x', padx=8, pady=8)

        # Memory panel
        tk.Label(parent, text="◈ AVA MEMORY", font=("Courier",8,"bold"),
                 bg=self.BG2, fg=self.TEXT2).pack(anchor='w', padx=10, pady=(0,4))

        tk.Label(parent, textvariable=self.mem_name_var, font=("Courier",12,"bold"),
                 bg=self.BG2, fg=self.CYAN).pack(anchor='w', padx=10)

        self.mem_text = tk.Text(parent, bg=self.BG2, fg=self.TEXT2, font=("Courier",7),
                                 relief='flat', bd=0, wrap='word', state='disabled',
                                 selectbackground=self.BG3)
        self.mem_text.pack(fill='both', expand=True, padx=8, pady=4)

        # Separator
        tk.Frame(parent, bg=self.TEXT3, height=1).pack(fill='x', padx=8, pady=4)

        # Learning stats
        tk.Label(parent, text="◈ LEARNING", font=("Courier",8,"bold"),
                 bg=self.BG2, fg=self.TEXT2).pack(anchor='w', padx=10)
        self.learn_text = tk.Text(parent, bg=self.BG2, fg=self.TEXT2, font=("Courier",7),
                                   relief='flat', bd=0, wrap='word', state='disabled', height=5)
        self.learn_text.pack(fill='x', padx=8, pady=4)

        self._refresh_memory()

    def _build_center(self, parent):
        # ORB area
        orb_frame = tk.Frame(parent, bg=self.BG)
        orb_frame.pack(fill='x', pady=4)

        self.orb_canvas = tk.Canvas(orb_frame, width=160, height=160,
                                     bg=self.BG, highlightthickness=0)
        self.orb_canvas.pack()
        self._draw_orb("IDLE")

        tk.Label(orb_frame, textvariable=self.state_var, font=("Courier",8),
                 bg=self.BG, fg=self.TEXT2).pack(pady=2)

        # Now playing bar
        self.np_frame = tk.Frame(parent, bg="#0a0800", relief='flat')
        np_inner = tk.Frame(self.np_frame, bg="#0a0800")
        np_inner.pack(fill='x', padx=8, pady=4)
        tk.Label(np_inner, text="♪", font=("Courier",12), bg="#0a0800", fg=self.YELLOW).pack(side='left', padx=4)
        tk.Label(np_inner, textvariable=self.np_var, font=("Courier",9), bg="#0a0800",
                 fg=self.YELLOW, anchor='w').pack(side='left', fill='x', expand=True)
        for txt, cmd in [("⏮",lambda:self._yt_ctrl("prev")),("⏸",lambda:self._yt_ctrl("pause")),
                          ("▶",lambda:self._yt_ctrl("play")),("⏭",lambda:self._yt_ctrl("next")),
                          ("🔊",lambda:self._yt_ctrl("vol_up")),("🔉",lambda:self._yt_ctrl("vol_down"))]:
            tk.Button(np_inner, text=txt, font=("Courier",10), bg="#0a0800", fg=self.YELLOW,
                      activebackground="#1a1200", activeforeground=self.YELLOW,
                      relief='flat', bd=0, cursor='hand2', command=cmd).pack(side='right', padx=1)

        # Chat area
        chat_frame = tk.Frame(parent, bg=self.BG2)
        chat_frame.pack(fill='both', expand=True, pady=4)

        chat_header = tk.Frame(chat_frame, bg=self.BG3)
        chat_header.pack(fill='x')
        tk.Label(chat_header, text="◈ NEURAL COMM LINK  ·  LEARNING ACTIVE",
                 font=("Courier",7,"bold"), bg=self.BG3, fg=self.TEXT2).pack(side='left', padx=10, pady=4)
        tk.Label(chat_header, textvariable=self.msg_cnt_var,
                 font=("Courier",7), bg=self.BG3, fg=self.TEXT3).pack(side='right', padx=10)

        self.chat = scrolledtext.ScrolledText(
            chat_frame, bg=self.BG, fg=self.TEXT, font=("Courier",10),
            relief='flat', bd=0, wrap='word', state='disabled',
            insertbackground=self.CYAN,
            selectbackground=self.BG3
        )
        self.chat.pack(fill='both', expand=True, padx=1, pady=1)

        # Tag configs
        self.chat.tag_config("you",     foreground="#00aadd", font=("Courier",9,"bold"))
        self.chat.tag_config("ava",     foreground="#00ff88", font=("Courier",9,"bold"))
        self.chat.tag_config("msg_you", foreground="#88ccee")
        self.chat.tag_config("msg_ava", foreground="#aaddff")
        self.chat.tag_config("tag_yt",  foreground=self.YELLOW)
        self.chat.tag_config("tag_cmd", foreground=self.GREEN)
        self.chat.tag_config("tag_web", foreground=self.PURPLE)
        self.chat.tag_config("time",    foreground=self.TEXT3, font=("Courier",8))
        self.chat.tag_config("sep",     foreground=self.TEXT3)

        # Input
        inp_frame = tk.Frame(parent, bg=self.BG)
        inp_frame.pack(fill='x', pady=(4,0))

        self.mic_btn = tk.Button(inp_frame, text="🎙", font=("Courier",14),
                                  bg=self.BG2, fg=self.CYAN, activebackground=self.BG3,
                                  relief='flat', bd=0, cursor='hand2', width=3,
                                  command=self._toggle_listen)
        self.mic_btn.pack(side='left', padx=(0,4))

        self.inp = tk.Entry(inp_frame, textvariable=self.inp_var,
                             bg=self.BG2, fg=self.CYAN, font=("Courier",11),
                             insertbackground=self.CYAN, relief='flat', bd=4,
                             selectbackground=self.BG3)
        self.inp.pack(side='left', fill='x', expand=True, ipady=6)
        self.inp.bind("<Return>", lambda e: self._send())
        self.inp.insert(0, 'Try: "play Shape of You" or "AVA what is quantum computing?"')
        self.inp.config(fg=self.TEXT2)
        self.inp.bind("<FocusIn>", self._clear_placeholder)

        tk.Button(inp_frame, text="SEND", font=("Courier",9,"bold"),
                  bg=self.CYAN2, fg=self.BG, activebackground=self.CYAN,
                  relief='flat', bd=0, cursor='hand2', padx=12, pady=6,
                  command=self._send).pack(side='left', padx=(4,2))

        tk.Button(inp_frame, text="CLR", font=("Courier",9),
                  bg=self.BG2, fg=self.RED, activebackground=self.BG3,
                  relief='flat', bd=0, cursor='hand2', padx=8, pady=6,
                  command=self._clear_chat).pack(side='left')

    def _build_right(self, parent):
        tk.Label(parent, text="◈ VOICE COMMANDS", font=("Courier",8,"bold"),
                 bg=self.BG2, fg=self.TEXT2).pack(anchor='w', padx=10, pady=(8,4))

        cmds = [
            ("▶ MUSIC","play Blinding Lights The Weeknd"),
            ("▶ Lo-Fi Study","play lo-fi hip hop study beats"),
            ("⏸ Pause","pause the music"),
            ("⏭ Next Song","next song"),
            ("🔍 AI News","search latest AI news today"),
            ("🔍 Weather","search weather today Delhi"),
            ("💻 VS Code","open VS Code"),
            ("⬛ Terminal","open terminal"),
            ("📸 Screenshot","take a screenshot"),
            ("🔊 Volume Up","volume up"),
            ("🧠 Build Project","build me a React todo app"),
            ("⚡ Write Code","write a Python web scraper"),
            ("💡 Startup Ideas","give me 5 startup ideas 2025"),
            ("🧠 What I Know","what do you remember about me"),
            ("🎭 My Style","what communication style am I"),
        ]
        cmd_frame = tk.Frame(parent, bg=self.BG2)
        cmd_frame.pack(fill='both', expand=True, padx=4)

        for label, cmd in cmds:
            btn = tk.Button(cmd_frame, text=label, font=("Courier",8),
                             bg=self.BG3, fg=self.TEXT2,
                             activebackground=self.GRAY, activeforeground=self.CYAN,
                             relief='flat', bd=0, cursor='hand2', anchor='w',
                             padx=8, pady=4,
                             command=lambda c=cmd: self._process(c))
            btn.pack(fill='x', pady=1)
            btn.bind("<Enter>", lambda e,b=btn: b.config(fg=self.CYAN))
            btn.bind("<Leave>", lambda e,b=btn: b.config(fg=self.TEXT2))

    def _build_bottom(self, parent):

        tk.Label(parent, textvariable=self.session_var, font=("Courier",8),
                 bg=self.BG2, fg=self.TEXT2).pack(side='left', padx=12)
        tk.Label(parent, textvariable=self.query_var, font=("Courier",8),
                 bg=self.BG2, fg=self.TEXT2).pack(side='left', padx=12)
        tk.Label(parent, textvariable=self.learn_var, font=("Courier",8),
                 bg=self.BG2, fg=self.CYAN).pack(side='right', padx=12)


    # ── ORB DRAWING ───────────────────────────────────────────────────────────
    def _draw_orb(self, state="IDLE"):
        c = self.orb_canvas
        c.delete('all')
        cx, cy, r = 80, 80, 65

        colors = {
            "IDLE":      (self.CYAN2,     self.CYAN,   self.BG2),
            "LISTENING": (self.CYAN,      "#ffffff",   "#001830"),
            "THINKING":  (self.ORANGE,    "#ffaa00",   "#180800"),
            "SPEAKING":  (self.GREEN,     "#ffffff",   "#001810"),
            "PLAYING":   (self.YELLOW,    "#ffffff",   "#181200"),
        }
        ring_color, glow_color, core_bg = colors.get(state, colors["IDLE"])

        # Outer rings
        for i, (rad, alpha) in enumerate([(r,0.15),(r-10,0.1),(r-20,0.06)]):
            c.create_oval(cx-rad,cy-rad,cx+rad,cy+rad,
                          outline=ring_color, width=1)

        # Core
        c.create_oval(cx-40,cy-40,cx+40,cy+40, fill=core_bg, outline=ring_color, width=2)

        # Symbol
        symbols = {"IDLE":"◈","LISTENING":"◉","THINKING":"⟳","SPEAKING":"◈","PLAYING":"♪"}
        sym = symbols.get(state,"◈")
        c.create_text(cx,cy, text=sym, fill=glow_color,
                      font=("Courier",22,"bold") if state!="IDLE" else ("Courier",18))

        # State label
        c.create_text(cx,cy+54, text=state, fill=ring_color,
                      font=("Courier",7,"bold"))

    def _animate_orb(self, state):
        self._draw_orb(state)
        labels = {
            "IDLE":      'SAY "AVA" + COMMAND  ·  OR CLICK MIC',
            "LISTENING": "LISTENING — SPEAK NOW, COMMANDER",
            "THINKING":  "NEURAL LINK ACTIVE — PROCESSING...",
            "SPEAKING":  "AVA IS RESPONDING...",
            "PLAYING":   "YOUTUBE PLAYBACK ACTIVE",
        }
        self.state_var.set(labels.get(state,''))

    # ── CHAT ──────────────────────────────────────────────────────────────────
    def _add_msg(self, role, text, tag=""):
        self.chat.configure(state='normal')
        ts = datetime.datetime.now().strftime("%H:%M")
        if role == "user":
            self.chat.insert('end', f"\n  YOU", "you")
            self.chat.insert('end', f" [{ts}]\n", "time")
            self.chat.insert('end', f"  {text}\n", "msg_you")
        else:
            self.chat.insert('end', f"\n  AVA", "ava")
            if tag:
                tag_labels = {"yt":"[YOUTUBE]","cmd":"[EXECUTING]","web":"[WEB SEARCH]"}
                self.chat.insert('end', f" {tag_labels.get(tag,'')}", f"tag_{tag}")
            self.chat.insert('end', f" [{ts}]\n", "time")
            self.chat.insert('end', f"  {text}\n", "msg_ava")
        self.chat.insert('end', f"  {'─'*50}\n", "sep")
        self.chat.configure(state='disabled')
        self.chat.see('end')
        count = self.chat.get('1.0','end').count('\n')
        self.msg_cnt_var.set(f"{self._qcount} MSGS")

    def _add_typing(self):
        self.chat.configure(state='normal')
        self.chat.insert('end', "\n  AVA [thinking...]\n", "time")
        self.chat.insert('end', "  ···\n", "msg_ava")
        self.chat.configure(state='disabled')
        self.chat.see('end')
        self._typing_pos = self.chat.index('end-3l')

    def _remove_typing(self):
        try:
            self.chat.configure(state='normal')
            self.chat.delete('end-4l', 'end-1c')
            self.chat.configure(state='disabled')
        except: pass

    # ── MEMORY/LEARNING DISPLAY ───────────────────────────────────────────────
    def _refresh_memory(self):
        m = mem()
        l = learn()
        self.mem_name_var.set(m.get("name","Commander"))

        self.mem_text.configure(state='normal')
        self.mem_text.delete('1.0','end')
        for p in m.get("projects",[])[-3:]:
            self.mem_text.insert('end', f"▸ {p['text'][:55]}\n")
        for f in m.get("facts",[])[-4:]:
            self.mem_text.insert('end', f"· {f['text'][:55]}\n")
        if not m.get("projects") and not m.get("facts"):
            self.mem_text.insert('end','Memories build as you chat.')
        self.mem_text.configure(state='disabled')

        self.learn_text.configure(state='normal')
        self.learn_text.delete('1.0','end')
        self.learn_text.insert('end', f"Style: {l.get('style','learning')}\n")
        self.learn_text.insert('end', f"Msgs:  {l.get('total_messages',0)}\n")
        interests = l.get('interests',[])[:4]
        if interests: self.learn_text.insert('end', f"Topics: {', '.join(interests)}\n")
        self.learn_text.configure(state='disabled')

        self.learn_var.set(f"STYLE: {l.get('style','LEARNING').upper()}  ·  MSGS: {l.get('total_messages',0)}")

    # ── CORE PROCESS ──────────────────────────────────────────────────────────
    def _local_intent(self, text):
        low = text.lower().strip()
        pm = re.match(r'^(?:play|put on|stream|play me)\s+(.+)', low)
        if pm: return {"type":"yt_play","query":pm.group(1)}
        if re.search(r'\b(pause|stop music|stop playing)\b',low): return {"type":"yt_ctrl","ctrl":"pause"}
        if re.search(r'\b(resume|unpause)\b',low):                return {"type":"yt_ctrl","ctrl":"play"}
        if re.search(r'\b(next song|skip|next track)\b',low):     return {"type":"yt_ctrl","ctrl":"next"}
        if re.search(r'\b(previous|prev|go back)\b',low):         return {"type":"yt_ctrl","ctrl":"prev"}
        if re.search(r'\bvolume up\b',low):                        return {"type":"yt_ctrl","ctrl":"vol_up"}
        if re.search(r'\bvolume down\b',low):                      return {"type":"yt_ctrl","ctrl":"vol_down"}
        if re.search(r'\b(screenshot|screen capture)\b',low):
            path = str(Path.home()/f"AVA_{int(time.time())}.png")
            try:
                import pyautogui; pyautogui.screenshot().save(path)
            except: pass
            return {"type":"screenshot","path":path}
        return None

    def _process(self, text):
        if not text or not text.strip(): return
        self._qcount += 1
        self.query_var.set(f"QUERIES: {self._qcount}  ·  CMDS: {self._ccount}")

        # Update learning engine
        LEARNER.update(text)
        hist_add("user", text)

        self._add_msg("user", text)
        intent = self._local_intent(text)

        if intent:
            self._ccount += 1
            self.query_var.set(f"QUERIES: {self._qcount}  ·  CMDS: {self._ccount}")

            if intent["type"] == "yt_play":
                reply = f"Playing {intent['query']} right now!"
                self._add_msg("ava", reply, "yt")
                self.np_var.set(intent["query"])
                self.np_frame.pack(fill='x', padx=0, pady=2)
                VOICE.speak(reply)
                self._animate_orb("PLAYING")
                threading.Thread(target=lambda: yt_play(intent["query"]), daemon=True).start()
                return

            if intent["type"] == "yt_ctrl":
                labels = {"pause":"Pausing.","play":"Resuming.","next":"Next track.","prev":"Previous.","vol_up":"Volume up.","vol_down":"Volume down."}
                reply = labels.get(intent["ctrl"],"Done.")
                self._add_msg("ava", reply, "cmd")
                VOICE.speak(reply)
                threading.Thread(target=lambda: yt_ctrl(intent["ctrl"]), daemon=True).start()
                return

            if intent["type"] == "screenshot":
                reply = f"Screenshot saved to your desktop, {mem().get('name','Commander')}."
                self._add_msg("ava", reply, "cmd")
                VOICE.speak(reply)
                return

        # Ask AI
        self._animate_orb("THINKING")
        self._add_typing()

        def ai_thread():
            raw = call_ai(text, self.conversation)
            self.queue.put(("ai_response", text, raw))

        threading.Thread(target=ai_thread, daemon=True).start()

    def _handle_ai_response(self, user_msg, raw):
        self._remove_typing()
        hist_add("assistant", raw)
        self.conversation = hist(30)
        LEARNER.update(user_msg)  # re-update after seeing full exchange
        self._refresh_memory()

        # Try parse JSON action
        try:
            p = json.loads(raw)
            reply = p.get("reply","Executing.")

            if p.get("action") == "yt_play" and p.get("query"):
                self._add_msg("ava", reply, "yt")
                VOICE.speak(reply, lambda: self._animate_orb("PLAYING"))
                self.np_var.set(p["query"])
                self.np_frame.pack(fill='x', padx=0, pady=2)
                threading.Thread(target=lambda: yt_play(p["query"]), daemon=True).start()
                return

            if p.get("action") == "yt_ctrl":
                self._add_msg("ava", reply, "cmd")
                VOICE.speak(reply)
                threading.Thread(target=lambda: yt_ctrl(p["ctrl"]), daemon=True).start()
                return

            if p.get("action") == "app_open":
                self._add_msg("ava", reply, "cmd")
                VOICE.speak(reply)
                launch_app(p.get("app",""))
                self._animate_orb("IDLE")
                return

            if p.get("action") == "search":
                self._add_msg("ava", reply, "web")
                VOICE.speak(reply)
                def do_search():
                    result = web_search(p["query"])
                    if result:
                        sr_reply = result[:300]
                        self.queue.put(("search_result", sr_reply))
                threading.Thread(target=do_search, daemon=True).start()
                return

            self._add_msg("ava", reply)
            VOICE.speak(reply, lambda: self._animate_orb("IDLE"))

        except (json.JSONDecodeError, KeyError):
            # Plain text response
            self._add_msg("ava", raw)
            VOICE.speak(raw, lambda: self._animate_orb("IDLE"))
        self._animate_orb("IDLE")

    # ── EVENT QUEUE (thread-safe UI updates) ──────────────────────────────────
    def _process_queue(self):
        try:
            while True:
                item = self.queue.get_nowait()
                try:
                    if item[0] == "ai_response":
                        _, user_msg, raw = item
                        self._handle_ai_response(user_msg, raw)
                    elif item[0] == "search_result":
                        self._add_msg("ava", item[1], "web")
                        try: VOICE.speak(item[1])
                        except: pass
                    elif item[0] == "voice_text":
                        self._process(item[1])
                    elif item[0] == "wake_detected":
                        self._animate_orb("LISTENING")
                        self.state_var.set("WAKE WORD DETECTED — SPEAK NOW")
                        try: VOICE.speak("Yes, I'm here. What do you need?")
                        except: pass
                        self.root.after(800, self._toggle_listen)
                except Exception as e:
                    print(f"[AVA] Queue item error: {e}")
        except queue.Empty:
            pass
        except Exception as e:
            print(f"[AVA] Queue error: {e}")
        try:
            self.root.after(50, self._process_queue)
        except: pass

    # ── VOICE CONTROL ─────────────────────────────────────────────────────────
    def _on_voice(self, text):
        self.queue.put(("voice_text", text))

    def _toggle_listen(self):
        if self.listening:
            self.listening = False
            self.mic_btn.config(fg=self.CYAN)
            self._animate_orb("IDLE")
        else:
            self.listening = True
            self.mic_btn.config(fg=self.RED)
            self._animate_orb("LISTENING")
            self.speech.listen_once()

    # ── STATS ─────────────────────────────────────────────────────────────────
    def _init_live_stats(self):
        def update():
            try:
                # Clock
                self.lbl_clock.config(text=datetime.datetime.now().strftime("%H:%M:%S"))
                # Session
                elapsed = int(time.time() - self._session_start)
                self.session_var.set(f"SESSION: {elapsed//60:02d}:{elapsed%60:02d}")
                # System stats
                if HAS_PSUTIL:
                    try:
                        cpu = psutil.cpu_percent()
                        ram = psutil.virtual_memory().percent
                        disk = psutil.disk_usage('/').percent
                        bat = psutil.sensors_battery()
                        bat_pct = round(bat.percent) if bat else 0
                        for key, val in [("cpu",cpu),("ram",ram),("disk",disk),("bat",bat_pct)]:
                            if key in self.stats_vars:
                                self.stats_vars[key].set(f"{val}%")
                            bar_key = key+"_bar"
                            if bar_key in self.stats_vars:
                                bar = self.stats_vars[bar_key]
                                try:
                                    parent_w = bar.master.winfo_width()
                                    if parent_w > 0:
                                        bar.place(x=0,y=0,relheight=1,width=int(parent_w*(val/100)))
                                    bar.config(bg=self.RED if val>80 else self.CYAN2)
                                except: pass
                    except: pass
            except: pass
            try:
                self.root.after(2000, update)
            except: pass
        update()

    # ── BOOT ──────────────────────────────────────────────────────────────────
    def _boot(self):
        try:
            m = mem()
            name = m.get("name","Commander")
            l = learn()
            sessions = l.get("sessions",0)
            l["sessions"] = sessions + 1
            learn_set(l)
            greetings = [
                f"AVA 5.0 online. Good to see you again, {name}.",
                f"Neural core active, {name}. Ready and learning.",
                f"Back online, {name}. {l.get('total_messages',0)} messages in my learning model.",
            ]
            greeting = greetings[sessions % len(greetings)] if sessions > 0 else                 "Hello! I am AVA 5.0. Add your OpenRouter API key in Settings to activate my brain. Get it free at openrouter.ai"
            self._add_msg("ava", greeting)
            try: VOICE.speak(greeting)
            except Exception as e: print(f"[AVA] Voice: {e}")
            try: self._set_dot(self.dot_ai, self.GREEN)
            except: pass
            try:
                if HAS_TTS or HAS_ELEVEN: self._set_dot(self.dot_voice, self.GREEN)
            except: pass
        except Exception as e:
            print(f"[AVA] Boot error: {e}")
            try: self._add_msg("ava", "AVA 5.0 online. Add Groq key in Settings.")
            except: pass


    # ── SETTINGS ─────────────────────────────────────────────────────────────
    def _open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("AVA Settings")
        win.geometry("520x600")
        win.configure(bg=self.BG2)
        win.resizable(False,False)

        tk.Label(win, text="◈  AVA 5.0  SETTINGS", font=("Courier",14,"bold"),
                 bg=self.BG2, fg=self.CYAN).pack(pady=16)

        c = cfg()
        fields = [
            ("OPENROUTER API KEY (free — openrouter.ai)", "openrouter_key", c.get("openrouter_key",""), False),
            ("ELEVENLABS KEY (optional — elevenlabs.io)", "eleven_key", c.get("eleven_key",""), False),
            ("ELEVENLABS VOICE (Rachel / Bella / Elli / Dorothy)", "eleven_voice", c.get("eleven_voice","Rachel"), True),
            ("TAVILY KEY (optional — tavily.com)", "tavily_key", c.get("tavily_key",""), False),
            ("PICOVOICE KEY (optional — picovoice.ai)", "pico_key", c.get("pico_key",""), False),
        ]

        entries = {}
        for label, key, val, is_plain in fields:
            tk.Label(win, text=label, font=("Courier",8), bg=self.BG2, fg=self.TEXT2).pack(anchor='w', padx=20, pady=(8,2))
            e = tk.Entry(win, font=("Courier",11), bg=self.BG3, fg=self.CYAN,
                         insertbackground=self.CYAN, relief='flat', bd=4,
                         show='' if is_plain else '')
            if not is_plain:
                e.config(show='•' if val and key!='eleven_voice' else '')
            e.insert(0, val)
            e.pack(fill='x', padx=20, ipady=5)
            entries[key] = e

        status_var = tk.StringVar()
        tk.Label(win, textvariable=status_var, font=("Courier",9),
                 bg=self.BG2, fg=self.GREEN).pack(pady=4)

        def save():
            for key, e in entries.items():
                v = e.get().strip()
                if v: cfg_set(**{('gemini_key' if key=='groq_key' else key):v})
            # Reinit ElevenLabs if key changed
            eleven_key = entries["eleven_key"].get().strip()
            eleven_voice = entries["eleven_voice"].get().strip() or "Rachel"
            if eleven_key:
                ok = VOICE.init_eleven(eleven_key, eleven_voice)
                self._set_dot(self.dot_voice, self.GREEN if ok else self.RED)
            status_var.set("✓ Settings saved!")
            self.root.after(2000, lambda: status_var.set(""))

        def clear_mem():
            if tk.messagebox.askyesno("Clear Memory","Clear all AVA memory?",parent=win):
                mem_set({"name":"Commander","facts":[],"projects":[],"mood_history":[],"topics":{}})
                HIST_F.write_text("[]")
                self._refresh_memory()
                status_var.set("✓ Memory cleared.")

        def start_wake():
            pico_key = entries["pico_key"].get().strip()
            if not pico_key: status_var.set("✗ Picovoice key required"); return
            if not HAS_WAKE: status_var.set("✗ Install: pip install pvporcupine sounddevice"); return
            self._start_wake_word(pico_key)
            status_var.set("✓ Wake word engine active!")
            self._set_dot(self.dot_wake, self.GREEN)

        tk.Button(win, text="SAVE SETTINGS", font=("Courier",10,"bold"),
                  bg=self.CYAN2, fg=self.BG, relief='flat', cursor='hand2',
                  padx=20, pady=8, command=save).pack(pady=8)

        tk.Button(win, text="▶ ACTIVATE WAKE WORD", font=("Courier",9),
                  bg=self.BG3, fg=self.CYAN, relief='flat', cursor='hand2',
                  padx=16, pady=6, command=start_wake).pack(pady=2)

        tk.Button(win, text="⚠ CLEAR ALL MEMORY", font=("Courier",9),
                  bg=self.BG3, fg=self.RED, relief='flat', cursor='hand2',
                  padx=16, pady=6, command=clear_mem).pack(pady=2)

        tk.Button(win, text="CLOSE", font=("Courier",9),
                  bg=self.BG3, fg=self.TEXT2, relief='flat', cursor='hand2',
                  padx=16, pady=6, command=win.destroy).pack(pady=2)

    def _start_wake_word(self, pico_key):
        def run():
            try:
                porc = pvporcupine.create(access_key=pico_key, keywords=["jarvis"])
                self._wake_active = True
                import sounddevice as sd
                def callback(indata, frames, t, status):
                    if not self._wake_active: raise sd.CallbackStop()
                    pcm = struct.unpack_from("h"*porc.frame_length, bytes(indata)[:porc.frame_length*2])
                    if porc.process(pcm) >= 0:
                        self.queue.put(("wake_detected",))
                with sd.RawInputStream(samplerate=porc.sample_rate, channels=1, dtype='int16',
                                       blocksize=porc.frame_length, callback=callback):
                    while self._wake_active:
                        import time as _t; _t.sleep(0.1)
                porc.delete()
            except Exception as e:
                print(f"[AVA] Wake: {e}")
        threading.Thread(target=run, daemon=True).start()

    # ── HELPERS ───────────────────────────────────────────────────────────────
    def _send(self):
        text = self.inp_var.get().strip()
        if text and text != 'Try: "play Shape of You" or "AVA what is quantum computing?"':
            self.inp_var.set("")
            self._process(text)

    def _clear_placeholder(self, event):
        if self.inp_var.get() == 'Try: "play Shape of You" or "AVA what is quantum computing?"':
            self.inp_var.set("")
            self.inp.config(fg=self.CYAN)

    def _clear_chat(self):
        self.chat.configure(state='normal')
        self.chat.delete('1.0','end')
        self.chat.configure(state='disabled')
        self.conversation = []
        self._add_msg("ava","Memory cleared for this session. My long-term learning remains intact.")

    def _yt_ctrl(self, action):
        threading.Thread(target=lambda: yt_ctrl(action), daemon=True).start()
        if action == "pause":
            self.np_frame.pack_forget()
            self._animate_orb("IDLE")

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _on_close(self):
        self._wake_active = False
        self.root.destroy()


# ── ENTRY ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import tkinter.font
    import tkinter.messagebox

    print("◈  A V A  5.0  —  SUPERIOR EDITION")
    print("="*40)
    print(f"  pyttsx3    : {'✓' if HAS_TTS else '✗ pip install pyttsx3'}")
    print(f"  speech_rec : {'✓' if HAS_SR else '✗ pip install SpeechRecognition'}")
    print(f"  selenium   : {'✓' if HAS_SELENIUM else '✗ pip install selenium'}")
    print(f"  wake word  : {'✓' if HAS_WAKE else '✗ pip install pvporcupine sounddevice'}")
    print(f"  elevenlabs : {'✓' if HAS_ELEVEN else '✗ pip install elevenlabs'}")
    print(f"  psutil     : {'✓' if HAS_PSUTIL else '✗ pip install psutil'}")
    print("="*40)

    app = AVADesktop()
    app.run()
