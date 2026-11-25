from fastapi import APIRouter, Depends, HTTPException

from app.core.config import Settings, get_settings
from app.db.database import connect
from app.schemas.conversations import ConversationCreate, ConversationRecord, ConversationRename
from app.services.conversation_service import create_conversation, get_conversation, list_conversations


router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationRecord, status_code=201)
def create(payload: ConversationCreate, settings: Settings = Depends(get_settings)) -> ConversationRecord:
    if payload.document_ids:
        with connect(settings) as db:
            count = db.execute(f"SELECT COUNT(*) FROM documents WHERE id IN ({','.join('?' for _ in payload.document_ids)})", payload.document_ids).fetchone()[0]
        if count != len(set(payload.document_ids)):
            raise HTTPException(404, detail="One or more documents were not found.")
    return create_conversation(settings, payload.title, payload.document_ids)


@router.get("", response_model=list[ConversationRecord])
def list_all(settings: Settings = Depends(get_settings)) -> list[ConversationRecord]:
    return list_conversations(settings)


@router.get("/{conversation_id}", response_model=ConversationRecord)
def get_one(conversation_id: str, settings: Settings = Depends(get_settings)) -> ConversationRecord:
    result = get_conversation(settings, conversation_id)
    if result is None:
        raise HTTPException(404, detail="Conversation not found.")
    return result


@router.patch("/{conversation_id}", response_model=ConversationRecord)
def rename(conversation_id: str, payload: ConversationRename, settings: Settings = Depends(get_settings)) -> ConversationRecord:
    with connect(settings) as db:
        cursor = db.execute("UPDATE conversations SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (payload.title.strip(), conversation_id))
    if not cursor.rowcount:
        raise HTTPException(404, detail="Conversation not found.")
    return get_one(conversation_id, settings)


@router.delete("/{conversation_id}", status_code=204)
def delete(conversation_id: str, settings: Settings = Depends(get_settings)) -> None:
    with connect(settings) as db:
        cursor = db.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
    if not cursor.rowcount:
        raise HTTPException(404, detail="Conversation not found.")
