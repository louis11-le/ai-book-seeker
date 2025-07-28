from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from ai_book_seeker.api.schemas.chat import ChatResponse
from ai_book_seeker.api.schemas.voice_assistant import VoiceRequest, VoiceResponse
from ai_book_seeker.core.config import AppSettings
from ai_book_seeker.core.dependencies import get_app_settings
from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.workflows.orchestrator import get_orchestrator

logger = get_logger(__name__)

router = APIRouter()


@router.post("/voice", response_model=VoiceResponse)
async def voice(
    request: VoiceRequest,
    fastapi_request: Request,
    x_api_key: str = Header(None),
    settings: AppSettings = Depends(get_app_settings),
):
    """
    Voice assistant endpoint for ElevenLabs integration.

    Accepts voice requests and returns responses using the LangGraph orchestrator.
    Requires valid ElevenLabs API key for authentication.
    """
    session_id = request.session_id or str(uuid4())
    elevenlabs_secret = settings.elevenlabs.api_key.get_secret_value() if settings.elevenlabs.api_key else None

    if x_api_key != elevenlabs_secret:
        logger.warning("[VOICE] Unauthorized access attempt: invalid API key")
        raise HTTPException(status_code=401, detail="Unauthorized")

    logger.info(f'[VOICE] Incoming request: session_id={session_id}, message="{request.message}"')

    try:
        orchestrator = await get_orchestrator(fastapi_request.app)

        from ai_book_seeker.workflows.schemas import get_state_manager

        state_manager = get_state_manager()
        initial_state = state_manager.create_initial_state(
            session_id=session_id, interface="voice", message=request.message, correlation_id=None
        )
        # Execute the workflow
        try:
            final_state = await orchestrator.ainvoke(initial_state, {"configurable": {"thread_id": session_id}})
            # Extract the final response from the state
            messages = final_state.get("messages", [])
            final_message = messages[-1] if messages else None
            result = ChatResponse(output=(final_message.content if final_message else "Sorry, no response generated."))
        except Exception as e:
            logger.error(f"[VOICE] Workflow execution error: {e}", exc_info=True)
            result = ChatResponse(output="Sorry, there was an error processing your request. Please try again.")
        logger.info(f"[VOICE] Outgoing response: session_id={session_id}, status=success")
        return VoiceResponse(session_id=session_id, response=result)
    except Exception as e:
        logger.error(f'[VOICE] Error: session_id={session_id}, error="{str(e)}"', exc_info=True)
        return VoiceResponse(
            session_id=session_id,
            response=ChatResponse(output="Sorry, there was an error processing your request. Please try again."),
        )
