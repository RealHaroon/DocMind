from pathlib import Path
from unittest.mock import patch

import fitz
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.db.database import initialize_database
from app.main import app
from app.services.chunking_service import chunk_pages
from app.services.pdf_service import PdfPage, PdfValidationError, extract_pages
from app.services.vector_service import add_chunks, collection, delete_chunks


def test_chunking_preserves_page_numbers() -> None:
    chunks = chunk_pages([PdfPage(3, "alpha " * 120), PdfPage(7, "beta " * 120)], 100, 20)
    assert {chunk.page for chunk in chunks} == {3, 7}
    assert all(len(chunk.text) <= 100 for chunk in chunks)
    assert chunks[0].index == 0


def test_extract_text_and_reject_image_only(tmp_path: Path) -> None:
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "Page one has searchable content")
    path = tmp_path / "valid.pdf"
    pdf.save(path)
    pdf.close()
    count, pages = extract_pages(path)
    assert count == 1
    assert pages[0].number == 1
    assert "searchable content" in pages[0].text

    blank = fitz.open()
    blank.new_page()
    blank_path = tmp_path / "blank.pdf"
    blank.save(blank_path)
    blank.close()
    try:
        extract_pages(blank_path)
    except PdfValidationError as exc:
        assert "No selectable text" in str(exc)
    else:
        raise AssertionError("Expected image-only PDF rejection")


def test_upload_list_and_delete(tmp_path: Path) -> None:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'app.db'}",
        upload_path=tmp_path / "uploads",
        chroma_path=tmp_path / "chroma",
    )
    app.dependency_overrides[get_settings] = lambda: settings
    initialize_database(settings)
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "This is a useful document about climate data.")
    payload = pdf.tobytes()
    pdf.close()
    try:
        with patch("app.api.documents.embed_texts", return_value=[[0.1, 0.2]]), patch("app.api.documents.add_chunks") as add, patch("app.api.documents.delete_chunks") as remove:
            with TestClient(app) as client:
                invalid = client.post("/api/documents/upload", files=[("files", ("bad.pdf", b"not a pdf", "application/pdf"))])
                assert invalid.status_code == 415
                response = client.post("/api/documents/upload", files=[("files", ("demo.pdf", payload, "application/pdf"))])
                assert response.status_code == 202
                document_id = response.json()[0]["id"]
                assert client.get(f"/api/documents/{document_id}").json()["status"] == "ready"
                assert len(client.get("/api/documents").json()) == 1
                assert client.get(f"/api/documents/{document_id}/file").content == payload
                assert client.delete(f"/api/documents/{document_id}").status_code == 204
                assert client.get("/api/documents").json() == []
            add.assert_called_once()
            remove.assert_called_once()
    finally:
        app.dependency_overrides.clear()


def test_chroma_persists_page_metadata_and_deletes_only_target(tmp_path: Path) -> None:
    settings = Settings(chroma_path=tmp_path / "vectors")
    chunks = chunk_pages([PdfPage(4, "short source text")])
    add_chunks(settings, "first", "one.pdf", chunks, [[0.1, 0.2]])
    add_chunks(settings, "second", "two.pdf", chunks, [[0.2, 0.1]])
    target = collection(str(settings.resolve_local_path(settings.chroma_path)))
    found = target.get(where={"document_id": "first"}, include=["metadatas"])
    assert found["metadatas"][0]["page"] == 4
    assert found["metadatas"][0]["filename"] == "one.pdf"
    delete_chunks(settings, "first")
    assert target.get(where={"document_id": "first"})["ids"] == []
    assert len(target.get(where={"document_id": "second"})["ids"]) == 1
