"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export function AnswerMarkdown({ children }: { children: string }) {
  return <div className="answer-markdown text-sm leading-7 text-zinc-200">
    <ReactMarkdown remarkPlugins={[remarkGfm]} skipHtml components={{
      a: ({ href, children: content }) => <a href={href} target="_blank" rel="noopener noreferrer" className="text-violet-300 underline">{content}</a>,
      code: ({ children: content }) => <code className="rounded bg-white/10 px-1 py-0.5 text-xs">{content}</code>,
    }}>{children}</ReactMarkdown>
  </div>;
}
