"""
API routes for the AI Book Seeker application.
"""

from fastapi import APIRouter, HTTPException

from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.services.chat_parser import ChatRequest, ChatResponse, process_chat_request
from ai_book_seeker.services.memory import SessionMemory

router = APIRouter()
logger = get_logger(__name__)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint for book recommendations"""
    try:
        # Process the chat request
        response = process_chat_request(request)
        return response
    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from e


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
