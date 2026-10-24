"use client";

import React, { useEffect, useState } from "react";
import { DocumentChunk, DocumentItem } from "@/lib/types";
import { api } from "@/lib/api";
import { X, Layers, Loader2, Copy, Check, Hash, FileText } from "lucide-react";

interface ChunkViewerModalProps {
  document: DocumentItem | null;
  onClose: () => void;
}

export const ChunkViewerModal: React.FC<ChunkViewerModalProps> = ({
  document,
  onClose,
}) => {
  const [chunks, setChunks] = useState<DocumentChunk[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    if (!document) return;

    let isMounted = true;
    const loadChunks = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await api.getDocumentChunks(document.id);
        if (isMounted) setChunks(data);
      } catch (err: any) {
        if (isMounted) setError(err.message || "Failed to load chunks");
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    loadChunks();
    return () => {
      isMounted = false;
    };
  }, [document]);

  if (!document) return null;

  const handleCopyChunk = (id: string, content: string) => {
    navigator.clipboard.writeText(content);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="relative flex flex-col w-full max-w-3xl max-h-[85vh] rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 p-5">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-teal-500/15 border border-teal-500/30 text-teal-400">
              <Layers className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                Document Chunks
                <span className="text-xs font-normal text-slate-400">
                  ({chunks.length} chunks indexed)
                </span>
              </h3>
              <p className="text-xs text-slate-400 truncate max-w-md">
                {document.original_filename}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Chunks List */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {loading && (
            <div className="flex flex-col items-center justify-center py-16 gap-3 text-slate-400 text-xs">
              <Loader2 className="h-6 w-6 animate-spin text-teal-400" />
              <span>Fetching chunks from Supabase vector store...</span>
            </div>
          )}

          {error && (
            <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-xs text-rose-300">
              {error}
            </div>
          )}

          {!loading && !error && chunks.length === 0 && (
            <div className="text-center py-12 text-slate-400 text-xs">
              No chunks generated for this document yet.
            </div>
          )}

          {!loading &&
            chunks.map((chunk) => (
              <div
                key={chunk.id}
                className="rounded-xl border border-slate-800/80 bg-slate-950/70 p-4 space-y-3 transition-colors hover:border-slate-700"
              >
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <span className="flex items-center gap-1 rounded bg-teal-500/15 text-teal-300 border border-teal-500/30 px-2 py-0.5 font-mono text-[11px]">
                      <Hash className="h-3 w-3" />
                      Chunk #{chunk.chunk_index + 1}
                    </span>
                    {chunk.page_number !== null && chunk.page_number !== undefined && (
                      <span className="rounded bg-slate-800 px-2 py-0.5 text-slate-300 text-[11px]">
                        Page {chunk.page_number}
                      </span>
                    )}
                    <span className="text-[11px] text-slate-400">
                      {chunk.token_count} tokens
                    </span>
                  </div>

                  <button
                    onClick={() => handleCopyChunk(chunk.id, chunk.content)}
                    className="flex items-center gap-1 rounded px-2 py-1 text-[11px] text-slate-400 hover:text-teal-300 transition-colors"
                  >
                    {copiedId === chunk.id ? (
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

                {chunk.section_path && (
                  <div className="text-[11px] text-slate-400">
                    <span className="text-slate-400">Hierarchy: </span>
                    <span className="text-slate-300">{chunk.section_path}</span>
                  </div>
                )}

                <div className="rounded-lg bg-slate-900/90 p-3 text-xs text-slate-300 leading-relaxed font-mono whitespace-pre-wrap max-h-48 overflow-y-auto">
                  {chunk.content}
                </div>
              </div>
            ))}
        </div>

        {/* Footer */}
        <div className="border-t border-slate-800 p-3.5 bg-slate-950/60 flex items-center justify-between text-xs text-slate-400">
          <span>Target ~800 tokens / 120 token overlap</span>
          <button
            onClick={onClose}
            className="rounded-lg bg-slate-800 px-3 py-1.5 text-slate-200 hover:bg-slate-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
