from pathlib import Path
from unittest.mock import patch

import httpx
import groq
from fastapi.testclient import TestClient
from google.genai import errors as genai_errors

from app.core.config import Settings, get_settings
from app.db.database import initialize_database, connect
from app.main import app
from app.services.chunking_service import TextChunk
from app.services.llm.base import ProviderError
from app.services.llm.gemini import GeminiProvider
from app.services.llm.groq import GroqProvider
from app.services.rag_service import NO_ANSWER, answer_question
from app.services.retrieval_service import RetrievedChunk, retrieve
from app.services.vector_service import add_chunks


def sample_chunk() -> RetrievedChunk:
    return RetrievedChunk("first:0", "first", "paper.pdf", 12, "The treatment group improved by 20 percent.", 0.1)


def test_retrieval_filters_unselected_documents(tmp_path: Path) -> None:
    settings = Settings(chroma_path=tmp_path / "vectors")
    add_chunks(settings, "first", "paper.pdf", [TextChunk(12, "Treatment improved by 20 percent", 0)], [[1.0, 0.0]])
    add_chunks(settings, "second", "secret.pdf", [TextChunk(3, "Treatment improved by 21 percent", 0)], [[0.99, 0.01]])
    with patch("app.services.retrieval_service.embed_texts", return_value=[[1.0, 0.0]]):
        found = retrieve("What improved?", ["first"], 5, settings)
    assert len(found) == 1
    assert found[0].document_id == "first"
    assert found[0].page == 12


def test_citations_only_from_retrieved_chunks() -> None:
    settings = Settings(gemini_api_key="test-key")
    with patch("app.services.rag_service.GeminiProvider") as provider:
        provider.return_value.generate.return_value = "The treatment improved by 20 percent. [1]"
        response = answer_question("What happened?", [sample_chunk()], "gemini", "test-model", settings)
        assert response.citations[0].page == 12
        assert response.citations[0].filename == "paper.pdf"
        provider.return_value.generate.return_value = "An unrelated claim. [2]"
        rejected = answer_question("What happened?", [sample_chunk()], "gemini", "test-model", settings)
        assert rejected.answer == NO_ANSWER
        assert rejected.citations == []


def test_chat_requires_ready_selected_documents(tmp_path: Path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'chat.db'}")
    initialize_database(settings)
    with connect(settings) as db:
        db.execute("INSERT INTO documents (id, filename, stored_name, size_bytes, status) VALUES ('first', 'paper.pdf', 'first.pdf', 10, 'processing')")
    app.dependency_overrides[get_settings] = lambda: settings
    try:
        with TestClient(app) as client:
            missing = client.post("/api/chat", json={"question": "What happened?", "document_ids": ["missing"]})
            assert missing.status_code == 404
            pending = client.post("/api/chat", json={"question": "What happened?", "document_ids": ["first"]})
            assert pending.status_code == 409
    finally:
        app.dependency_overrides.clear()


def test_provider_not_configured_and_error_mapping() -> None:
    with patch("app.services.rag_service.GeminiProvider", side_effect=ProviderError("Missing key", 503)):
        try:
            answer_question("Question?", [sample_chunk()], "gemini", "model", Settings())
        except ProviderError as exc:
            assert exc.status_code == 503
        else:
            raise AssertionError("Expected provider error")


def test_gemini_quota_error_is_actionable() -> None:
    with patch("app.services.llm.gemini.genai.Client") as client:
        client.return_value.models.generate_content.side_effect = genai_errors.ClientError(429, {"error": {"message": "quota"}})
        provider = GeminiProvider("test-key")
        try:
            provider.generate("system", "prompt", "test-model")
        except ProviderError as exc:
            assert exc.status_code == 429
            assert "quota" in str(exc).lower()
        else:
            raise AssertionError("Expected quota error")


def test_groq_rate_limit_error_is_actionable() -> None:
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    response = httpx.Response(429, request=request)
    with patch("app.services.llm.groq.groq.Groq") as client:
        client.return_value.chat.completions.create.side_effect = groq.RateLimitError("limit", response=response, body=None)
        provider = GroqProvider("test-key")
        try:
            provider.generate("system", "prompt", "test-model")
        except ProviderError as exc:
            assert exc.status_code == 429
            assert "rate limit" in str(exc).lower()
        else:
            raise AssertionError("Expected rate limit error")


def test_chat_api_returns_structured_source_for_selected_pdf(tmp_path: Path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'chat.db'}", chroma_path=tmp_path / "vectors", gemini_api_key="test-key")
    initialize_database(settings)
    with connect(settings) as db:
        db.execute("INSERT INTO documents (id, filename, stored_name, size_bytes, status, page_count) VALUES ('first', 'paper.pdf', 'first.pdf', 10, 'ready', 12)")
    add_chunks(settings, "first", "paper.pdf", [TextChunk(12, "Treatment improved by 20 percent", 0)], [[1.0, 0.0]])
    app.dependency_overrides[get_settings] = lambda: settings
    try:
        with patch("app.services.retrieval_service.embed_texts", return_value=[[1.0, 0.0]]), patch("app.services.rag_service.GeminiProvider") as provider:
            provider.return_value.generate.return_value = "The treatment improved by 20 percent. [1]"
            with TestClient(app) as client:
                response = client.post("/api/chat", json={"question": "What changed?", "document_ids": ["first"]})
        assert response.status_code == 200
        assert response.json()["citations"] == [{"document_id": "first", "filename": "paper.pdf", "page": 12, "chunk_id": "first:0", "marker": 1}]
    finally:
        app.dependency_overrides.clear()
