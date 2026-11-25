import json
from collections.abc import Iterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.core.config import Settings, get_settings
from app.db.database import connect
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm.base import ProviderError
from app.services.conversation_service import create_conversation, get_conversation, save_exchange
from app.services.rag_service import SYSTEM, answer_question, build_prompt, finalize_answer, get_provider
from app.services.retrieval_service import retrieve


router = APIRouter(prefix="/chat", tags=["chat"])


def prepare(payload: ChatRequest, settings: Settings):
    ids = list(dict.fromkeys(payload.document_ids))
    with connect(settings) as db:
        rows = db.execute(
            f"SELECT id, status FROM documents WHERE id IN ({','.join('?' for _ in ids)})", ids
        ).fetchall()
        selected = db.execute("SELECT provider, gemini_model, groq_model, rag_top_k FROM app_settings WHERE id = 1").fetchone()
    if len(rows) != len(ids):
        raise HTTPException(404, detail="One or more selected documents were not found.")
    if any(row["status"] != "ready" for row in rows):
        raise HTTPException(409, detail="Wait until all selected documents are ready.")
    conversation = get_conversation(settings, payload.conversation_id) if payload.conversation_id else None
    if payload.conversation_id and conversation is None:
        raise HTTPException(404, detail="Conversation not found.")
    provider = selected["provider"]
    model = selected["gemini_model"] if provider == "gemini" else selected["groq_model"]
    if not (settings.gemini_api_key if provider == "gemini" else settings.groq_api_key):
        raise HTTPException(503, detail=f"{provider.title()} is not configured. Add its API key to backend/.env.")
    try:
        chunks = retrieve(payload.question, ids, selected["rag_top_k"], settings)
        history = ([{"role": msg.role, "content": msg.content} for msg in conversation.messages[-6:]] if conversation else [item for item in payload.history if item.get("role") in ("user", "assistant") and "content" in item])
        return ids, provider, model, chunks, history
    except ProviderError as exc:
        raise HTTPException(exc.status_code, detail=str(exc)) from exc


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, settings: Settings = Depends(get_settings)) -> ChatResponse:
    ids, provider, model, chunks, history = prepare(payload, settings)
    try:
        result = answer_question(payload.question, chunks, provider, model, settings, history)
    except ProviderError as exc:
        raise HTTPException(exc.status_code, detail=str(exc)) from exc
    conversation_id = payload.conversation_id or create_conversation(settings, "New conversation", ids).id
    result.conversation_id = conversation_id
    save_exchange(settings, conversation_id, payload.question, result, ids)
    return result


def _event(name: str, payload: dict) -> str:
    return f"event: {name}\ndata: {json.dumps(payload)}\n\n"


@router.post("/stream")
def stream_chat(payload: ChatRequest, settings: Settings = Depends(get_settings)) -> StreamingResponse:
    ids, provider_name, model, chunks, history = prepare(payload, settings)
    conversation_id = payload.conversation_id or create_conversation(settings, "New conversation", ids).id

    def events() -> Iterator[str]:
        yield _event("start", {"conversation_id": conversation_id})
        if not chunks:
            result = finalize_answer("", chunks, provider_name, model)
        else:
            try:
                provider = get_provider(provider_name, settings)
                parts = []
                for token in provider.stream(SYSTEM, build_prompt(payload.question, chunks, history), model):
                    parts.append(token)
                    yield _event("delta", {"text": token})
                result = finalize_answer("".join(parts), chunks, provider_name, model)
            except ProviderError as exc:
                yield _event("error", {"message": str(exc), "status": exc.status_code})
                return
        result.conversation_id = conversation_id
        save_exchange(settings, conversation_id, payload.question, result, ids)
        yield _event("done", result.model_dump())

    return StreamingResponse(events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
