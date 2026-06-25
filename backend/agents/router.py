"""
AVA Model Router
Routes tasks to the right free AI model:
  - Groq (Llama 3.3 70B)  → fast reasoning, chat, code, short tasks
  - Gemini 1.5 Flash       → long context, file reading, document tasks
"""

from enum import Enum
from groq import AsyncGroq
import google.generativeai as genai
from core.config import settings


class ModelChoice(str, Enum):
    GROQ = "groq"
    GEMINI = "gemini"


# Keywords that trigger Gemini (long context / file tasks)
GEMINI_TRIGGERS = {
    "summarize", "document", "pdf", "long", "file",
    "image", "upload", "analyse", "analyze", "report",
    "essay", "transcribe", "extract all", "read this",
    "csv", "plot",
}


def choose_model(message: str) -> ModelChoice:
    """Pick the best model for this message."""
    lower = message.lower()
    for trigger in GEMINI_TRIGGERS:
        if trigger in lower:
            return ModelChoice.GEMINI
    return ModelChoice.GROQ


# ── Groq client ──────────────────────────────────────────────────────
def get_groq_client() -> AsyncGroq:
    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set in .env")
    return AsyncGroq(api_key=settings.GROQ_API_KEY)


# ── Gemini client ────────────────────────────────────────────────────
def get_gemini_client():
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set in .env")
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel("gemini-1.5-flash")


# ── Unified streamed completion ──────────────────────────────────────
async def stream_completion(messages: list[dict], model: ModelChoice | None = None):
    """
    Yields text chunks from the chosen model.
    messages: [{"role": "user"|"assistant"|"system", "content": str}]
    """
    # Auto-route if not specified
    if model is None:
        last_user = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
        )
        model = choose_model(last_user)

    if model == ModelChoice.GROQ:
        async for chunk in _groq_stream(messages):
            yield chunk
    else:
        async for chunk in _gemini_stream(messages):
            yield chunk


async def _groq_stream(messages: list[dict]):
    client = get_groq_client()
    stream = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        stream=True,
        max_tokens=2048,
        temperature=0.7,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


async def _gemini_stream(messages: list[dict]):
    client = get_gemini_client()
    # Convert to Gemini format
    history = []
    system_prompt = ""
    for m in messages:
        if m["role"] == "system":
            system_prompt = m["content"]
        elif m["role"] == "user":
            history.append({"role": "user", "parts": [m["content"]]})
        elif m["role"] == "assistant":
            history.append({"role": "model", "parts": [m["content"]]})

    # Inject system prompt into first user message
    if system_prompt and history and history[0]["role"] == "user":
        history[0]["parts"][0] = f"{system_prompt}\n\n{history[0]['parts'][0]}"

    chat = client.start_chat(history=history[:-1] if len(history) > 1 else [])
    last_user = history[-1]["parts"][0] if history else ""

    response = await chat.send_message_async(last_user, stream=True)
    async for chunk in response:
        if chunk.text:
            yield chunk.text


# ── Single (non-streaming) completion ────────────────────────────────
async def complete(messages: list[dict], model: ModelChoice | None = None) -> str:
    """Non-streaming completion — returns full string."""
    result = []
    async for chunk in stream_completion(messages, model):
        result.append(chunk)
    return "".join(result)
