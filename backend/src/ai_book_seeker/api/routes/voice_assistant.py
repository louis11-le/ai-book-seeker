import os
from uuid import uuid4

from ai_book_seeker.api.schemas.chat import ChatResponse
from ai_book_seeker.api.schemas.voice_assistant import VoiceRequest, VoiceResponse
from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.services.langchain_orchestrator import LangChainOrchestrator
from fastapi import APIRouter, Header, HTTPException, Request

logger = get_logger(__name__)

router = APIRouter()
ELEVENLABS_SECRET = os.getenv("ELEVENLABS_WEBHOOK_SECRET")

# @router.post("/webhook/get-book-details", response_model=GetBookDetailsResponse, status_code=status.HTTP_200_OK)
# async def get_book_details(payload: GetBookDetailsRequest, db: Session = Depends(get_db_session)):
#     """
#     Webhook endpoint for ElevenLabs to get comprehensive book details.
#     Accepts a book_id (book title) and returns all relevant book information.
#     """
#     book = db.query(Book).filter(Book.title.ilike(payload.book_id)).first()
#     if book:
#         title = getattr(book, "title", "")
#         author = getattr(book, "author", "")
#         price = float(getattr(book, "price", 0.0))
#         quantity = int(getattr(book, "quantity", 0))
#         description = getattr(book, "description", None)
#         genre = getattr(book, "genre", None)
#         availability = "In Stock" if quantity > 0 else "Out of Stock"
#         return GetBookDetailsResponse(
#             book_id=payload.book_id,
#             title=title,
#             author=author,
#             price=price,
#             quantity=quantity,
#             description=description,
#             genre=genre,
#             availability=availability,
#         )

#     return GetBookDetailsResponse(
#         book_id=payload.book_id,
#         title="",
#         author="",
#         price=0.0,
#         quantity=0,
#         description=None,
#         genre=None,
#         availability="Not Found",
#     )


@router.post("/voice", response_model=VoiceResponse)
async def voice(request: VoiceRequest, fastapi_request: Request, x_api_key: str = Header(None)):
    session_id = request.session_id or str(uuid4())
    if x_api_key != ELEVENLABS_SECRET:
        logger.warning("[VOICE] Unauthorized access attempt: invalid API key")
        raise HTTPException(status_code=401, detail="Unauthorized")

    logger.info(f'[VOICE] Incoming request: session_id={session_id}, message="{request.message}"')
    try:
        orchestrator = LangChainOrchestrator(fastapi_request.app)
        result_chunks = [
            chunk async for chunk in orchestrator.stream_query(request.message, session_id, interface="voice")
        ]
        result = result_chunks[-1] if result_chunks else ChatResponse(output="Sorry, no response generated.")
        logger.info(f"[VOICE] Outgoing response: session_id={session_id}, status=success")
        return VoiceResponse(session_id=session_id, response=result)
    except Exception as e:
        logger.error(f'[VOICE] Error: session_id={session_id}, error="{str(e)}"', exc_info=True)
        return VoiceResponse(
            session_id=session_id,
            response=ChatResponse(output="Sorry, there was an error processing your request. Please try again."),
        )
