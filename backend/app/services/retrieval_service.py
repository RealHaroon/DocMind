from dataclasses import dataclass

from app.core.config import Settings
from app.services.embedding_service import embed_texts
from app.services.vector_service import collection


@dataclass(frozen=True)
class RetrievedChunk:
    id: str
    document_id: str
    filename: str
    page: int
    text: str
    distance: float


def retrieve(question: str, document_ids: list[str], top_k: int, settings: Settings) -> list[RetrievedChunk]:
    if not document_ids:
        return []
    vector = embed_texts([question], settings.embedding_model)[0]
    target = collection(str(settings.resolve_local_path(settings.chroma_path)))
    result = target.query(
        query_embeddings=[vector],
        n_results=top_k,
        where={"document_id": {"$in": document_ids}},
        include=["documents", "metadatas", "distances"],
    )
    chunks = []
    for chunk_id, text, metadata, distance in zip(
        result["ids"][0], result["documents"][0], result["metadatas"][0], result["distances"][0]
    ):
        if metadata["document_id"] not in document_ids or not text.strip():
            continue
        chunks.append(RetrievedChunk(chunk_id, metadata["document_id"], metadata["filename"], int(metadata["page"]), text, float(distance)))
    return chunks
