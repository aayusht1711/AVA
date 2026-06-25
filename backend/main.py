"""
AVA Backend — FastAPI Entry Point
Phase 1: Foundation
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.auth import router as auth_router
from api.chat import router as chat_router
from api.voice import router as voice_router
from db.postgres import init_db
from core.config import settings
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    await init_db()
    scheduler.start()
    print("✅ AVA Backend online")
    yield
    scheduler.shutdown()
    print("👋 AVA Backend shutting down")


app = FastAPI(
    title="AVA — Autonomous Virtual Assistant",
    description="Backend API for AVA multi-agent system",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(voice_router, prefix="/api/voice", tags=["voice"])


@app.get("/")
async def root():
    return {"status": "online", "service": "AVA Backend", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
