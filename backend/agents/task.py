"""
AVA Task Agent
Manages reminders and to-dos via APScheduler.
"""

def needs_task(content: str) -> bool:
    lower = content.lower()
    return any(word in lower for word in ["remind me", "task", "list"])

async def handle_task(request: str, history: list[dict]) -> dict:
    # TODO: Implement APScheduler parsing
    return {"final_response": "I have noted your task. (Task agent placeholder)"}
