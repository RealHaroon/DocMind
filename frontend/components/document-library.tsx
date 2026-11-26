"use client";

import { Check, FileText, LoaderCircle, Trash2, UploadCloud, X } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { deleteDocument, fetchDocuments, uploadDocuments, type DocumentRecord } from "@/lib/api";

export function DocumentLibrary({ onClose, selected, onToggle }: {
  onClose: () => void;
  selected: string[];
  onToggle: (id: string) => void;
}) {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [busy, setBusy] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [message, setMessage] = useState("");
  const input = useRef<HTMLInputElement>(null);
  const ready = documents.filter((doc) => doc.status === "ready");
  const selectedReady = ready.filter((doc) => selected.includes(doc.id));
  const refresh = useCallback(async () => {
    try { setDocuments(await fetchDocuments()); }
    catch (error) { setMessage((error as Error).message); }
  }, []);

  useEffect(() => {
    fetchDocuments().then(setDocuments).catch((error: Error) => setMessage(error.message));
  }, []);
  useEffect(() => {
    if (!documents.some((doc) => doc.status === "processing")) return;
    const timer = window.setInterval(() => { void refresh(); }, 1500);
    return () => window.clearInterval(timer);
  }, [documents, refresh]);

  async function add(files: FileList | null) {
    if (!files?.length) return;
    setMessage("");
    const batch = Array.from(files);
    if (batch.length > 10 || batch.some((file) => !file.name.toLowerCase().endsWith(".pdf") || file.size > 20 * 1024 * 1024)) {
      setMessage("Select up to 10 PDF files, each 20 MB or smaller.");
      return;
    }
    setBusy(true);
    try { await uploadDocuments(batch); await refresh(); setMessage("PDFs uploaded. Processing has started."); }
    catch (error) { setMessage((error as Error).message); }
    finally { setBusy(false); if (input.current) input.current.value = ""; }
  }

  async function remove(doc: DocumentRecord) {
    if (!window.confirm(`Delete ${doc.filename}?`)) return;
    try { await deleteDocument(doc.id); if (selected.includes(doc.id)) onToggle(doc.id); await refresh(); }
    catch (error) { setMessage((error as Error).message); }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4" role="dialog" aria-modal="true" aria-label="Document library">
      <div className="flex max-h-[90vh] w-full max-w-2xl flex-col rounded-3xl border border-white/10 bg-[#14141a] p-5 shadow-2xl sm:p-7">
        <div className="mb-6 flex items-start justify-between">
          <div><h2 className="text-xl font-semibold">Document library</h2><p className="mt-1 text-sm text-zinc-500">Choose the PDFs DocMind may use for your answers.</p></div>
          <Button variant="ghost" size="icon" onClick={onClose} aria-label="Close library"><X className="size-4" /></Button>
        </div>
        <input ref={input} type="file" accept="application/pdf,.pdf" multiple className="hidden" onChange={(event) => void add(event.target.files)} />
        <div onDragOver={(event) => { event.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={(event) => { event.preventDefault(); setDragging(false); void add(event.dataTransfer.files); }} className={`rounded-2xl border border-dashed p-6 text-center transition ${dragging ? "border-violet-400 bg-violet-500/10" : "border-white/15 bg-white/[0.025]"}`}>
          <UploadCloud className="mx-auto mb-3 size-7 text-violet-400" />
          <p className="text-sm font-medium">Drag and drop your PDFs here</p>
          <p className="mt-1 text-xs text-zinc-500">Up to 10 PDFs at once · 20 MB each · searchable text required</p>
          <Button className="mt-4" disabled={busy} onClick={() => input.current?.click()}>{busy ? <LoaderCircle className="size-4 animate-spin" /> : <UploadCloud className="size-4" />} Choose files</Button>
        </div>
        {message && <p className="mt-4 rounded-xl bg-white/5 p-3 text-sm text-zinc-300" role="status">{message}</p>}
        <div className="mt-6 flex items-center justify-between gap-3">
          <h3 className="text-xs font-medium uppercase tracking-wider text-zinc-500">Your documents · {documents.length}</h3>
          {ready.length > 0 && <button type="button" onClick={() => ready.filter((doc) => !selected.includes(doc.id)).forEach((doc) => onToggle(doc.id))} className="text-xs text-violet-300 hover:text-violet-200">Select all ready</button>}
        </div>
        <div className="mt-3 min-h-0 space-y-2 overflow-y-auto pr-1">
          {documents.length === 0 && <p className="py-6 text-center text-sm text-zinc-600">Your library is empty.</p>}
          {documents.map((doc) => (
            <div key={doc.id} className={`flex items-center gap-3 rounded-xl border p-3 transition ${selected.includes(doc.id) ? "border-violet-400/40 bg-violet-500/[0.08]" : "border-white/[0.07] bg-white/[0.025]"}`}>
              <label className={`flex min-w-0 flex-1 items-center gap-3 ${doc.status === "ready" ? "cursor-pointer" : "cursor-not-allowed"}`}>
                <input type="checkbox" aria-label={`Select ${doc.filename}`} checked={selected.includes(doc.id)} disabled={doc.status !== "ready"} onChange={() => onToggle(doc.id)} className="size-4 accent-violet-500" />
                <FileText className="size-5 shrink-0 text-violet-400" />
                <span className="min-w-0 flex-1"><span className="block truncate text-sm font-medium" title={doc.filename}>{doc.filename}</span><span className="mt-1 block text-xs text-zinc-500">{doc.page_count} pages · {(doc.size_bytes / 1024 / 1024).toFixed(2)} MB · {new Date(doc.uploaded_at).toLocaleDateString()} · <span className={doc.status === "failed" ? "text-rose-400" : doc.status === "ready" ? "text-emerald-400" : "text-amber-400"}>{doc.status}</span></span>{doc.error && <span className="mt-1 block text-xs text-rose-400">{doc.error}</span>}</span>
              </label>
              <Button variant="ghost" size="icon" aria-label={`Delete ${doc.filename}`} onClick={() => void remove(doc)}><Trash2 className="size-4" /></Button>
            </div>
          ))}
        </div>
        <div className="mt-5 flex items-center justify-between gap-3 border-t border-white/10 pt-4">
          <p className="text-xs text-zinc-500">{selectedReady.length} ready PDF{selectedReady.length === 1 ? "" : "s"} selected{documents.some((doc) => doc.status === "processing") ? " · Processing continues in the background" : ""}</p>
          <Button onClick={onClose}><Check className="size-4" /> OK</Button>
        </div>
      </div>
    </div>
  );
}
