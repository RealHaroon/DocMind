from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.db.database import connect, initialize_database
from app.main import app
from app.services.chunking_service import TextChunk
from app.services.vector_service import add_chunks


def test_conversation_create_rename_restore_delete(tmp_path: Path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'app.db'}")
    initialize_database(settings)
    app.dependency_overrides[get_settings] = lambda: settings
    try:
        with TestClient(app) as client:
            created = client.post("/api/conversations", json={"title": "Research"})
            assert created.status_code == 201
            conversation_id = created.json()["id"]
            assert client.get("/api/conversations").json()[0]["title"] == "Research"
            assert client.patch(f"/api/conversations/{conversation_id}", json={"title": "Renamed"}).json()["title"] == "Renamed"
            assert client.get(f"/api/conversations/{conversation_id}").json()["messages"] == []
            assert client.delete(f"/api/conversations/{conversation_id}").status_code == 204
            assert client.get(f"/api/conversations/{conversation_id}").status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_stream_saves_answer_and_citation(tmp_path: Path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'app.db'}", chroma_path=tmp_path / "chroma", gemini_api_key="test-key")
    initialize_database(settings)
    with connect(settings) as db:
        db.execute("INSERT INTO documents (id, filename, stored_name, size_bytes, status, page_count) VALUES ('first', 'paper.pdf', 'first.pdf', 10, 'ready', 4)")
    add_chunks(settings, "first", "paper.pdf", [TextChunk(4, "The result was positive.", 0)], [[1.0, 0.0]])
    app.dependency_overrides[get_settings] = lambda: settings
    try:
        with patch("app.services.retrieval_service.embed_texts", return_value=[[1.0, 0.0]]), patch("app.api.chat.get_provider") as provider:
            provider.return_value.stream.return_value = iter(["The result ", "was positive. [1]"])
            with TestClient(app) as client:
                response = client.post("/api/chat/stream", json={"question": "What was the result?", "document_ids": ["first"]})
                assert response.status_code == 200
                assert "event: delta" in response.text
                assert "event: done" in response.text
                conversation = client.get("/api/conversations").json()[0]
                restored = client.get(f"/api/conversations/{conversation['id']}").json()
                assert len(restored["messages"]) == 2
                assert restored["messages"][1]["citations"][0]["page"] == 4
    finally:
        app.dependency_overrides.clear()


def test_summary_batches_long_document(tmp_path: Path) -> None:
    settings = Settings(chroma_path=tmp_path / "chroma")
    chunks = [TextChunk(i + 1, f"Page {i + 1} discusses result {i}.", i) for i in range(23)]
    add_chunks(settings, "long", "long.pdf", chunks, [[1.0, 0.0] for _ in chunks])
    with patch("app.services.summary_service.get_provider") as provider:
        provider.return_value.generate.return_value = "Summary text."
        from app.services.summary_service import summarize_document
        result = summarize_document("long", "concise", "gemini", "model", settings)
    assert result == "Summary text."
    assert provider.return_value.generate.call_count == 4
