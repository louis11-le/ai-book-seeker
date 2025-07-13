from uuid import uuid4

from ai_book_seeker.api.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatSessionResponse,
)
from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.services.langchain_orchestrator import LangChainOrchestrator
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

router = APIRouter()
logger = get_logger(__name__)

# Remove global orchestrator instance


def get_orchestrator(app):
    if not hasattr(app.state, "orchestrator"):
        app.state.orchestrator = LangChainOrchestrator(app)
    return app.state.orchestrator


@router.post("/chat", response_model=ChatSessionResponse)
async def chat(request: ChatRequest, fastapi_request: Request):
    """Chat endpoint powered by LangChainOrchestrator."""
    try:
        logger.info(f"Chat request received: {request.session_id}")
        session_id = request.session_id or str(uuid4())
        logger.info(f"Session ID: {session_id}")
        orchestrator = get_orchestrator(fastapi_request.app)
        result = await orchestrator.process_query(request.message, session_id, interface="chat")
        return ChatSessionResponse(session_id=session_id, response=result)
    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, fastapi_request: Request):
    """Streaming chat endpoint powered by LangChainOrchestrator."""
    try:
        logger.info(f"Streaming chat request received: {request.session_id}")
        session_id = request.session_id or str(uuid4())
        orchestrator = get_orchestrator(fastapi_request.app)

        async def event_generator():
            async for chunk in orchestrator.stream_query(request.message, session_id, interface="chat"):
                # Use Pydantic schema for strict consistency
                yield ChatSessionResponse(
                    session_id=session_id, response=ChatResponse(output=chunk.output)
                ).model_dump_json() + "\n"

        return StreamingResponse(event_generator(), media_type="application/json")
    except Exception as e:
        logger.error(f"Error processing streaming chat request: {e}", exc_info=True)

        def error_stream():
            yield ChatSessionResponse(
                session_id=str(request.session_id or ""), response=ChatResponse(output="Internal server error")
            ).model_dump_json() + "\n"

        return StreamingResponse(error_stream(), media_type="application/json")
