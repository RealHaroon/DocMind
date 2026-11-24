from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ProviderName = Literal["gemini", "groq"]
ThemeName = Literal["dark", "light", "system"]


class AppSettingsResponse(BaseModel):
    provider: ProviderName
    gemini_model: str
    groq_model: str
    rag_top_k: int
    theme: ThemeName
    provider_configured: bool


class AppSettingsUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    provider: ProviderName
    gemini_model: str = Field(min_length=1, max_length=100)
    groq_model: str = Field(min_length=1, max_length=100)
    rag_top_k: int = Field(ge=1, le=20)
    theme: ThemeName

