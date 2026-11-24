from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    app_name: str = "DocMind API"
    app_version: str = "0.1.0"
    environment: str = "development"

    gemini_api_key: str = Field(default="", repr=False)
    groq_api_key: str = Field(default="", repr=False)
    gemini_model: str = "gemini-3.5-flash-lite"
    groq_model: str = "openai/gpt-oss-20b"
    default_llm_provider: Literal["gemini", "groq"] = "gemini"

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chroma_path: Path = Path("../storage/chroma")
    upload_path: Path = Path("../storage/uploads")
    database_url: str = "sqlite:///./docmind.db"
    max_upload_size_mb: int = Field(default=20, ge=1, le=200)
    rag_top_k: int = Field(default=5, ge=1, le=20)

    allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def resolve_local_path(self, value: Path) -> Path:
        return value if value.is_absolute() else (BACKEND_DIR / value).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()

