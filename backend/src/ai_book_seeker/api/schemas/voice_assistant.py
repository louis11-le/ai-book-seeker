from typing import Optional

from ai_book_seeker.api.schemas.chat import ChatResponse
from pydantic import BaseModel


class GetBookDetailsRequest(BaseModel):
    book_id: str


class GetBookDetailsResponse(BaseModel):
    book_id: str
    title: str
    author: str
    price: float
    quantity: int
    description: Optional[str] = None
    genre: Optional[str] = None
    availability: str


class VoiceRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class VoiceResponse(BaseModel):
    session_id: str
    response: ChatResponse
