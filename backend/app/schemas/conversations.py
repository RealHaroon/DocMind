from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.chat import Citation


class ConversationCreate(BaseModel):
    title: str = Field(default="New conversation", min_length=1, max_length=120)
    document_ids: list[str] = Field(default_factory=list, max_length=20)


class ConversationRename(BaseModel):
    title: str = Field(min_length=1, max_length=120)


class MessageRecord(BaseModel):
    id: str
    role: str
    content: str
    citations: list[Citation]
    created_at: datetime


class ConversationRecord(BaseModel):
    id: str
    title: str
    document_ids: list[str]
    created_at: datetime
    updated_at: datetime
    messages: list[MessageRecord] = []
