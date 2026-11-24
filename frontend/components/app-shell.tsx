"use client";

import {
  BookOpenText,
  ChevronDown,
  FileText,
  Library,
  Menu,
  MessageSquareText,
  PanelRight,
  Plus,
  Send,
  Settings,
  Sparkles,
  UploadCloud,
} from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { fetchHealth, type HealthResponse } from "@/lib/api";

const suggestions = [
  { icon: BookOpenText, title: "Summarize this document", detail: "Get a concise, sourced overview" },
  { icon: Sparkles, title: "Find the key insights", detail: "Surface important takeaways" },
  { icon: MessageSquareText, title: "Explain a complex topic", detail: "Ask for a clear explanation" },
];

export function AppShell() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    fetchHealth().then(setHealth).catch(() => setOffline(true));
  }, []);

  return (
    <main className="flex min-h-screen bg-[#09090b] text-zinc-100">
      <aside className="hidden w-64 shrink-0 flex-col border-r border-white/[0.07] bg-[#0c0c0f] p-4 md:flex">
        <div className="mb-7 flex items-center gap-3 px-2 py-1">
          <div className="grid size-9 place-items-center rounded-xl bg-gradient-to-br from-violet-500 to-indigo-600 shadow-lg shadow-violet-950/50">
            <FileText className="size-5" />
          </div>
          <div>
            <div className="font-semibold tracking-tight">DocMind</div>
            <div className="text-[10px] uppercase tracking-[0.2em] text-zinc-500">Document AI</div>
          </div>
        </div>

        <Button className="mb-6 w-full justify-start"><Plus className="size-4" /> New chat</Button>

        <nav className="space-y-1">
          <SidebarItem icon={MessageSquareText} label="Conversations" active />
          <SidebarItem icon={Library} label="Document library" />
          <SidebarItem icon={Settings} label="Settings" />
        </nav>

        <div className="mt-8 px-3 text-[11px] font-medium uppercase tracking-[0.16em] text-zinc-600">Recent</div>
        <div className="mt-3 rounded-xl border border-dashed border-white/[0.08] px-3 py-4 text-center text-xs leading-relaxed text-zinc-600">
          Your conversations will appear here.
        </div>

        <div className="mt-auto rounded-2xl border border-white/[0.08] bg-white/[0.025] p-3">
          <div className="flex items-center gap-2 text-xs text-zinc-400">
            <span className={`size-2 rounded-full ${offline ? "bg-rose-400" : health ? "bg-emerald-400" : "animate-pulse bg-amber-400"}`} />
            {offline ? "Backend offline" : health ? `API v${health.version} connected` : "Connecting to API…"}
          </div>
        </div>
      </aside>

      <section className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 items-center justify-between border-b border-white/[0.07] px-4 lg:px-6">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" className="md:hidden" aria-label="Open menu"><Menu className="size-5" /></Button>
            <div>
              <h1 className="text-sm font-medium">New conversation</h1>
              <p className="text-xs text-zinc-600">No documents selected</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm"><UploadCloud className="size-4" /><span className="hidden sm:inline">Add documents</span></Button>
            <Button variant="ghost" size="icon" aria-label="Toggle PDF panel"><PanelRight className="size-4" /></Button>
          </div>
        </header>

        <div className="relative flex flex-1 overflow-hidden">
          <div className="flex min-w-0 flex-1 flex-col">
            <div className="flex flex-1 items-center justify-center overflow-y-auto px-5 py-12">
              <div className="w-full max-w-2xl text-center">
                <div className="mx-auto mb-6 grid size-14 place-items-center rounded-2xl border border-violet-400/20 bg-violet-500/10 text-violet-300 shadow-[0_0_50px_rgba(124,58,237,0.14)]">
                  <Sparkles className="size-6" />
                </div>
                <h2 className="text-3xl font-semibold tracking-[-0.04em] sm:text-4xl">Ask your documents anything</h2>
                <p className="mx-auto mt-4 max-w-lg text-sm leading-6 text-zinc-500">
                  Upload PDFs and get clear, grounded answers with citations that take you straight to the source.
                </p>

                <div className="mt-9 grid gap-3 sm:grid-cols-3">
                  {suggestions.map(({ icon: Icon, title, detail }) => (
                    <button key={title} className="group rounded-2xl border border-white/[0.08] bg-white/[0.025] p-4 text-left transition hover:-translate-y-0.5 hover:border-violet-400/25 hover:bg-violet-500/[0.06]">
                      <Icon className="mb-7 size-4 text-violet-400" />
                      <div className="text-sm font-medium text-zinc-300 group-hover:text-white">{title}</div>
                      <div className="mt-1 text-xs leading-5 text-zinc-600">{detail}</div>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="mx-auto w-full max-w-3xl px-4 pb-5">
              <div className="rounded-2xl border border-white/[0.1] bg-[#111116] p-2 shadow-2xl shadow-black/30 focus-within:border-violet-500/40">
                <textarea aria-label="Ask a question" rows={2} placeholder="Select a document, then ask a question…" className="w-full resize-none bg-transparent px-3 py-2 text-sm text-zinc-200 outline-none placeholder:text-zinc-600" />
                <div className="flex items-center justify-between px-2 pb-1">
                  <button className="flex items-center gap-1.5 rounded-lg px-2 py-1 text-xs text-zinc-500 transition hover:bg-white/5 hover:text-zinc-300">
                    Gemini <ChevronDown className="size-3" />
                  </button>
                  <Button size="icon" className="size-9" aria-label="Send message"><Send className="size-4" /></Button>
                </div>
              </div>
              <p className="mt-2 text-center text-[10px] text-zinc-700">Answers are grounded in selected documents. Verify important information.</p>
            </div>
          </div>

          <aside className="hidden w-[38%] min-w-80 border-l border-white/[0.07] bg-[#0b0b0e] xl:flex xl:flex-col">
            <div className="flex h-14 items-center justify-between border-b border-white/[0.07] px-4">
              <span className="text-sm font-medium">Document preview</span>
              <span className="rounded-full bg-white/5 px-2 py-1 text-[10px] text-zinc-600">PDF</span>
            </div>
            <div className="grid flex-1 place-items-center p-8">
              <div className="max-w-xs text-center">
                <div className="mx-auto mb-5 grid size-16 place-items-center rounded-2xl border border-dashed border-white/10 bg-white/[0.02]">
                  <FileText className="size-7 text-zinc-700" />
                </div>
                <div className="text-sm font-medium text-zinc-400">No document open</div>
                <p className="mt-2 text-xs leading-5 text-zinc-600">Select a PDF or click a citation to preview its source page here.</p>
              </div>
            </div>
          </aside>
        </div>
      </section>
    </main>
  );
}

function SidebarItem({ icon: Icon, label, active = false }: { icon: typeof MessageSquareText; label: string; active?: boolean }) {
  return (
    <button className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition ${active ? "bg-white/[0.06] text-zinc-100" : "text-zinc-500 hover:bg-white/[0.035] hover:text-zinc-300"}`}>
      <Icon className="size-4" /> {label}
    </button>
  );
}

