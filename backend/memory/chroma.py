"""
AVA Memory — ChromaDB Vector Store
Stores long-term memories per user.
Each memory = a text chunk embedded and stored with metadata.
"""

import chromadb
from chromadb.config import Settings as ChromaSettings
import uuid
from datetime import datetime
from core.config import settings


def get_chroma_client() -> chromadb.AsyncHttpClient:
    return chromadb.AsyncHttpClient(
        host=settings.CHROMA_HOST,
        port=settings.CHROMA_PORT,
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def _collection_name(user_id: str) -> str:
    """Each user gets their own collection."""
    return f"ava_user_{user_id.replace('-', '_')}"


async def store_memory(user_id: str, content: str, metadata: dict | None = None) -> str:
    """
    Store a memory for a user.
    Returns the memory ID.
    """
    client = get_chroma_client()
    collection = await client.get_or_create_collection(
        name=_collection_name(user_id),
        metadata={"hnsw:space": "cosine"},
    )

    memory_id = str(uuid.uuid4())
    await collection.add(
        ids=[memory_id],
        documents=[content],
        metadatas=[{
            "user_id":    user_id,
            "created_at": datetime.utcnow().isoformat(),
            **(metadata or {}),
        }],
    )
    return memory_id


async def recall_memories(
    user_id: str,
    query: str,
    n_results: int = 5,
) -> list[dict]:
    """
    Retrieve most relevant memories for a query.
    Returns list of { content, metadata, distance }
    """
    client = get_chroma_client()

    try:
        collection = await client.get_collection(_collection_name(user_id))
    except Exception:
        return []  # No memories yet

    results = await collection.query(
        query_texts=[query],
        n_results=min(n_results, await collection.count()),
    )

    memories = []
    if results["documents"] and results["documents"][0]:
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            memories.append({
                "content":  doc,
                "metadata": meta,
                "distance": round(dist, 4),
            })

    return memories


async def delete_user_memories(user_id: str) -> bool:
    """Delete all memories for a user (GDPR)."""
    client = get_chroma_client()
    try:
        await client.delete_collection(_collection_name(user_id))
        return True
    except Exception:
        return False


async def format_memories_for_context(user_id: str, query: str) -> str:
    """
    Retrieve memories and format them as context for the LLM.
    Returns empty string if no memories found.
    """
    memories = await recall_memories(user_id, query, n_results=5)
    if not memories:
        return ""

    lines = ["[Relevant memories about this user:]"]
    for m in memories:
        lines.append(f"- {m['content']}")
    return "\n".join(lines)
