from typing import Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    output: str


class ChatSessionResponse(BaseModel):
    session_id: str
    response: ChatResponse
