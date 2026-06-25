from fastapi import APIRouter, Depends, HTTPException
from api.auth import get_current_user
from db.postgres import User
from memory.chroma import get_all_memories, delete_memory

router = APIRouter()

@router.get("/")
async def list_memories(current_user: User = Depends(get_current_user)):
    """List all long-term memories stored in ChromaDB for the user."""
    memories = await get_all_memories(str(current_user.id))
    return {"memories": memories}

@router.delete("/{memory_id}")
async def remove_memory(memory_id: str, current_user: User = Depends(get_current_user)):
    """Delete a specific memory from ChromaDB."""
    success = await delete_memory(str(current_user.id), memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found or deletion failed")
    return {"status": "deleted", "id": memory_id}
