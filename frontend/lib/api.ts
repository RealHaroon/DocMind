export const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export type HealthResponse = {
  status: string;
  service: string;
  version: string;
  timestamp: string;
};

export type AppSettings = {
  provider: "gemini" | "groq";
  gemini_model: string;
  groq_model: string;
  rag_top_k: number;
  theme: "dark" | "light" | "system";
  provider_configured: boolean;
};

export type DocumentRecord = {
  id: string;
  filename: string;
  page_count: number;
  size_bytes: number;
  status: "processing" | "ready" | "failed";
  error: string | null;
  uploaded_at: string;
};

export async function fetchDocuments(): Promise<DocumentRecord[]> {
  const response = await fetch(`${API_URL}/api/documents`, { cache: "no-store" });
  if (!response.ok) throw new Error("Could not load documents");
  return response.json();
}

export async function uploadDocuments(files: File[]): Promise<DocumentRecord[]> {
  const body = new FormData();
  files.forEach((file) => body.append("files", file));
  const response = await fetch(`${API_URL}/api/documents/upload`, { method: "POST", body });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(typeof payload.detail === "string" ? payload.detail : "Upload failed");
  }
  return response.json();
}

export async function deleteDocument(id: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/documents/${id}`, { method: "DELETE" });
  if (!response.ok) throw new Error("Could not delete document");
}

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_URL}/api/health`, { cache: "no-store" });
  if (!response.ok) throw new Error("Backend is unavailable");
  return response.json();
}

export async function fetchSettings(): Promise<AppSettings> {
  const response = await fetch(`${API_URL}/api/settings`, { cache: "no-store" });
  if (!response.ok) throw new Error("Could not load settings");
  return response.json();
}

export async function updateSettings(settings: Omit<AppSettings, "provider_configured">): Promise<AppSettings> {
  const response = await fetch(`${API_URL}/api/settings`, {
    method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(settings),
  });
  if (!response.ok) throw new Error("Could not save settings");
  return response.json();
}

export type Citation = { document_id: string; filename: string; page: number; chunk_id: string; marker: number };
export type ChatAnswer = { answer: string; citations: Citation[]; provider: string; model: string };
export type ChatResult = ChatAnswer & { conversation_id: string | null };
export type MessageRecord = { id: string; role: "user" | "assistant"; content: string; citations: Citation[]; created_at: string };
export type ConversationRecord = { id: string; title: string; document_ids: string[]; created_at: string; updated_at: string; messages: MessageRecord[] };

export async function fetchConversations(): Promise<ConversationRecord[]> {
  const response = await fetch(`${API_URL}/api/conversations`, { cache: "no-store" });
  if (!response.ok) throw new Error("Could not load conversations");
  return response.json();
}

export async function fetchConversation(id: string): Promise<ConversationRecord> {
  const response = await fetch(`${API_URL}/api/conversations/${id}`, { cache: "no-store" });
  if (!response.ok) throw new Error("Could not restore conversation");
  return response.json();
}

export async function deleteConversation(id: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/conversations/${id}`, { method: "DELETE" });
  if (!response.ok) throw new Error("Could not delete conversation");
}

export async function renameConversation(id: string, title: string): Promise<ConversationRecord> {
  const response = await fetch(`${API_URL}/api/conversations/${id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ title }) });
  if (!response.ok) throw new Error("Could not rename conversation");
  return response.json();
}

export async function summarizeDocument(id: string, style: "concise" | "detailed" | "key_takeaways"): Promise<string> {
  const response = await fetch(`${API_URL}/api/documents/${id}/summarize`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ style }) });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(typeof payload.detail === "string" ? payload.detail : "Could not summarize document");
  }
  return (await response.json()).summary;
}

export async function streamQuestion(
  question: string, documentIds: string[], conversationId: string | null,
  callbacks: { onStart: (id: string) => void; onDelta: (text: string) => void; onDone: (answer: ChatResult) => void },
): Promise<void> {
  const response = await fetch(`${API_URL}/api/chat/stream`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, document_ids: documentIds, conversation_id: conversationId }),
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(typeof payload.detail === "string" ? payload.detail : "Could not start answer");
  }
  if (!response.body) throw new Error("Streaming is unavailable in this browser");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let completed = false;
  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value, { stream: !done });
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";
    for (const raw of events) {
      const kind = raw.match(/^event: (.+)$/m)?.[1];
      const data = raw.match(/^data: (.+)$/m)?.[1];
      if (!kind || !data) continue;
      const payload = JSON.parse(data);
      if (kind === "start") callbacks.onStart(payload.conversation_id);
      if (kind === "delta") callbacks.onDelta(payload.text);
      if (kind === "done") { completed = true; callbacks.onDone(payload); }
      if (kind === "error") throw new Error(payload.message);
    }
    if (done) break;
  }
  if (!completed) throw new Error("The answer stream ended unexpectedly");
}

export async function askQuestion(question: string, documentIds: string[], history: { role: "user" | "assistant"; content: string }[]): Promise<ChatAnswer> {
  const response = await fetch(`${API_URL}/api/chat`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, document_ids: documentIds, history }),
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(typeof payload.detail === "string" ? payload.detail : "The answer could not be generated");
  }
  return response.json();
}

