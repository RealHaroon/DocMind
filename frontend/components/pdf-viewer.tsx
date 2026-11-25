"use client";

import { ChevronLeft, ChevronRight, Minus, Plus, FileText } from "lucide-react";
import { useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

import { Button } from "@/components/ui/button";
import { API_URL, type DocumentRecord } from "@/lib/api";

pdfjs.GlobalWorkerOptions.workerSrc = new URL("pdfjs-dist/build/pdf.worker.min.mjs", import.meta.url).toString();

export function PdfViewer({ documents, documentId, page, onChangeDocument, onChangePage }: {
  documents: DocumentRecord[]; documentId: string | null; page: number;
  onChangeDocument: (id: string) => void; onChangePage: (page: number) => void;
}) {
  const [pages, setPages] = useState(0);
  const [zoom, setZoom] = useState(1);
  const selected = documents.find((doc) => doc.id === documentId);

  return <aside className="hidden w-[40%] min-w-80 flex-col border-l border-white/[0.07] bg-[#0b0b0e] lg:flex">
    <div className="flex h-14 items-center gap-2 border-b border-white/[0.07] px-3">
      <select aria-label="PDF document" value={documentId ?? ""} onChange={(event) => onChangeDocument(event.target.value)} className="min-w-0 flex-1 truncate bg-transparent text-sm outline-none">
        <option value="" className="bg-zinc-900">Document preview</option>
        {documents.filter((doc) => doc.status === "ready").map((doc) => <option className="bg-zinc-900" key={doc.id} value={doc.id}>{doc.filename}</option>)}
      </select>
      <span className="rounded-full bg-white/5 px-2 py-1 text-[10px] text-zinc-500">PDF</span>
    </div>
    {selected ? <>
      <div className="flex items-center justify-between gap-1 border-b border-white/[0.07] p-2">
        <div className="flex items-center gap-1"><Button variant="ghost" size="icon" aria-label="Previous page" disabled={page <= 1} onClick={() => onChangePage(page - 1)}><ChevronLeft className="size-4" /></Button><span className="text-xs text-zinc-400">{page} / {pages || selected.page_count}</span><Button variant="ghost" size="icon" aria-label="Next page" disabled={page >= (pages || selected.page_count)} onClick={() => onChangePage(page + 1)}><ChevronRight className="size-4" /></Button></div>
        <div className="flex items-center gap-1"><Button variant="ghost" size="icon" aria-label="Zoom out" onClick={() => setZoom((value) => Math.max(0.5, value - 0.15))}><Minus className="size-4" /></Button><span className="w-10 text-center text-xs text-zinc-500">{Math.round(zoom * 100)}%</span><Button variant="ghost" size="icon" aria-label="Zoom in" onClick={() => setZoom((value) => Math.min(2, value + 0.15))}><Plus className="size-4" /></Button></div>
      </div>
      <div className="flex flex-1 justify-center overflow-auto bg-[#16161b] p-4">
        <Document file={`${API_URL}/api/documents/${selected.id}/file`} loading={<p className="animate-pulse text-sm text-zinc-500">Loading PDF…</p>} error={<p className="text-sm text-rose-400">Could not open this PDF.</p>} onLoadSuccess={(pdf) => setPages(pdf.numPages)}>
          <Page pageNumber={Math.min(page, pages || selected.page_count)} width={520 * zoom} loading={<p className="animate-pulse text-sm text-zinc-500">Rendering page…</p>} />
        </Document>
      </div>
    </> : <div className="grid flex-1 place-items-center p-8"><div className="max-w-xs text-center"><FileText className="mx-auto mb-5 size-10 text-zinc-700" /><div className="text-sm font-medium text-zinc-400">No document open</div><p className="mt-2 text-xs leading-5 text-zinc-600">Select a PDF or click a citation to preview its source page here.</p></div></div>}
  </aside>;
}
