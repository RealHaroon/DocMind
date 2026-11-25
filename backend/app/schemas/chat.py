from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=4000)
    document_ids: list[str] = Field(min_length=1, max_length=20)
    history: list[dict[Literal["role", "content"], str]] = Field(default_factory=list, max_length=12)
    conversation_id: str | None = None


class Citation(BaseModel):
    document_id: str
    filename: str
    page: int
    chunk_id: str
    marker: int


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    provider: str
    model: str
    conversation_id: str | None = None
