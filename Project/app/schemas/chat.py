"""对话 Schema"""
from pydantic import BaseModel
from typing import Optional


class ChatMessageReq(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    user_context: Optional[dict] = None


class ChatMessageResp(BaseModel):
    conversation_id: Optional[str] = None
    answer: str
    intent: Optional[str] = None
    agent: Optional[str] = None
    suggested_questions: list[str] = []
