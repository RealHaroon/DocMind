from typing import Literal

from pydantic import BaseModel


class SummaryRequest(BaseModel):
    style: Literal["concise", "detailed", "key_takeaways"] = "concise"


class SummaryResponse(BaseModel):
    document_id: str
    style: str
    summary: str
    provider: str
    model: str
