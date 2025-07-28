from typing import Any, Dict, Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    output: str
    data: Optional[Dict[str, Any]] = None


class ChatSessionResponse(BaseModel):
    session_id: str
    response: ChatResponse


class EnhancedChatSessionResponse(ChatSessionResponse):
    """Enhanced chat session response with correlation ID for tracing."""

    correlation_id: Optional[str] = None
