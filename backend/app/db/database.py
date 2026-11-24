import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from app.core.config import Settings


SCHEMA = """
CREATE TABLE IF NOT EXISTS app_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    provider TEXT NOT NULL CHECK (provider IN ('gemini', 'groq')),
    gemini_model TEXT NOT NULL,
    groq_model TEXT NOT NULL,
    rag_top_k INTEGER NOT NULL CHECK (rag_top_k BETWEEN 1 AND 20),
    theme TEXT NOT NULL CHECK (theme IN ('dark', 'light', 'system')),
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def database_path(database_url: str) -> Path:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise ValueError("Phase 1 supports only sqlite:/// database URLs")
    raw_path = Path(database_url.removeprefix(prefix))
    return raw_path if raw_path.is_absolute() else Path.cwd() / raw_path


def initialize_database(settings: Settings) -> None:
    path = database_path(settings.database_url)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.executescript(SCHEMA)
        connection.execute(
            """
            INSERT OR IGNORE INTO app_settings
                (id, provider, gemini_model, groq_model, rag_top_k, theme)
            VALUES (1, ?, ?, ?, ?, 'dark')
            """,
            (
                settings.default_llm_provider,
                settings.gemini_model,
                settings.groq_model,
                settings.rag_top_k,
            ),
        )


@contextmanager
def connect(settings: Settings) -> Generator[sqlite3.Connection, None, None]:
    connection = sqlite3.connect(database_path(settings.database_url))
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()

