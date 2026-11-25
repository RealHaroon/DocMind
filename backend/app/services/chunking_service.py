from dataclasses import dataclass

from app.services.pdf_service import PdfPage


@dataclass(frozen=True)
class TextChunk:
    page: int
    text: str
    index: int


def chunk_pages(pages: list[PdfPage], size: int = 800, overlap: int = 120) -> list[TextChunk]:
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("Chunk size must be positive and overlap must be smaller than size.")
    chunks: list[TextChunk] = []
    for page in pages:
        text = " ".join(page.text.split())
        start = 0
        while start < len(text):
            end = min(start + size, len(text))
            if end < len(text):
                boundary = text.rfind(" ", start + size // 2, end)
                if boundary > start:
                    end = boundary
            part = text[start:end].strip()
            if part:
                chunks.append(TextChunk(page.number, part, len(chunks)))
            if end == len(text):
                break
            start = max(start + 1, end - overlap)
    return chunks
