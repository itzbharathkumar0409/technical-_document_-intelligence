"use client";

import React, { useEffect, useState } from "react";
import { AnalyticsResponse } from "@/lib/types";
import { api } from "@/lib/api";
import {
  BarChart3,
  FileText,
  Layers,
  MessageSquare,
  Clock,
  ThumbsUp,
  ThumbsDown,
  AlertTriangle,
  RefreshCw,
  Loader2,
  PieChart,
  Zap,
} from "lucide-react";

interface AnalyticsViewProps {
  isAuthenticated: boolean;
  onOpenAuth: () => void;
}

export const AnalyticsView: React.FC<AnalyticsViewProps> = ({
  isAuthenticated,
  onOpenAuth,
}) => {
  const [data, setData] = useState<AnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = async () => {
    if (!isAuthenticated) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.getAnalytics();
      setData(res);
    } catch (err: any) {
      setError(err.message || "Failed to load metrics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [isAuthenticated]);

  if (!isAuthenticated) {
    return (
      <div className="mx-auto max-w-7xl p-8 text-center py-20 space-y-4">
        <BarChart3 className="mx-auto h-12 w-12 text-slate-600" />
        <h2 className="text-lg font-bold text-white">Analytics Dashboard</h2>
        <p className="text-xs text-slate-400 max-w-md mx-auto">
          Sign in to view real measured metrics for document indexing, query latencies, and citation grounding accuracy.
        </p>
        <button
          onClick={onOpenAuth}
          className="rounded-xl bg-gradient-to-r from-teal-500 to-cyan-500 px-4 py-2 text-xs font-semibold text-slate-950 shadow-md shadow-teal-500/20"
        >
          Sign In / Register
        </button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl p-4 sm:p-6 lg:p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <BarChart3 className="h-6 w-6 text-teal-400" />
            System Metrics & Performance Analytics
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real measured analytics from Supabase queries, hybrid retrieval times, and user feedback.
          </p>
        </div>

        <button
          onClick={fetchAnalytics}
          disabled={loading}
          className="flex items-center gap-1.5 rounded-xl border border-slate-800 bg-slate-900 px-3.5 py-2 text-xs font-medium text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-teal-400" : ""}`} />
          Refresh
        </button>
      </div>

      {loading && !data && (
        <div className="flex flex-col items-center justify-center py-20 gap-3 text-slate-400 text-xs">
          <Loader2 className="h-6 w-6 animate-spin text-teal-400" />
          <span>Measuring metrics from Supabase database...</span>
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-xs text-rose-300">
          {error}
        </div>
      )}

      {data && (
        <>
          {/* Key Metric Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 space-y-2">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-xs font-medium">Total Documents</span>
                <FileText className="h-4 w-4 text-teal-400" />
              </div>
              <div className="text-2xl font-bold text-white">{data.total_documents}</div>
              <div className="text-[11px] text-slate-500">Indexed in storage</div>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 space-y-2">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-xs font-medium">Indexed Chunks</span>
                <Layers className="h-4 w-4 text-cyan-400" />
              </div>
              <div className="text-2xl font-bold text-white">{data.total_chunks}</div>
              <div className="text-[11px] text-slate-500">HNSW pgvector vectors</div>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 space-y-2">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-xs font-medium">Total Queries</span>
                <MessageSquare className="h-4 w-4 text-emerald-400" />
              </div>
              <div className="text-2xl font-bold text-white">{data.total_messages}</div>
              <div className="text-[11px] text-slate-500">Across {data.total_conversations} threads</div>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 space-y-2">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-xs font-medium">Avg Latency</span>
                <Clock className="h-4 w-4 text-amber-400" />
              </div>
              <div className="text-2xl font-bold text-white font-mono">
                {data.avg_latency_ms ? `${data.avg_latency_ms}ms` : "—"}
              </div>
              <div className="text-[11px] text-slate-500">End-to-end response</div>
            </div>
          </div>

          {/* Deep Dive Breakdown Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Latency Pipeline Breakdown */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 space-y-4">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Zap className="h-4 w-4 text-amber-400" />
                Pipeline Latency Distribution
              </h3>

              <div className="space-y-3 pt-2">
                <div>
                  <div className="flex justify-between text-xs text-slate-300 mb-1">
                    <span>Vector & Keyword Retrieval</span>
                    <span className="font-mono text-teal-400">
                      {data.avg_retrieval_ms || 0}ms
                    </span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-teal-400"
                      style={{
                        width: `${
                          data.avg_latency_ms
                            ? Math.min(100, ((data.avg_retrieval_ms || 0) / data.avg_latency_ms) * 100)
                            : 25
                        }%`,
                      }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs text-slate-300 mb-1">
                    <span>LLM Synthesis & Citation Verification</span>
                    <span className="font-mono text-cyan-400">
                      {data.avg_generation_ms || 0}ms
                    </span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-cyan-400"
                      style={{
                        width: `${
                          data.avg_latency_ms
                            ? Math.min(100, ((data.avg_generation_ms || 0) / data.avg_latency_ms) * 100)
                            : 75
                        }%`,
                      }}
                    />
                  </div>
                </div>
              </div>

              <p className="text-[11px] text-slate-500 pt-2 border-t border-slate-800/60">
                Hybrid retrieval combines pgvector cosine similarity with PostgreSQL tsvector full-text search.
              </p>
            </div>

            {/* User Feedback & Hallucination Defense */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 space-y-4">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <ThumbsUp className="h-4 w-4 text-emerald-400" />
                Accuracy & Citation Feedback
              </h3>

              <div className="grid grid-cols-2 gap-3 pt-2">
                <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4 flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/15 text-emerald-400">
                    <ThumbsUp className="h-5 w-5" />
                  </div>
                  <div>
                    <div className="text-xl font-bold text-white">{data.feedback_positive}</div>
                    <div className="text-[11px] text-slate-400">Helpful Answers</div>
                  </div>
                </div>

                <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-4 flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-500/15 text-rose-400">
                    <ThumbsDown className="h-5 w-5" />
                  </div>
                  <div>
                    <div className="text-xl font-bold text-white">{data.feedback_negative}</div>
                    <div className="text-[11px] text-slate-400">Reported Issues</div>
                  </div>
                </div>
              </div>

              <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-3 flex items-center justify-between text-xs text-amber-300">
                <span className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-amber-400" />
                  Insufficient Evidence Guardrail Flags:
                </span>
                <span className="font-bold font-mono">
                  {data.insufficient_evidence_count} queries
                </span>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
