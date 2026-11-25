"use client";

import dynamic from "next/dynamic";
import { useTheme } from "next-themes";
import { BookOpenText, FileText, Library, Menu, MessageSquareText, PanelRight, Plus, Send, Settings, Sparkles, Trash2, UploadCloud, X } from "lucide-react";
import { useEffect, useState } from "react";

import { AnswerMarkdown } from "@/components/answer-markdown";
import { DocumentLibrary } from "@/components/document-library";
import { Button } from "@/components/ui/button";
import { API_URL, deleteConversation, fetchConversation, fetchConversations, fetchDocuments, fetchHealth, fetchSettings, renameConversation, streamQuestion, summarizeDocument, updateSettings, type AppSettings, type Citation, type ConversationRecord, type DocumentRecord } from "@/lib/api";

const PdfViewer = dynamic(() => import("@/components/pdf-viewer").then((module) => module.PdfViewer), { ssr: false });

type Message = { role: "user" | "assistant"; content: string; citations: Citation[] };

export function Workspace() {
  const { setTheme } = useTheme();
  const [online, setOnline] = useState(false);
  const [libraryOpen, setLibraryOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [viewerOpen, setViewerOpen] = useState(true);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [viewerId, setViewerId] = useState<string | null>(null);
  const [viewerPage, setViewerPage] = useState(1);
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [conversations, setConversations] = useState<ConversationRecord[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchHealth().then(() => setOnline(true)).catch(() => setOnline(false));
    fetchSettings().then(setSettings).catch(() => {});
    fetchDocuments().then(setDocuments).catch(() => {});
    fetchConversations().then(setConversations).catch(() => {});
  }, []);

  async function refresh() {
    try {
      const [docs, chats] = await Promise.all([fetchDocuments(), fetchConversations()]);
      setDocuments(docs); setConversations(chats);
    } catch (cause) { setError((cause as Error).message); }
  }

  function toggleDocument(id: string) {
    setSelected((items) => items.includes(id) ? items.filter((item) => item !== id) : [...items, id]);
    if (!viewerId) { setViewerId(id); setViewerPage(1); }
  }

  function openSource(citation: Citation) {
    setViewerId(citation.document_id); setViewerPage(citation.page); setViewerOpen(true);
    if (window.innerWidth < 1024) window.open(`${API_URL}/api/documents/${citation.document_id}/file#page=${citation.page}`, "_blank", "noopener,noreferrer");
  }

  async function send(value = question) {
    const prompt = value.trim();
    if (!prompt || busy) return;
    if (!selected.length) { setLibraryOpen(true); return; }
    setQuestion(""); setError(""); setBusy(true);
    setMessages((items) => [...items, { role: "user", content: prompt, citations: [] }, { role: "assistant", content: "", citations: [] }]);
    try {
      await streamQuestion(prompt, selected, conversationId, {
        onStart: (id) => setConversationId(id),
        onDelta: (text) => setMessages((items) => items.map((item, index) => index === items.length - 1 ? { ...item, content: item.content + text } : item)),
        onDone: (answer) => {
          setMessages((items) => items.map((item, index) => index === items.length - 1 ? { ...item, content: answer.answer, citations: answer.citations } : item));
          if (answer.conversation_id) setConversationId(answer.conversation_id);
        },
      });
      await refresh();
    } catch (cause) {
      setError((cause as Error).message);
      setMessages((items) => items.slice(0, -2));
      setQuestion(prompt);
    } finally { setBusy(false); }
  }

  async function openConversation(id: string) {
    try {
      const conversation = await fetchConversation(id);
      setConversationId(id); setSelected(conversation.document_ids);
      setMessages(conversation.messages.map((item) => ({ role: item.role, content: item.content, citations: item.citations })));
      setViewerId(conversation.document_ids[0] ?? null); setViewerPage(1); setSidebarOpen(false); setError("");
    } catch (cause) { setError((cause as Error).message); }
  }

  async function removeConversation(id: string) {
    if (!window.confirm("Delete this conversation?")) return;
    try {
      await deleteConversation(id);
      if (conversationId === id) { setConversationId(null); setMessages([]); }
      await refresh();
    } catch (cause) { setError((cause as Error).message); }
  }

  async function rename(id: string, oldTitle: string) {
    const title = window.prompt("Conversation title", oldTitle)?.trim();
    if (!title || title === oldTitle) return;
    try { await renameConversation(id, title); await refresh(); }
    catch (cause) { setError((cause as Error).message); }
  }

  async function summarize(style: "concise" | "detailed" | "key_takeaways") {
    if (!selected.length) { setLibraryOpen(true); return; }
    setBusy(true); setError("");
    try {
      const text = await summarizeDocument(selected[0], style);
      setMessages((items) => [...items, { role: "assistant", content: text, citations: [] }]);
    } catch (cause) { setError((cause as Error).message); }
    finally { setBusy(false); }
  }

  async function saveSettings(next: AppSettings) {
    try { const saved = await updateSettings(next); setSettings(saved); setTheme(saved.theme); setError(""); }
    catch (cause) { setError((cause as Error).message); }
  }

  const currentTitle = conversations.find((item) => item.id === conversationId)?.title ?? "New conversation";
  return <main className="flex h-screen min-h-[580px] bg-[#09090b] text-zinc-100">
    {libraryOpen && <DocumentLibrary onClose={() => { setLibraryOpen(false); void refresh(); }} selected={selected} onToggle={toggleDocument} />}
    {settingsOpen && settings && <div className="fixed inset-0 z-50 grid place-items-center bg-black/75 p-4" role="dialog" aria-modal="true" aria-label="Settings"><div className="w-full max-w-md rounded-3xl border border-white/10 bg-[#17171d] p-6 shadow-2xl"><div className="mb-6 flex items-center justify-between"><h2 className="text-xl font-semibold">Settings</h2><Button variant="ghost" size="icon" onClick={() => setSettingsOpen(false)} aria-label="Close settings"><X className="size-4" /></Button></div><div className="space-y-4 text-sm"><label className="block">AI provider<select value={settings.provider} onChange={(event) => void saveSettings({ ...settings, provider: event.target.value as "gemini" | "groq" })} className="mt-2 w-full rounded-xl border border-white/10 bg-[#22222a] p-2"><option value="gemini">Google Gemini</option><option value="groq">Groq</option></select></label><label className="block">Gemini model<input value={settings.gemini_model} onChange={(event) => setSettings({ ...settings, gemini_model: event.target.value })} onBlur={() => void saveSettings(settings)} className="mt-2 w-full rounded-xl border border-white/10 bg-[#22222a] p-2" /></label><label className="block">Groq model<input value={settings.groq_model} onChange={(event) => setSettings({ ...settings, groq_model: event.target.value })} onBlur={() => void saveSettings(settings)} className="mt-2 w-full rounded-xl border border-white/10 bg-[#22222a] p-2" /></label><label className="block">Retrieved chunks: {settings.rag_top_k}<input type="range" min="1" max="20" value={settings.rag_top_k} onChange={(event) => setSettings({ ...settings, rag_top_k: Number(event.target.value) })} onPointerUp={() => void saveSettings(settings)} className="mt-2 w-full accent-violet-500" /></label><label className="block">Theme<select value={settings.theme} onChange={(event) => void saveSettings({ ...settings, theme: event.target.value as AppSettings["theme"] })} className="mt-2 w-full rounded-xl border border-white/10 bg-[#22222a] p-2"><option value="dark">Dark</option><option value="light">Light</option><option value="system">System</option></select></label><p className="text-xs text-zinc-500">{settings.provider_configured ? "Selected provider is configured." : "Add this provider’s API key in backend/.env before chatting."}</p></div></div></div>}
    <aside className={`${sidebarOpen ? "flex fixed inset-y-0 left-0 z-40" : "hidden"} w-64 shrink-0 flex-col border-r border-white/[0.07] bg-[#0c0c0f] p-4 md:relative md:flex`}>
      <div className="mb-7 flex items-center gap-3 px-2 py-1"><div className="grid size-9 place-items-center rounded-xl bg-gradient-to-br from-violet-500 to-indigo-600"><FileText className="size-5" /></div><div><div className="font-semibold tracking-tight">DocMind</div><div className="text-[10px] uppercase tracking-[0.2em] text-zinc-500">Document AI</div></div></div>
      <Button className="mb-6 justify-start" onClick={() => { setConversationId(null); setMessages([]); setQuestion(""); setSidebarOpen(false); }}><Plus className="size-4" /> New chat</Button>
      <nav className="space-y-1"><button onClick={() => setSidebarOpen(false)} className="flex w-full items-center gap-3 rounded-xl bg-white/[0.06] px-3 py-2.5 text-sm"><MessageSquareText className="size-4" /> Conversations</button><button onClick={() => { setLibraryOpen(true); setSidebarOpen(false); }} className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-zinc-400 hover:bg-white/5"><Library className="size-4" /> Document library</button><button onClick={() => { setSettingsOpen(true); setSidebarOpen(false); }} className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-zinc-400 hover:bg-white/5"><Settings className="size-4" /> Settings</button></nav>
      <div className="mt-8 px-3 text-[11px] font-medium uppercase tracking-[0.16em] text-zinc-600">Recent</div>
      <div className="mt-3 flex-1 space-y-1 overflow-y-auto">{conversations.length ? conversations.map((item) => <div key={item.id} className={`group flex items-center rounded-xl ${conversationId === item.id ? "bg-white/[0.07]" : "hover:bg-white/[0.04]"}`}><button onClick={() => void openConversation(item.id)} onDoubleClick={() => void rename(item.id, item.title)} title="Open; double-click to rename" className="min-w-0 flex-1 truncate px-3 py-2 text-left text-xs text-zinc-400">{item.title}</button><button onClick={() => void removeConversation(item.id)} aria-label={`Delete ${item.title}`} className="p-2 text-zinc-600 opacity-0 hover:text-rose-400 group-hover:opacity-100"><Trash2 className="size-3.5" /></button></div>) : <p className="rounded-xl border border-dashed border-white/10 p-4 text-center text-xs text-zinc-600">Your conversations will appear here.</p>}</div>
      <div className="mt-3 rounded-2xl border border-white/[0.08] bg-white/[0.025] p-3 text-xs text-zinc-400"><span className={`mr-2 inline-block size-2 rounded-full ${online ? "bg-emerald-400" : "bg-rose-400"}`} />{online ? "API connected" : "Backend offline"}</div>
    </aside>
    <section className="flex min-w-0 flex-1 flex-col"><header className="flex h-16 shrink-0 items-center justify-between border-b border-white/[0.07] px-4 lg:px-6"><div className="flex items-center gap-3"><Button variant="ghost" size="icon" className="md:hidden" aria-label="Open menu" onClick={() => setSidebarOpen(true)}><Menu className="size-5" /></Button><div><h1 className="max-w-52 truncate text-sm font-medium">{currentTitle}</h1><p className="text-xs text-zinc-600">{selected.length} document{selected.length === 1 ? "" : "s"} selected</p></div></div><div className="flex items-center gap-2"><Button variant="outline" size="sm" onClick={() => setLibraryOpen(true)}><UploadCloud className="size-4" /><span className="hidden sm:inline">Add documents</span></Button><Button variant="ghost" size="icon" aria-label="Toggle PDF panel" onClick={() => setViewerOpen((open) => !open)}><PanelRight className="size-4" /></Button></div></header>
      <div className="flex min-h-0 flex-1"><div className="flex min-w-0 flex-1 flex-col"><div className="flex-1 overflow-y-auto px-5 py-8"><div className="mx-auto max-w-2xl space-y-5">{messages.length ? messages.map((message, index) => <div key={index} className={message.role === "user" ? "ml-auto max-w-[85%] rounded-2xl bg-violet-500/15 p-4 text-sm" : "rounded-2xl border border-white/10 bg-white/[0.025] p-5"}>{message.role === "assistant" ? <AnswerMarkdown>{message.content || "Thinking…"}</AnswerMarkdown> : <p className="whitespace-pre-wrap">{message.content}</p>}{message.citations.length > 0 && <div className="mt-4 flex flex-wrap gap-2 border-t border-white/10 pt-4">{message.citations.map((cite) => <button key={cite.marker} onClick={() => openSource(cite)} className="rounded-lg border border-violet-400/20 bg-violet-500/10 px-2 py-1 text-left text-xs text-violet-300 hover:bg-violet-500/20">[{cite.marker}] {cite.filename} · Page {cite.page}</button>)}</div>}</div>) : <div className="py-12 text-center"><div className="mx-auto mb-6 grid size-14 place-items-center rounded-2xl border border-violet-400/20 bg-violet-500/10 text-violet-300"><Sparkles className="size-6" /></div><h2 className="text-3xl font-semibold tracking-tight">Ask your documents anything</h2><p className="mx-auto mt-4 max-w-lg text-sm leading-6 text-zinc-500">Upload PDFs and get clear answers with citations that take you straight to the source.</p><div className="mt-9 grid gap-3 sm:grid-cols-3"><button onClick={() => void summarize("concise")} className="rounded-2xl border border-white/10 bg-white/[0.025] p-4 text-left hover:bg-white/5"><BookOpenText className="mb-6 size-4 text-violet-400" /><span className="text-sm">Concise summary</span></button><button onClick={() => void summarize("detailed")} className="rounded-2xl border border-white/10 bg-white/[0.025] p-4 text-left hover:bg-white/5"><Sparkles className="mb-6 size-4 text-violet-400" /><span className="text-sm">Detailed summary</span></button><button onClick={() => void summarize("key_takeaways")} className="rounded-2xl border border-white/10 bg-white/[0.025] p-4 text-left hover:bg-white/5"><MessageSquareText className="mb-6 size-4 text-violet-400" /><span className="text-sm">Key takeaways</span></button></div></div>}{busy && <p className="animate-pulse text-center text-xs text-zinc-500">Working on your request…</p>}</div></div><div className="mx-auto w-full max-w-3xl px-4 pb-5"><div className="rounded-2xl border border-white/[0.1] bg-[#111116] p-2 focus-within:border-violet-500/40"><textarea aria-label="Ask a question" rows={2} value={question} onChange={(event) => setQuestion(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); void send(); } }} placeholder="Ask about your selected PDFs…" className="w-full resize-none bg-transparent px-3 py-2 text-sm outline-none placeholder:text-zinc-600" /><div className="flex items-center justify-between px-2 pb-1"><button onClick={() => setSettingsOpen(true)} className="text-xs text-zinc-500 hover:text-zinc-300">{settings?.provider === "groq" ? "Groq" : "Gemini"} · Settings</button><Button size="icon" aria-label="Send message" disabled={busy || !question.trim()} onClick={() => void send()}><Send className="size-4" /></Button></div></div>{error && <p role="alert" className="mt-2 rounded-lg bg-rose-500/10 p-2 text-sm text-rose-300">{error}</p>}<p className="mt-2 text-center text-[10px] text-zinc-700">Answers use selected documents. Verify important information.</p></div></div>{viewerOpen && <PdfViewer key={viewerId ?? "none"} documents={documents} documentId={viewerId} page={viewerPage} onChangeDocument={(id) => { setViewerId(id || null); setViewerPage(1); }} onChangePage={setViewerPage} />}</div>
    </section>
  </main>;
}
