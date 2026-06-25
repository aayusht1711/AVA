"""
AVA Memory Agent
Auto-extracts facts from recent chat loops and stores them in ChromaDB.
"""

from datetime import datetime
import json

async def extract_and_store_memory(user_id: str, message: str, response: str):
    # TODO: Use an LLM to extract facts and store them in ChromaDB
    # Format required by frontend Memory Browser:
    # {
    #   "timestamp": "2026-06-20T19:24:13",
    #   "topic": "User Interest",
    #   "content": "Aayush is interested in [X]",
    #   "importance": "high"
    # }
    
    # Placeholder logic
    fact = {
        "timestamp": datetime.now().isoformat(),
        "topic": "General Fact",
        "content": f"User mentioned: {message[:50]}...",
        "importance": "medium"
    }
    
    # In a real implementation, we would insert this into ChromaDB
    # memory_collection.add(
    #     documents=[json.dumps(fact)],
    #     metadatas=[{"user_id": user_id}],
    #     ids=[f"{user_id}_{datetime.now().timestamp()}"]
    # )
    pass
