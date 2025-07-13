from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.services.memory import SessionMemory
from fastapi import APIRouter, HTTPException

router = APIRouter()
logger = get_logger(__name__)


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    try:
        SessionMemory.delete_session(session_id)
        logger.info(f"Session {session_id} deleted successfully")
        return {"status": "ok", "message": "Session deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from e
