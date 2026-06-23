"""
AVA Chat API — Phase 2 Update
WebSocket now streams real AI responses via LangGraph orchestrator.
REST endpoint also upgraded with real AI.
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import Optional
import json

from db.postgres import get_db, User, ChatSession, Message
from api.auth import get_current_user, decode_token
from agents.orchestrator import run_ava
from memory.chroma import store_memory

router = APIRouter()
bearer = HTTPBearer(auto_error=False)


# ── Schemas ──────────────────────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    title: Optional[str] = None


class SendMessageRequest(BaseModel):
    content: str


# ── Sessions ──────────────────────────────────────────────────────────

@router.post("/sessions", status_code=201)
async def create_session(
    body: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = ChatSession(user_id=current_user.id, title=body.title or "New Chat")
    db.add(session)
    await db.flush()
    return {"id": session.id, "title": session.title, "created_at": str(session.created_at)}


@router.get("/sessions")
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(desc(ChatSession.updated_at))
        .limit(50)
    )
    sessions = result.scalars().all()
    return [{"id": s.id, "title": s.title, "created_at": str(s.created_at)} for s in sessions]


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    msgs = await db.execute(
        select(Message).where(Message.session_id == session_id).order_by(Message.created_at)
    )
    messages = msgs.scalars().all()

    return {
        "id": session.id,
        "title": session.title,
        "created_at": str(session.created_at),
        "messages": [
            {"id": m.id, "role": m.role, "content": m.content,
             "agent": m.agent, "created_at": str(m.created_at)}
            for m in messages
        ],
    }


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.delete(session)


# ── REST message (with real AI) ───────────────────────────────────────

@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: str,
    body: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Load conversation history
    msgs_result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)
        .limit(20)
    )
    history = [
        {"role": m.role, "content": m.content}
        for m in msgs_result.scalars().all()
    ]

    # Save user message
    user_msg = Message(session_id=session_id, role="user", content=body.content)
    db.add(user_msg)
    await db.flush()

    # Run AVA orchestrator
    full_response = []
    active_agent = "orchestrator"

    async for event in run_ava(
        user_message=body.content,
        user_id=current_user.id,
        session_id=session_id,
        history=history,
    ):
        if event["type"] == "agent":
            active_agent = event["agent"]
        elif event["type"] == "chunk":
            full_response.append(event["content"])

    response_text = "".join(full_response)

    # Save AVA reply
    ava_msg = Message(
        session_id=session_id,
        role="assistant",
        content=response_text,
        agent=active_agent,
    )
    db.add(ava_msg)

    # Auto-store memory if meaningful
    if len(body.content) > 20:
        await store_memory(
            current_user.id,
            f"User said: {body.content[:200]}",
            {"session_id": session_id, "type": "message"},
        )

    return {
        "user_message": {"id": user_msg.id, "content": user_msg.content},
        "ava_reply": {
            "id": ava_msg.id,
            "content": response_text,
            "agent": active_agent,
        },
    }


# ── WebSocket Manager ──────────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        # user_id -> list of WebSockets
        self.active_connections: dict[str, list[WebSocket]] = {}

    def connect(self, user_id: str, websocket: WebSocket):
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self.active_connections:
            try:
                self.active_connections[user_id].remove(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            except ValueError:
                pass

    async def broadcast_to_user(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

manager = ConnectionManager()

# ── WebSocket — real-time streaming ──────────────────────────────────

@router.websocket("/ws/{session_id}")
async def websocket_chat(
    websocket: WebSocket,
    session_id: str,
):
    """
    Real-time WebSocket chat with streaming AI responses.

    Client sends:  { "content": "user message", "token": "jwt..." }
    Server sends:
      { "type": "connected" }
      { "type": "agent",   "agent": "orchestrator|coder|researcher" }
      { "type": "chunk",   "content": "..." }
      { "type": "done",    "agent": "..." }
      { "type": "error",   "message": "..." }
    """
    await websocket.accept()
    await websocket.send_json({"type": "connected", "message": "AVA WebSocket ready"})

    current_user_id: Optional[str] = None
    session_history: list[dict] = []

    try:
        while True:
            raw = await websocket.receive_text()
            payload = json.loads(raw)

            # Auth via token in first payload
            if not current_user_id:
                incoming_token = payload.get("token", "")
                if not incoming_token:
                    await websocket.send_json({"type": "error", "message": "No auth token provided"})
                    continue
                try:
                    token_data = decode_token(incoming_token)
                    current_user_id = token_data.get("sub")
                    if current_user_id:
                        manager.connect(current_user_id, websocket)
                except Exception:
                    await websocket.send_json({"type": "error", "message": "Invalid token"})
                    continue

            user_content = payload.get("content", "").strip()
            if not user_content:
                continue

            # Add user message to local history
            session_history.append({"role": "user", "content": user_content})

            # Stream AVA response
            full_response = []
            active_agent  = "orchestrator"

            async for event in run_ava(
                user_message=user_content,
                user_id=current_user_id,
                session_id=session_id,
                history=session_history[:-1],
            ):
                if event["type"] == "agent":
                    active_agent = event["agent"]
                    await websocket.send_json({"type": "agent", "agent": active_agent})

                elif event["type"] == "chunk":
                    full_response.append(event["content"])
                    await websocket.send_json({"type": "chunk", "content": event["content"]})

                elif event["type"] == "done":
                    await websocket.send_json({"type": "done", "agent": active_agent})

            # Save AVA reply to local history
            session_history.append({
                "role": "assistant",
                "content": "".join(full_response),
            })

    except WebSocketDisconnect:
        if current_user_id:
            manager.disconnect(current_user_id, websocket)
    except Exception as e:
        if current_user_id:
            manager.disconnect(current_user_id, websocket)
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass

