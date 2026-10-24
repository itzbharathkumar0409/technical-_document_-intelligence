"use client";

import React, { useState, useEffect, useRef } from "react";
import { DocumentItem } from "@/lib/types";
import { api } from "@/lib/api";
import {
  UploadCloud,
  FileText,
  Trash2,
  Layers,
  Search,
  Filter,
  RefreshCw,
  CheckCircle,
  Clock,
  AlertCircle,
  FileCode,
  File,
  Loader2,
  FolderOpen,
} from "lucide-react";

interface DocumentManagerProps {
  onInspectDocument: (doc: DocumentItem) => void;
  onOpenAuth: () => void;
  isAuthenticated: boolean;
}

export const DocumentManager: React.FC<DocumentManagerProps> = ({
  onInspectDocument,
  onOpenAuth,
  isAuthenticated,
}) => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [dragActive, setDragActive] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadDocuments = async () => {
    if (!isAuthenticated) return;
    setLoading(true);
    try {
      const res = await api.listDocuments(1, 100, statusFilter, search);
      setDocuments(res.items);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, [isAuthenticated, statusFilter]);

  // Polling for processing documents
  useEffect(() => {
    if (!isAuthenticated) return;
    const hasProcessing = documents.some(
      (d) => d.status === "pending" || d.status === "processing"
    );
    if (!hasProcessing) return;

    const interval = setInterval(() => {
      api
        .listDocuments(1, 100, statusFilter, search)
        .then((res) => setDocuments(res.items))
        .catch(() => {});
    }, 2500);

    return () => clearInterval(interval);
  }, [documents, isAuthenticated, statusFilter, search]);

  const handleUploadFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    if (!isAuthenticated) {
      onOpenAuth();
      return;
    }

    setUploading(true);
    setMessage(null);

    let successCount = 0;
    let failedCount = 0;

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      try {
        await api.uploadDocument(file);
        successCount++;
      } catch (err: any) {
        console.error(err);
        failedCount++;
      }
    }

    setUploading(false);
    if (successCount > 0) {
      setMessage({
        type: "success",
        text: `Uploaded ${successCount} document${successCount > 1 ? "s" : ""}. Background ingestion started!`,
      });
      loadDocuments();
    }
    if (failedCount > 0) {
      setMessage({
        type: "error",
        text: `Failed to upload ${failedCount} document${failedCount > 1 ? "s" : ""}. Check format or size.`,
      });
    }

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to delete "${name}" and all its vector embeddings?`)) {
      return;
    }
    try {
      await api.deleteDocument(id);
      setDocuments((prev) => prev.filter((d) => d.id !== id));
      setMessage({ type: "success", text: `Deleted "${name}" successfully.` });
    } catch (err: any) {
      setMessage({ type: "error", text: err.message || "Failed to delete document" });
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleUploadFiles(e.dataTransfer.files);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  const getFormatBadge = (type: string) => {
    switch (type.toLowerCase()) {
      case "pdf":
        return <span className="rounded bg-rose-500/15 border border-rose-500/30 px-1.5 py-0.5 text-[10px] font-bold text-rose-300">PDF</span>;
      case "md":
      case "markdown":
        return <span className="rounded bg-sky-500/15 border border-sky-500/30 px-1.5 py-0.5 text-[10px] font-bold text-sky-300">MD</span>;
      case "docx":
        return <span className="rounded bg-indigo-500/15 border border-indigo-500/30 px-1.5 py-0.5 text-[10px] font-bold text-indigo-300">DOCX</span>;
      case "txt":
        return <span className="rounded bg-slate-500/15 border border-slate-500/30 px-1.5 py-0.5 text-[10px] font-bold text-slate-300">TXT</span>;
      default:
        return <span className="rounded bg-teal-500/15 border border-teal-500/30 px-1.5 py-0.5 text-[10px] font-bold text-teal-300">{type.toUpperCase()}</span>;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-[11px] font-medium text-emerald-400 border border-emerald-500/20">
            <CheckCircle className="h-3 w-3" />
            Ready
          </span>
        );
      case "processing":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 px-2 py-0.5 text-[11px] font-medium text-amber-300 border border-amber-500/20">
            <Loader2 className="h-3 w-3 animate-spin" />
            Indexing
          </span>
        );
      case "pending":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-slate-500/10 px-2 py-0.5 text-[11px] font-medium text-slate-400 border border-slate-500/20">
            <Clock className="h-3 w-3" />
            Queued
          </span>
        );
      case "failed":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-rose-500/10 px-2 py-0.5 text-[11px] font-medium text-rose-400 border border-rose-500/20">
            <AlertCircle className="h-3 w-3" />
            Failed
          </span>
        );
      default:
        return <span className="text-xs text-slate-400">{status}</span>;
    }
  };

  return (
    <div className="mx-auto max-w-7xl p-4 sm:p-6 lg:p-8 space-y-6">
      {/* Top Banner / Heading */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <FolderOpen className="h-6 w-6 text-teal-400" />
            Document Ingestion & Repository
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Uploaded files are parsed, chunked with structure-awareness, embedded, and stored with HNSW vectors in Supabase.
          </p>
        </div>

        <button
          onClick={loadDocuments}
          disabled={loading || !isAuthenticated}
          className="flex items-center self-start gap-1.5 rounded-xl border border-slate-800 bg-slate-900 px-3.5 py-2 text-xs font-medium text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-teal-400" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Messages */}
      {message && (
        <div
          className={`rounded-xl p-3 text-xs flex items-center justify-between ${
            message.type === "success"
              ? "border border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
              : "border border-rose-500/30 bg-rose-500/10 text-rose-300"
          }`}
        >
          <span>{message.text}</span>
          <button onClick={() => setMessage(null)} className="text-slate-400 hover:text-white">
            ×
          </button>
        </div>
      )}

      {/* Drag & Drop Upload Card */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => {
          if (!isAuthenticated) onOpenAuth();
          else fileInputRef.current?.click();
        }}
        className={`relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-8 text-center transition-all cursor-pointer ${
          dragActive
            ? "border-teal-400 bg-teal-500/10 scale-[1.01]"
            : "border-slate-800 bg-slate-900/40 hover:border-slate-700 hover:bg-slate-900/70"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.docx,.txt,.md"
          onChange={(e) => handleUploadFiles(e.target.files)}
          className="hidden"
        />

        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-teal-500/10 border border-teal-500/30 text-teal-400 mb-3 shadow-lg shadow-teal-500/10">
          {uploading ? (
            <Loader2 className="h-7 w-7 animate-spin" />
          ) : (
            <UploadCloud className="h-7 w-7" />
          )}
        </div>

        <h3 className="text-sm font-semibold text-white">
          {uploading
            ? "Uploading & Starting Ingestion..."
            : "Click to upload or drag & drop files here"}
        </h3>
        <p className="text-xs text-slate-400 mt-1 max-w-sm">
          Supports <span className="text-teal-400 font-medium">PDF, DOCX, Markdown, TXT</span> up to 50MB per file.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-2 mt-4 text-[11px] text-slate-500">
          <span className="rounded bg-slate-800 px-2 py-0.5">Semantic Structure Chunking</span>
          <span className="rounded bg-slate-800 px-2 py-0.5">all-MiniLM-L6-v2 Embeddings</span>
          <span className="rounded bg-slate-800 px-2 py-0.5">Full-Text TSVECTOR Index</span>
        </div>
      </div>

      {/* Sample Docs Info Banner */}
      <div className="rounded-xl border border-teal-500/20 bg-teal-500/5 p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
        <div className="space-y-0.5">
          <span className="font-semibold text-teal-300">Quick Test Tip:</span>
          <p className="text-slate-300">
            You have sample files ready in your project directory: <code className="text-teal-300 font-mono">sample_docs/architecture_guide.md</code> and <code className="text-teal-300 font-mono">api_reference.md</code>.
          </p>
        </div>
        <span className="rounded-lg bg-teal-500/10 border border-teal-500/30 px-2.5 py-1 text-teal-300 font-medium shrink-0">
          Upload them above to test Q&A!
        </span>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && loadDocuments()}
            placeholder="Search documents by name..."
            className="w-full rounded-xl border border-slate-800 bg-slate-900/80 py-2 pl-9 pr-3 text-xs text-slate-200 placeholder-slate-500 focus:border-teal-500/50 focus:outline-none"
          />
        </div>

        <div className="flex items-center gap-2 self-end sm:self-auto">
          <Filter className="h-3.5 w-3.5 text-slate-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-xl border border-slate-800 bg-slate-900/80 px-3 py-1.5 text-xs text-slate-300 focus:border-teal-500/50 focus:outline-none"
          >
            <option value="all">All Statuses</option>
            <option value="completed">Ready (Completed)</option>
            <option value="processing">Processing</option>
            <option value="pending">Queued</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </div>

      {/* Documents Table / Grid */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 overflow-hidden shadow-xl">
        {!isAuthenticated ? (
          <div className="text-center py-16 p-4">
            <FileText className="mx-auto h-8 w-8 text-slate-600 mb-2" />
            <h4 className="text-sm font-semibold text-slate-300">Sign in to view your documents</h4>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Your uploaded files are securely isolated and tied to your user account.
            </p>
            <button
              onClick={onOpenAuth}
              className="mt-4 rounded-xl bg-gradient-to-r from-teal-500 to-cyan-500 px-4 py-2 text-xs font-semibold text-slate-950"
            >
              Sign In / Register
            </button>
          </div>
        ) : loading && documents.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 gap-3 text-slate-400 text-xs">
            <Loader2 className="h-6 w-6 animate-spin text-teal-400" />
            <span>Loading documents from Supabase...</span>
          </div>
        ) : documents.length === 0 ? (
          <div className="text-center py-16 p-4">
            <FileText className="mx-auto h-8 w-8 text-slate-600 mb-2" />
            <h4 className="text-sm font-semibold text-slate-300">No documents uploaded yet</h4>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Use the upload area above to upload technical specifications, architectural guides, or API references.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-800 bg-slate-950/60 text-slate-400">
                <tr>
                  <th className="py-3 px-4 font-medium">Document</th>
                  <th className="py-3 px-4 font-medium">Type</th>
                  <th className="py-3 px-4 font-medium">Size</th>
                  <th className="py-3 px-4 font-medium">Status</th>
                  <th className="py-3 px-4 font-medium">Chunks</th>
                  <th className="py-3 px-4 font-medium">Uploaded</th>
                  <th className="py-3 px-4 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3.5 px-4 font-medium text-white max-w-xs truncate">
                      <div className="flex items-center gap-2.5">
                        <FileText className="h-4 w-4 text-teal-400 shrink-0" />
                        <span className="truncate">{doc.original_filename}</span>
                      </div>
                      {doc.error_message && (
                        <p className="text-[10px] text-rose-400 mt-0.5 truncate">
                          {doc.error_message}
                        </p>
                      )}
                    </td>
                    <td className="py-3.5 px-4">{getFormatBadge(doc.file_type)}</td>
                    <td className="py-3.5 px-4 text-slate-400 font-mono">
                      {formatFileSize(doc.file_size)}
                    </td>
                    <td className="py-3.5 px-4">{getStatusBadge(doc.status)}</td>
                    <td className="py-3.5 px-4 font-mono text-slate-300">
                      {doc.chunk_count !== undefined ? doc.chunk_count : "—"}
                    </td>
                    <td className="py-3.5 px-4 text-slate-400">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3.5 px-4 text-right space-x-2">
                      <button
                        onClick={() => onInspectDocument(doc)}
                        title="Inspect Chunks"
                        className="inline-flex items-center gap-1 rounded-lg border border-slate-700 bg-slate-800 px-2.5 py-1 text-[11px] text-slate-300 hover:bg-slate-700 hover:text-white transition-colors"
                      >
                        <Layers className="h-3 w-3 text-teal-400" />
                        Chunks
                      </button>
                      <button
                        onClick={() => handleDelete(doc.id, doc.original_filename)}
                        title="Delete Document"
                        className="inline-flex items-center rounded-lg border border-slate-800 bg-slate-900/80 p-1.5 text-slate-400 hover:bg-rose-500/10 hover:border-rose-500/30 hover:text-rose-400 transition-colors"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
