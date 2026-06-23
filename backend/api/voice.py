"""
AVA Voice API
POST /api/voice/transcribe  — Whisper STT (audio → text)
POST /api/voice/speak       — ElevenLabs TTS (text → audio stream)
WS   /api/voice/ws          — Full Pipeline (STT -> Orchestrator -> TTS)
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx
import json
import asyncio

from api.auth import get_current_user
from db.postgres import User
from core.config import settings

# In a real setup, we would import the orchestrator here
# from agents.orchestrator import run_ava

router = APIRouter()


class SpeakRequest(BaseModel):
    text: str
    voice_id: str | None = None


@router.post("/transcribe")
async def transcribe(
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user, use_cache=False),
):
    if not settings.GROQ_API_KEY:
        raise HTTPException(status_code=503, detail="GROQ_API_KEY not configured")

    audio_bytes = await audio.read()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
            files={"file": (audio.filename or "audio.webm", audio_bytes, audio.content_type)},
            data={"model": "whisper-large-v3"},
            timeout=30,
        )

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Transcription failed")

    result = response.json()
    return {"text": result.get("text", "").strip()}


@router.post("/speak")
async def speak(
    body: SpeakRequest,
    current_user: User = Depends(get_current_user, use_cache=False),
):
    if not settings.ELEVENLABS_API_KEY:
        raise HTTPException(status_code=503, detail="ELEVENLABS_API_KEY not configured")

    voice_id = body.voice_id or settings.ELEVENLABS_VOICE_ID

    async def stream_audio():
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream",
                headers={
                    "xi-api-key": settings.ELEVENLABS_API_KEY,
                    "Content-Type": "application/json",
                },
                json={
                    "text": body.text,
                    "model_id": "eleven_monolingual_v1",
                    "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
                },
                timeout=60,
            ) as resp:
                async for chunk in resp.aiter_bytes(chunk_size=1024):
                    yield chunk

    return StreamingResponse(
        stream_audio(),
        media_type="audio/mpeg",
        headers={"Transfer-Encoding": "chunked"},
    )


@router.websocket("/ws/{session_id}")
async def voice_websocket(websocket: WebSocket, session_id: str):
    """
    Full Voice Pipeline:
    Frontend Audio -> VAD (frontend/backend) -> Whisper STT -> Orchestrator -> ElevenLabs TTS WebSocket -> Frontend Audio Playback
    """
    await websocket.accept()
    audio_buffer = bytearray()
    
    # Needs a real user ideally, but for demo we mock or expect token in first message
    current_user_id = "test-user-id" # Simplified for this snippet

    try:
        while True:
            # Receive message from frontend (either bytes for audio, or JSON for control signals)
            message = await websocket.receive()
            
            if "bytes" in message:
                audio_buffer.extend(message["bytes"])
                
            elif "text" in message:
                data = json.loads(message["text"])
                
                # VAD: High priority signal from frontend when silence > 800ms
                if data.get("type") == "vad_stop":
                    # 1. Trigger stop audio stream to frontend to halt any playing response
                    await websocket.send_json({"type": "stop_audio_stream"})
                    
                    if not audio_buffer:
                        continue
                        
                    # 2. Send accumulated audio buffer to Whisper
                    try:
                        async with httpx.AsyncClient() as client:
                            response = await client.post(
                                "https://api.groq.com/openai/v1/audio/transcriptions",
                                headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                                files={"file": ("audio.webm", bytes(audio_buffer), "audio/webm")},
                                data={"model": "whisper-large-v3"},
                                timeout=30,
                            )
                        audio_buffer.clear()
                        if response.status_code != 200:
                            continue
                        transcript = response.json().get("text", "").strip()
                        if not transcript:
                            continue
                            
                        # Inform frontend we heard them
                        await websocket.send_json({"type": "transcript", "text": transcript})

                        # 3. Pass to Orchestrator LangGraph Router
                        from agents.orchestrator import run_ava
                        
                        full_response_text = ""
                        # Note: we need a session history if we want context. Keeping it simple here.
                        async for event in run_ava(user_message=transcript, user_id=current_user_id, session_id=session_id):
                            if event["type"] == "chunk":
                                full_response_text += event["content"]
                        
                        # 4. Stream AI text chunks to ElevenLabs WebSocket (Here using REST stream for simplicity)
                        async def stream_audio_back():
                            async with httpx.AsyncClient() as client:
                                async with client.stream(
                                    "POST",
                                    f"https://api.elevenlabs.io/v1/text-to-speech/{settings.ELEVENLABS_VOICE_ID}/stream",
                                    headers={
                                        "xi-api-key": settings.ELEVENLABS_API_KEY,
                                        "Content-Type": "application/json",
                                    },
                                    json={
                                        "text": full_response_text,
                                        "model_id": "eleven_monolingual_v1",
                                    },
                                    timeout=60,
                                ) as resp:
                                    async for chunk in resp.aiter_bytes(chunk_size=4096):
                                        await websocket.send_bytes(chunk)
                        
                        # Fire and forget the audio stream back
                        asyncio.create_task(stream_audio_back())

                    except Exception as e:
                        print(f"Voice pipeline error: {e}")
                    
    except WebSocketDisconnect:
        print("Voice WebSocket disconnected")

