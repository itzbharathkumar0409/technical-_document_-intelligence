"use client";

import React from "react";
import {
  Settings,
  Database,
  Cpu,
  Layers,
  ShieldCheck,
  HardDrive,
  Sliders,
  CheckCircle2,
} from "lucide-react";

export const SettingsView: React.FC = () => {
  return (
    <div className="mx-auto max-w-7xl p-4 sm:p-6 lg:p-8 space-y-6">
      {/* Heading */}
      <div>
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <Settings className="h-6 w-6 text-teal-400" />
          System Configuration & Pipeline Parameters
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Active infrastructure, vector database connections, and RAG retrieval settings.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Database & Vector Store Card */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 space-y-4 shadow-xl">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-500/15 border border-teal-500/30 text-teal-400">
              <Database className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">Database & Vector Store</h3>
              <p className="text-xs text-slate-400">Supabase Managed PostgreSQL 17</p>
            </div>
          </div>

          <div className="space-y-3 pt-2 text-xs">
            <div className="flex items-center justify-between border-b border-slate-800/60 pb-2">
              <span className="text-slate-400">Host</span>
              <span className="font-mono text-slate-200">db.gevsekvgmlfzkilafnqn.supabase.co</span>
            </div>
            <div className="flex items-center justify-between border-b border-slate-800/60 pb-2">
              <span className="text-slate-400">Extension</span>
              <span className="flex items-center gap-1.5 text-emerald-400 font-medium">
                <CheckCircle2 className="h-3.5 w-3.5" />
                pgvector (HNSW Index Active)
              </span>
            </div>
            <div className="flex items-center justify-between border-b border-slate-800/60 pb-2">
              <span className="text-slate-400">Embedding Dimension</span>
              <span className="font-mono text-teal-400">384 dimensions</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Full-Text Search</span>
              <span className="text-slate-200 font-medium">PostgreSQL TSVECTOR + GIN index</span>
            </div>
          </div>
        </div>

        {/* Embedding & LLM Card */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 space-y-4 shadow-xl">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-500/15 border border-cyan-500/30 text-cyan-400">
              <Cpu className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">Models & Inference Engine</h3>
              <p className="text-xs text-slate-400">Embedding models and generation fallbacks</p>
            </div>
          </div>

          <div className="space-y-3 pt-2 text-xs">
            <div className="flex items-center justify-between border-b border-slate-800/60 pb-2">
              <span className="text-slate-400">Embedding Model</span>
              <span className="font-mono text-cyan-400">all-MiniLM-L6-v2 (sentence-transformers)</span>
            </div>
            <div className="flex items-center justify-between border-b border-slate-800/60 pb-2">
              <span className="text-slate-400">Embedding Mode</span>
              <span className="text-slate-200">Local Zero-Dependency Fallback</span>
            </div>
            <div className="flex items-center justify-between border-b border-slate-800/60 pb-2">
              <span className="text-slate-400">LLM Provider</span>
              <span className="font-mono text-slate-200">Ollama (llama3.1) / OpenAI compatible</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Hallucination Mitigation</span>
              <span className="text-emerald-400 font-medium">Verbatim Citation Grounding</span>
            </div>
          </div>
        </div>

        {/* Retrieval Parameters Card */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 space-y-4 shadow-xl">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500/15 border border-amber-500/30 text-amber-400">
              <Sliders className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">Hybrid Retrieval Pipeline</h3>
              <p className="text-xs text-slate-400">Reciprocal Rank Fusion & Chunker tuning</p>
            </div>
          </div>

          <div className="space-y-3 pt-2 text-xs">
            <div className="flex items-center justify-between border-b border-slate-800/60 pb-2">
              <span className="text-slate-400">Vector Top-K</span>
              <span className="font-mono text-slate-200">20 passages</span>
            </div>
            <div className="flex items-center justify-between border-b border-slate-800/60 pb-2">
              <span className="text-slate-400">Keyword BM25/TSVECTOR Top-K</span>
              <span className="font-mono text-slate-200">20 passages</span>
            </div>
            <div className="flex items-center justify-between border-b border-slate-800/60 pb-2">
              <span className="text-slate-400">Final Context Window Top-K</span>
              <span className="font-mono text-teal-400 font-semibold">8 chunks sent to prompt</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Chunk Target Size</span>
              <span className="font-mono text-slate-200">800 tokens (120 token overlap)</span>
            </div>
          </div>
        </div>

        {/* Security & Isolation */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 space-y-4 shadow-xl">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-400">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">Security & Data Isolation</h3>
              <p className="text-xs text-slate-400">Enterprise tenant protection</p>
            </div>
          </div>

          <div className="space-y-3 pt-2 text-xs">
            <div className="flex items-center justify-between border-b border-slate-800/60 pb-2">
              <span className="text-slate-400">Authentication</span>
              <span className="text-slate-200">JWT Bearer (HS256) + bcrypt rounds 12</span>
            </div>
            <div className="flex items-center justify-between border-b border-slate-800/60 pb-2">
              <span className="text-slate-400">Ownership Scoping</span>
              <span className="text-emerald-400 font-medium">Strict user_id foreign key in all queries</span>
            </div>
            <div className="flex items-center justify-between border-b border-slate-800/60 pb-2">
              <span className="text-slate-400">Prompt Injection Defense</span>
              <span className="text-slate-200">Delimited XML tags + strict schema guardrails</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">File Sanitization</span>
              <span className="text-slate-200">Path traversal protection & MIME verification</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
