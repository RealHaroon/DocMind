from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: str
    filename: str
    page_count: int
    size_bytes: int
    status: Literal["processing", "ready", "failed"]
    error: str | None
    uploaded_at: datetime
