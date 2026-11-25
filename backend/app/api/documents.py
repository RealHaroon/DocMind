import asyncio
import logging
import threading
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.core.config import Settings, get_settings
from app.db.database import connect
from app.schemas.documents import DocumentResponse
from app.schemas.summaries import SummaryRequest, SummaryResponse
from app.services.llm.base import ProviderError
from app.services.summary_service import summarize_document
from app.services.chunking_service import chunk_pages
from app.services.embedding_service import embed_texts
from app.services.pdf_service import PdfValidationError, extract_pages
from app.services.vector_service import add_chunks, delete_chunks


router = APIRouter(prefix="/documents", tags=["documents"])
logger = logging.getLogger(__name__)
processing_lock = threading.Lock()


def _document(row: object) -> DocumentResponse:
    return DocumentResponse.model_validate(dict(row))  # type: ignore[arg-type]


def process_document(document_id: str, filename: str, path: Path, settings: Settings) -> None:
    with processing_lock:
        try:
            page_count, pages = extract_pages(path)
            chunks = chunk_pages(pages, settings.chunk_size, settings.chunk_overlap)
            vectors = embed_texts([chunk.text for chunk in chunks], settings.embedding_model)
            add_chunks(settings, document_id, filename, chunks, vectors)
            with connect(settings) as db:
                db.execute("UPDATE documents SET page_count = ?, status = 'ready', error = NULL WHERE id = ?", (page_count, document_id))
        except Exception as exc:
            logger.exception("Document processing failed for %s", document_id)
            try:
                delete_chunks(settings, document_id)
            except Exception:
                logger.exception("Could not clear partial vectors for %s", document_id)
            with connect(settings) as db:
                db.execute("UPDATE documents SET status = 'failed', error = ? WHERE id = ?", (str(exc)[:300], document_id))


@router.post("/upload", response_model=list[DocumentResponse], status_code=202)
async def upload_documents(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    settings: Settings = Depends(get_settings),
) -> list[DocumentResponse]:
    if not files or len(files) > 10:
        raise HTTPException(400, detail="Upload between 1 and 10 PDFs at a time.")
    results: list[DocumentResponse] = []
    upload_dir = settings.resolve_local_path(settings.upload_path)
    upload_dir.mkdir(parents=True, exist_ok=True)
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    for file in files:
        filename = Path(file.filename or "").name
        if not filename.lower().endswith(".pdf"):
            for created in results:
                with connect(settings) as db:
                    db.execute("DELETE FROM documents WHERE id = ?", (created.id,))
                (upload_dir / f"{created.id}.pdf").unlink(missing_ok=True)
            raise HTTPException(415, detail="Only PDF files are accepted.")
        document_id = uuid4().hex
        stored_name = f"{document_id}.pdf"
        path = upload_dir / stored_name
        total = 0
        try:
            with path.open("wb") as target:
                first = await file.read(65536)
                if not first.startswith(b"%PDF-"):
                    raise HTTPException(415, detail=f"{filename}: invalid PDF signature.")
                while first:
                    total += len(first)
                    if total > max_bytes:
                        raise HTTPException(413, detail=f"{filename}: exceeds {settings.max_upload_size_mb} MB limit.")
                    target.write(first)
                    first = await file.read(65536)
            try:
                page_count, _ = await asyncio.to_thread(extract_pages, path)
            except PdfValidationError as exc:
                raise HTTPException(422, detail=f"{filename}: {exc}") from exc
            with connect(settings) as db:
                db.execute(
                    "INSERT INTO documents (id, filename, stored_name, page_count, size_bytes, status) VALUES (?, ?, ?, ?, ?, 'processing')",
                    (document_id, filename, stored_name, page_count, total),
                )
                row = db.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
            results.append(_document(row))
            background_tasks.add_task(process_document, document_id, filename, path, settings)
        except Exception:
            path.unlink(missing_ok=True)
            for created in results:
                with connect(settings) as db:
                    db.execute("DELETE FROM documents WHERE id = ?", (created.id,))
                (upload_dir / f"{created.id}.pdf").unlink(missing_ok=True)
            raise
        finally:
            await file.close()
    return results


@router.get("", response_model=list[DocumentResponse])
def list_documents(settings: Settings = Depends(get_settings)) -> list[DocumentResponse]:
    with connect(settings) as db:
        rows = db.execute("SELECT * FROM documents ORDER BY uploaded_at DESC, rowid DESC").fetchall()
    return [_document(row) for row in rows]


def _find(document_id: str, settings: Settings):
    with connect(settings) as db:
        row = db.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
    if row is None:
        raise HTTPException(404, detail="Document not found.")
    return row


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str, settings: Settings = Depends(get_settings)) -> DocumentResponse:
    return _document(_find(document_id, settings))


@router.get("/{document_id}/file")
def get_document_file(document_id: str, settings: Settings = Depends(get_settings)) -> FileResponse:
    row = _find(document_id, settings)
    path = settings.resolve_local_path(settings.upload_path) / row["stored_name"]
    if not path.is_file():
        raise HTTPException(404, detail="Document file is unavailable.")
    return FileResponse(path, media_type="application/pdf", filename=row["filename"], content_disposition_type="inline")


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: str, settings: Settings = Depends(get_settings)) -> None:
    row = _find(document_id, settings)
    with processing_lock:
        delete_chunks(settings, document_id)
        with connect(settings) as db:
            db.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        (settings.resolve_local_path(settings.upload_path) / row["stored_name"]).unlink(missing_ok=True)


@router.post("/{document_id}/summarize", response_model=SummaryResponse)
def summarize(document_id: str, payload: SummaryRequest, settings: Settings = Depends(get_settings)) -> SummaryResponse:
    document = _find(document_id, settings)
    if document["status"] != "ready":
        raise HTTPException(409, detail="Wait until the document is ready.")
    with connect(settings) as db:
        selected = db.execute("SELECT provider, gemini_model, groq_model FROM app_settings WHERE id = 1").fetchone()
    provider = selected["provider"]
    model = selected["gemini_model"] if provider == "gemini" else selected["groq_model"]
    try:
        summary = summarize_document(document_id, payload.style, provider, model, settings)
    except ProviderError as exc:
        raise HTTPException(exc.status_code, detail=str(exc)) from exc
    return SummaryResponse(document_id=document_id, style=payload.style, summary=summary, provider=provider, model=model)
