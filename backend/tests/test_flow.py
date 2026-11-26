from pathlib import Path
from unittest.mock import patch

import pymupdf as fitz
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.db.database import initialize_database
from app.main import app
from app.services.vector_service import collection


def test_upload_chat_restore_and_delete_flow(tmp_path: Path) -> None:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'flow.db'}",
        upload_path=tmp_path / "uploads",
        chroma_path=tmp_path / "chroma",
        gemini_api_key="test-key",
    )
    initialize_database(settings)
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "Binary search repeatedly halves a sorted search space.")
    content = pdf.tobytes()
    pdf.close()
    app.dependency_overrides[get_settings] = lambda: settings
    try:
        with patch("app.api.documents.embed_texts", return_value=[[1.0, 0.0]]), patch(
            "app.services.retrieval_service.embed_texts", return_value=[[1.0, 0.0]]
        ), patch("app.api.chat.get_provider") as provider:
            provider.return_value.stream.return_value = iter(
                ["Binary search halves a sorted search space. [1]"]
            )
            with TestClient(app) as client:
                upload = client.post(
                    "/api/documents/upload",
                    files=[("files", ("algorithm.pdf", content, "application/pdf"))],
                )
                assert upload.status_code == 202
                document_id = upload.json()[0]["id"]
                assert client.get(f"/api/documents/{document_id}").json()["status"] == "ready"

                response = client.post(
                    "/api/chat/stream",
                    json={"question": "How does binary search work?", "document_ids": [document_id]},
                )
                assert response.status_code == 200
                assert '"page": 1' in response.text
                conversation_id = client.get("/api/conversations").json()[0]["id"]
                saved = client.get(f"/api/conversations/{conversation_id}").json()
                assert saved["document_ids"] == [document_id]
                assert saved["messages"][1]["citations"][0]["document_id"] == document_id

                assert client.delete(f"/api/documents/{document_id}").status_code == 204
                assert client.get(f"/api/documents/{document_id}").status_code == 404
                assert collection(str(settings.resolve_local_path(settings.chroma_path))).get(
                    where={"document_id": document_id}
                )["ids"] == []
                assert client.get(f"/api/conversations/{conversation_id}").json()["document_ids"] == []
    finally:
        app.dependency_overrides.clear()
