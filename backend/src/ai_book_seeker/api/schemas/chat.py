from typing import Dict, List, Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    output: str
    data: Optional[List[Dict]] = None


class ChatSessionResponse(BaseModel):
    session_id: str
    response: ChatResponse
