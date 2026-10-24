"use client";

import React, { useState } from "react";
import { CitationDetail } from "@/lib/types";
import { X, FileText, Bookmark, Hash, Copy, Check, ExternalLink } from "lucide-react";

interface CitationDrawerProps {
  citations: CitationDetail[];
  activeCitation: CitationDetail | null;
  onClose: () => void;
  onSelectCitation: (citation: CitationDetail) => void;
}

export const CitationDrawer: React.FC<CitationDrawerProps> = ({
  citations,
  activeCitation,
  onClose,
  onSelectCitation,
}) => {
  const [copied, setCopied] = useState(false);

  if (!activeCitation && citations.length === 0) return null;

  const current = activeCitation || citations[0];

  const handleCopy = () => {
    if (!current) return;
    navigator.clipboard.writeText(current.excerpt);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-y-0 right-0 z-50 flex w-full max-w-md flex-col bg-slate-900 border-l border-slate-800 shadow-2xl animate-in slide-in-from-right duration-200">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 p-4">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-teal-500/15 border border-teal-500/30 text-teal-300 font-mono text-xs font-bold">
            {current?.citation_label || "[S]"}
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">Citation Inspector</h3>
            <p className="text-[11px] text-slate-400">Verifiable ground truth source</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Citations List Selector if multiple */}
      {citations.length > 1 && (
        <div className="flex gap-2 overflow-x-auto border-b border-slate-800/80 bg-slate-950/40 p-2.5">
          {citations.map((c) => (
            <button
              key={c.chunk_id + c.citation_label}
              onClick={() => onSelectCitation(c)}
              className={`flex shrink-0 items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-mono transition-all ${
                c.citation_label === current?.citation_label
                  ? "bg-teal-500/20 text-teal-300 border border-teal-500/40"
                  : "bg-slate-800/60 text-slate-400 hover:text-slate-200"
              }`}
            >
              <span>{c.citation_label}</span>
              <span className="max-w-[100px] truncate font-sans text-[11px] text-slate-400">
                {c.filename}
              </span>
            </button>
          ))}
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Source metadata card */}
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3.5 space-y-2.5">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-200">
            <FileText className="h-4 w-4 text-teal-400" />
            <span className="truncate">{current?.filename}</span>
          </div>

          <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800/60 text-xs">
            {current?.page_number !== null && current?.page_number !== undefined && (
              <div className="flex items-center gap-1 text-slate-400">
                <Bookmark className="h-3.5 w-3.5 text-slate-500" />
                <span>Page: {current.page_number}</span>
              </div>
            )}
            {current?.retrieval_rank !== undefined && (
              <div className="flex items-center gap-1 text-slate-400">
                <Hash className="h-3.5 w-3.5 text-slate-500" />
                <span>Rank: #{current.retrieval_rank}</span>
              </div>
            )}
            {current?.retrieval_score !== null && current?.retrieval_score !== undefined && (
              <div className="col-span-2 flex items-center justify-between text-[11px] text-slate-400">
                <span>Relevance score:</span>
                <span className="font-mono text-teal-400 font-semibold">
                  {(current.retrieval_score * 100).toFixed(1)}%
                </span>
              </div>
            )}
            {current?.section_path && (
              <div className="col-span-2 text-[11px] text-slate-400 truncate">
                <span className="text-slate-500">Section: </span>
                {current.section_path}
              </div>
            )}
          </div>
        </div>

        {/* Excerpt Section */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-slate-300">Retrieved Excerpt</span>
            <button
              onClick={handleCopy}
              className="flex items-center gap-1 rounded px-2 py-0.5 text-[11px] text-slate-400 hover:text-teal-300 transition-colors"
            >
              {copied ? (
                <>
                  <Check className="h-3 w-3 text-emerald-400" />
                  <span className="text-emerald-400">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="h-3 w-3" />
                  <span>Copy</span>
                </>
              )}
            </button>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-950 p-3.5 text-xs text-slate-300 leading-relaxed font-mono whitespace-pre-wrap selection:bg-teal-500/20 selection:text-teal-200">
            {current?.excerpt}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-slate-800 p-3 bg-slate-950/80 text-center">
        <p className="text-[11px] text-slate-400">
          Grounded citation verified from indexed document chunks in Supabase
        </p>
      </div>
    </div>
  );
};
