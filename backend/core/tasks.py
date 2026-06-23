import psutil
import asyncio
from api.chat import manager

async def monitor_system_health():
    """
    Monitors CPU and Memory usage.
    If CPU > 90% or RAM > 90%, it broadcasts a proactive warning to all active users.
    """
    cpu_percent = psutil.cpu_percent(interval=1)
    ram_percent = psutil.virtual_memory().percent

    if cpu_percent > 90 or ram_percent > 90:
        warning_msg = f"Sir, I am detecting high system load. CPU: {cpu_percent}%, RAM: {ram_percent}%."
        
        # In a single-user system like Jarvis, we can just broadcast to everyone connected
        for user_id in list(manager.active_connections.keys()):
            await manager.broadcast_to_user(
                user_id,
                {
                    "type": "agent",
                    "agent": "orchestrator"
                }
            )
            await manager.broadcast_to_user(
                user_id,
                {
                    "type": "chunk",
                    "content": warning_msg
                }
            )
            await manager.broadcast_to_user(
                user_id,
                {
                    "type": "done",
                    "agent": "orchestrator"
                }
            )

from agents.memory_builder import build_memory_for_all_users

def setup_tasks(scheduler):
    """Register all background tasks."""
    scheduler.add_job(monitor_system_health, 'interval', minutes=1, id='system_health_monitor')
    scheduler.add_job(build_memory_for_all_users, 'interval', minutes=60, id='memory_builder')
