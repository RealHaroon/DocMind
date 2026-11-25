from functools import lru_cache

import chromadb

from app.core.config import Settings
from app.services.chunking_service import TextChunk


@lru_cache(maxsize=4)
def collection(path: str):
    client = chromadb.PersistentClient(path=path)
    return client.get_or_create_collection(name="document_chunks", metadata={"hnsw:space": "cosine"})


def add_chunks(settings: Settings, document_id: str, filename: str, chunks: list[TextChunk], vectors: list[list[float]]) -> None:
    if len(chunks) != len(vectors):
        raise ValueError("Chunk and embedding counts differ.")
    target = collection(str(settings.resolve_local_path(settings.chroma_path)))
    for offset in range(0, len(chunks), 64):
        batch = chunks[offset:offset + 64]
        target.add(
            ids=[f"{document_id}:{chunk.index}" for chunk in batch],
            documents=[chunk.text for chunk in batch],
            embeddings=vectors[offset:offset + 64],
            metadatas=[{"document_id": document_id, "filename": filename, "page": chunk.page} for chunk in batch],
        )


def delete_chunks(settings: Settings, document_id: str) -> None:
    collection(str(settings.resolve_local_path(settings.chroma_path))).delete(where={"document_id": document_id})
