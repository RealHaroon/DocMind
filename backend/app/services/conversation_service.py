import json
from uuid import uuid4

from app.core.config import Settings
from app.db.database import connect
from app.schemas.chat import ChatResponse
from app.schemas.conversations import ConversationRecord, MessageRecord


def list_conversations(settings: Settings) -> list[ConversationRecord]:
    with connect(settings) as db:
        rows = db.execute("SELECT * FROM conversations ORDER BY updated_at DESC, rowid DESC").fetchall()
        links = db.execute("SELECT conversation_id, document_id FROM conversation_documents").fetchall()
    documents: dict[str, list[str]] = {}
    for link in links:
        documents.setdefault(link["conversation_id"], []).append(link["document_id"])
    return [ConversationRecord(id=row["id"], title=row["title"], document_ids=documents.get(row["id"], []), created_at=row["created_at"], updated_at=row["updated_at"]) for row in rows]


def get_conversation(settings: Settings, conversation_id: str) -> ConversationRecord | None:
    with connect(settings) as db:
        row = db.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,)).fetchone()
        if row is None:
            return None
        links = db.execute("SELECT document_id FROM conversation_documents WHERE conversation_id = ?", (conversation_id,)).fetchall()
        messages = db.execute("SELECT * FROM messages WHERE conversation_id = ? ORDER BY rowid", (conversation_id,)).fetchall()
    return ConversationRecord(
        id=row["id"], title=row["title"], document_ids=[link["document_id"] for link in links],
        created_at=row["created_at"], updated_at=row["updated_at"],
        messages=[MessageRecord(id=msg["id"], role=msg["role"], content=msg["content"], citations=json.loads(msg["citations_json"]), created_at=msg["created_at"]) for msg in messages],
    )


def create_conversation(settings: Settings, title: str, document_ids: list[str]) -> ConversationRecord:
    conversation_id = uuid4().hex
    with connect(settings) as db:
        db.execute("INSERT INTO conversations (id, title) VALUES (?, ?)", (conversation_id, title.strip()[:120] or "New conversation"))
        db.executemany("INSERT INTO conversation_documents (conversation_id, document_id) VALUES (?, ?)", [(conversation_id, doc) for doc in dict.fromkeys(document_ids)])
    result = get_conversation(settings, conversation_id)
    assert result is not None
    return result


def save_exchange(settings: Settings, conversation_id: str, question: str, answer: ChatResponse, document_ids: list[str]) -> None:
    with connect(settings) as db:
        db.executemany("INSERT OR IGNORE INTO conversation_documents (conversation_id, document_id) VALUES (?, ?)", [(conversation_id, doc) for doc in dict.fromkeys(document_ids)])
        db.execute("INSERT INTO messages (id, conversation_id, role, content) VALUES (?, ?, 'user', ?)", (uuid4().hex, conversation_id, question))
        db.execute("INSERT INTO messages (id, conversation_id, role, content, citations_json) VALUES (?, ?, 'assistant', ?, ?)", (uuid4().hex, conversation_id, answer.answer, json.dumps([cite.model_dump() for cite in answer.citations])))
        db.execute("UPDATE conversations SET updated_at = CURRENT_TIMESTAMP, title = CASE WHEN title = 'New conversation' THEN ? ELSE title END WHERE id = ?", (question[:80], conversation_id))
