"""
AVA Deep Entity-Based Memory
Periodically reads recent chat sessions, extracts long-term facts using Gemini,
and stores them as permanent context for the user.
"""

from db.postgres import AsyncSessionLocal, User, ChatSession, Message
from memory.chroma import store_memory
from agents.router import complete, ModelChoice
from sqlalchemy import select
from datetime import datetime, timedelta

async def build_memory_for_all_users():
    """
    Background job to build memory for all users based on recent messages.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        # Consider messages from the last 24 hours
        yesterday = datetime.utcnow() - timedelta(days=1)

        for user in users:
            msgs_result = await session.execute(
                select(Message)
                .join(ChatSession)
                .where(ChatSession.user_id == user.id)
                .where(Message.created_at >= yesterday)
                .order_by(Message.created_at)
            )
            recent_msgs = msgs_result.scalars().all()
            
            if not recent_msgs:
                continue
                
            # Create a transcript
            transcript = "\n".join([f"{m.role}: {m.content}" for m in recent_msgs])
            
            system_prompt = (
                "You are the memory extraction module for AVA. "
                "Read the following chat transcript and extract any NEW long-term facts, "
                "preferences, or entities about the user. Output ONLY the extracted facts, "
                "one per line. If there are no new facts to remember, output 'NONE'."
            )
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Transcript:\n{transcript}"}
            ]
            
            extracted = await complete(messages, model=ModelChoice.GEMINI)
            
            if extracted and "NONE" not in extracted.upper():
                facts = extracted.strip().split("\n")
                for fact in facts:
                    if fact.strip():
                        await store_memory(
                            user.id,
                            f"User Fact: {fact.strip()}",
                            {"type": "entity_extraction", "source": "reflection"}
                        )
