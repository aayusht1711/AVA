# AVA — Autonomous Virtual Assistant

Your personal Jarvis. Witty, adaptive, full-stack AI system.

## Stack
- **Frontend**: Next.js 14 + TypeScript + Tailwind
- **Backend**: FastAPI (Python) + PostgreSQL + ChromaDB
- **AI**: Groq (Llama 3.3 70B) + Gemini 1.5 Flash — both free
- **Voice**: Whisper STT (Groq) + ElevenLabs TTS
- **Agents**: LangGraph orchestration (Phase 2)
- **Deploy**: Google Cloud Run

---

## Phase 1 Setup — Local Dev

### 1. Clone and enter
```bash
git clone <your-repo>
cd ava
```

### 2. Get your free API keys (10 mins)
| Service | URL | Cost |
|---------|-----|------|
| Groq (AI + STT) | console.groq.com | Free |
| Gemini Flash | aistudio.google.com | Free |
| ElevenLabs (voice) | elevenlabs.io | 10k/mo free |
| Tavily (search) | tavily.com | 1k/mo free |
| E2B (code sandbox) | e2b.dev | Free tier |

### 3. Set up environment
```bash
cp .env.example .env
# Fill in your API keys in .env
```

### 4. Start with Docker
```bash
docker-compose up --build
```

This starts:
- PostgreSQL on port 5432
- ChromaDB on port 8001
- FastAPI backend on port 8000
- Next.js frontend on port 3000

### 5. Open AVA
```
http://localhost:3000
```

Sign up → get redirected to dashboard → start talking to AVA.

---

## Project Structure

```
ava/
├── backend/                  # FastAPI Python
│   ├── main.py               # Entry point
│   ├── core/
│   │   ├── config.py         # All env vars
│   │   └── security.py       # JWT + password hashing
│   ├── api/
│   │   ├── auth.py           # Signup, login, me
│   │   ├── chat.py           # Sessions + WebSocket
│   │   └── voice.py          # STT + TTS
│   ├── db/
│   │   └── postgres.py       # Models + async engine
│   ├── agents/               # Phase 2: LangGraph agents
│   ├── memory/               # Phase 2: ChromaDB
│   ├── tools/                # Phase 2: E2B, Tavily
│   └── requirements.txt
│
├── frontend/                 # Next.js 14
│   ├── app/
│   │   ├── (auth)/
│   │   │   ├── login/        # Login page
│   │   │   └── signup/       # Signup page
│   │   ├── dashboard/        # Main AVA interface
│   │   └── api/auth/         # NextAuth handler
│   ├── components/
│   │   ├── layout/
│   │   │   ├── TopBar.tsx    # Nav + status chips
│   │   │   ├── SplashScreen.tsx
│   │   │   └── HomeScreen.tsx
│   │   ├── voice/
│   │   │   └── VoiceScreen.tsx
│   │   └── chat/
│   │       └── ChatScreen.tsx
│   ├── lib/
│   │   ├── api.ts            # Axios client + helpers
│   │   └── store/auth.ts     # Zustand auth state
│   └── styles/globals.css
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Build Phases

| Phase | What | Status |
|-------|------|--------|
| **1** | FastAPI + PostgreSQL + NextAuth + WebSocket + UI | ✅ **Done** |
| 2 | Groq + Gemini routing + LangGraph orchestrator | 🔜 Next |
| 3 | All 8 agents (Coder, Researcher, Document, Memory, File, Data, Task) | 🔜 |
| 4 | ElevenLabs voice pipeline + Whisper STT | 🔜 |
| 5 | ChromaDB long-term memory + E2B sandbox | 🔜 |
| 6 | Google Cloud Run deployment | 🔜 |

---

## API Reference

### Auth
```
POST /api/auth/signup   { name, email, password }
POST /api/auth/login    { email, password }
GET  /api/auth/me       → { id, name, email }
POST /api/auth/logout
```

### Chat
```
POST   /api/chat/sessions              → create session
GET    /api/chat/sessions              → list sessions
GET    /api/chat/sessions/{id}         → get session + messages
DELETE /api/chat/sessions/{id}         → delete
POST   /api/chat/sessions/{id}/messages → send message
WS     /api/chat/ws/{session_id}       → streaming
```

### Voice
```
POST /api/voice/transcribe   audio file → { text }
POST /api/voice/speak        { text }   → audio stream
```

---

## Deployment (Phase 6 — Google Cloud Run)

```bash
# Build and push
gcloud builds submit --tag gcr.io/$PROJECT_ID/ava-backend ./backend
gcloud builds submit --tag gcr.io/$PROJECT_ID/ava-frontend ./frontend

# Deploy
gcloud run deploy ava-backend --image gcr.io/$PROJECT_ID/ava-backend --platform managed
gcloud run deploy ava-frontend --image gcr.io/$PROJECT_ID/ava-frontend --platform managed
```

---

Built with ❤️ — AVA v1.0, Phase 1

---

## Phase 2 — What was added

### Backend
| File | What it does |
|------|-------------|
| `agents/router.py` | Routes tasks → Groq (fast) or Gemini Flash (long context) |
| `agents/orchestrator.py` | LangGraph ReAct loop — the main brain |
| `agents/researcher.py` | Live web search via Tavily + LLM synthesis |
| `agents/coder.py` | Writes code → runs in E2B → auto-debugs (3 retries) |
| `agents/prompts.py` | AVA personality + agent system prompts |
| `memory/chroma.py` | ChromaDB vector store per user |
| `tools/tavily_tool.py` | Tavily web search wrapper |
| `tools/e2b_tool.py` | E2B isolated code sandbox wrapper |
| `tools/pdf_tool.py` | ReportLab PDF generator |
| `api/chat.py` | Upgraded — real AI via WebSocket streaming |

### Frontend
| File | What changed |
|------|-------------|
| `components/chat/ChatScreen.tsx` | Real WebSocket streaming, live agent traces, code highlighting |

### How the AI routing works
```
User message
     │
     ▼
  router.py  ──── contains "search/find/latest"? ──→  researcher.py (Tavily)
     │
     ├─── contains "code/debug/write/python"?   ──→  coder.py (E2B sandbox)
     │
     └─── everything else                        ──→  Groq/Gemini direct
```
