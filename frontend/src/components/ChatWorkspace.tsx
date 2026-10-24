"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Conversation,
  MessageItem,
  CitationDetail,
  DocumentItem,
  AnswerResponse,
} from "@/lib/types";
import { api } from "@/lib/api";
import {
  Send,
  Plus,
  Trash2,
  MessageSquare,
  Sparkles,
  Bot,
  User,
  ThumbsUp,
  ThumbsDown,
  Clock,
  AlertTriangle,
  ExternalLink,
  Loader2,
  FileText,
  Filter,
  CheckCircle2,
  Zap,
} from "lucide-react";

interface ChatWorkspaceProps {
  onSelectCitation: (citation: CitationDetail, allCitations: CitationDetail[]) => void;
  onOpenAuth: () => void;
  isAuthenticated: boolean;
}

export const ChatWorkspace: React.FC<ChatWorkspaceProps> = ({
  onSelectCitation,
  onOpenAuth,
  isAuthenticated,
}) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [inputQuestion, setInputQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Document scope filter
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [scopeDropdownOpen, setScopeDropdownOpen] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Load conversations and available documents
  useEffect(() => {
    if (!isAuthenticated) return;
    loadConversations();
    loadDocuments();
  }, [isAuthenticated]);

  const loadConversations = async () => {
    try {
      const res = await api.listConversations();
      setConversations(res.conversations);
      if (res.conversations.length > 0 && !currentConversationId) {
        selectConversation(res.conversations[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const loadDocuments = async () => {
    try {
      const res = await api.listDocuments(1, 100);
      setDocuments(res.items.filter((d) => d.status === "completed"));
    } catch (err) {
      console.error(err);
    }
  };

  const selectConversation = async (convId: string) => {
    setCurrentConversationId(convId);
    setLoadingHistory(true);
    try {
      const msgs = await api.getConversationMessages(convId);
      setMessages(msgs);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleNewConversation = () => {
    setCurrentConversationId(null);
    setMessages([]);
    if (textareaRef.current) textareaRef.current.focus();
  };

  const handleDeleteConversation = async (convId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.deleteConversation(convId);
      setConversations((prev) => prev.filter((c) => c.id !== convId));
      if (currentConversationId === convId) {
        handleNewConversation();
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Scroll to bottom on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async (questionText?: string) => {
    const q = questionText || inputQuestion.trim();
    if (!q || loading) return;

    if (!isAuthenticated) {
      onOpenAuth();
      return;
    }

    setInputQuestion("");

    // Optimistically add user message
    const tempUserMsg: MessageItem = {
      id: "temp-" + Date.now(),
      role: "user",
      content: q,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, tempUserMsg]);
    setLoading(true);

    try {
      const res: AnswerResponse = await api.askQuestion(
        q,
        currentConversationId,
        selectedDocIds.length > 0 ? selectedDocIds : null
      );

      // If new conversation was created, update ID and refresh conversation list
      if (!currentConversationId || currentConversationId !== res.conversation_id) {
        setCurrentConversationId(res.conversation_id);
        loadConversations();
      }

      // Add assistant message
      const assistantMsg: MessageItem = {
        id: res.message_id,
        role: "assistant",
        content: res.answer,
        citations: res.citations,
        insufficient_evidence: res.insufficient_evidence,
        latency_breakdown: res.latency_breakdown,
        latency_ms: res.latency_breakdown.total_ms,
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const errorMsg: MessageItem = {
        id: "err-" + Date.now(),
        role: "assistant",
        content: `Error: ${err.message || "Failed to retrieve response from DocIQ."}`,
        insufficient_evidence: true,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (msgId: string, rating: number) => {
    try {
      await api.submitFeedback(msgId, rating);
      setMessages((prev) =>
        prev.map((m) => (m.id === msgId ? { ...m, feedback_rating: rating } : m))
      );
    } catch (err) {
      console.error(err);
    }
  };

  const renderContentWithCitations = (
    content: string,
    citations: CitationDetail[] = []
  ) => {
    // Regular expression to identify citation labels like [S1], [S2]
    const regex = /(\[S\d+\])/g;
    const parts = content.split(regex);

    return parts.map((part, index) => {
      const match = part.match(/^\[S\d+\]$/);
      if (match) {
        const label = match[0];
        const citation = citations.find((c) => c.citation_label === label);
        return (
          <button
            key={index}
            onClick={() => citation && onSelectCitation(citation, citations)}
            className="inline-flex items-center gap-1 rounded bg-teal-500/20 text-teal-300 border border-teal-500/40 px-1.5 py-0.2 mx-0.5 text-xs font-mono font-semibold hover:bg-teal-500/30 transition-colors cursor-pointer"
            title={citation ? `${citation.filename} (Page ${citation.page_number || "—"})` : "Source citation"}
          >
            {label}
          </button>
        );
      }
      return <span key={index}>{part}</span>;
    });
  };

  const samplePrompts = [
    "What is the system architecture of DocIQ?",
    "Summarize the API authentication endpoints and flow",
    "Explain the document ingestion and structure chunking pipeline",
  ];

  return (
    <div className="mx-auto flex h-[calc(100vh-4rem)] max-w-7xl overflow-hidden p-2 sm:p-4 gap-4">
      {/* Left Sidebar: Conversations & Scope */}
      <div className="hidden md:flex w-72 flex-col rounded-2xl border border-slate-800 bg-slate-900/60 p-4 space-y-4">
        {/* New Chat Button */}
        <button
          onClick={handleNewConversation}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-teal-500 to-cyan-500 py-2.5 px-4 text-xs font-semibold text-slate-950 shadow-md shadow-teal-500/20 hover:opacity-95 transition-all"
        >
          <Plus className="h-4 w-4" />
          New Q&A Thread
        </button>

        {/* Document Scope Filter */}
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center gap-1.5 font-medium text-slate-300">
              <Filter className="h-3.5 w-3.5 text-teal-400" />
              Document Scope
            </span>
            <span className="text-[10px]">
              {selectedDocIds.length === 0 ? "All Docs" : `${selectedDocIds.length} active`}
            </span>
          </div>

          <div className="max-h-28 overflow-y-auto space-y-1 text-xs">
            {documents.length === 0 ? (
              <p className="text-[11px] text-slate-500 italic">No completed documents.</p>
            ) : (
              documents.map((doc) => {
                const isSelected = selectedDocIds.includes(doc.id);
                return (
                  <label
                    key={doc.id}
                    className="flex items-center gap-2 rounded-lg p-1.5 hover:bg-slate-800/60 cursor-pointer text-[11px]"
                  >
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => {
                        setSelectedDocIds((prev) =>
                          isSelected ? prev.filter((id) => id !== doc.id) : [...prev, doc.id]
                        );
                      }}
                      className="rounded border-slate-700 text-teal-500 focus:ring-0"
                    />
                    <span className="truncate text-slate-300">{doc.original_filename}</span>
                  </label>
                );
              })
            )}
          </div>
        </div>

        {/* Conversations List */}
        <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 px-2">
            History
          </span>

          {conversations.length === 0 ? (
            <p className="text-xs text-slate-500 p-2 italic">No past conversations</p>
          ) : (
            conversations.map((conv) => (
              <div
                key={conv.id}
                onClick={() => selectConversation(conv.id)}
                className={`group flex items-center justify-between rounded-xl px-3 py-2 text-xs transition-colors cursor-pointer ${
                  conv.id === currentConversationId
                    ? "bg-teal-500/15 text-teal-300 border border-teal-500/30"
                    : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
                }`}
              >
                <div className="flex items-center gap-2 truncate">
                  <MessageSquare className="h-3.5 w-3.5 shrink-0 text-slate-500 group-hover:text-teal-400" />
                  <span className="truncate">{conv.title}</span>
                </div>
                <button
                  onClick={(e) => handleDeleteConversation(conv.id, e)}
                  className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-rose-400 transition-opacity"
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Center Chat View */}
      <div className="flex flex-1 flex-col rounded-2xl border border-slate-800 bg-slate-900/60 overflow-hidden shadow-2xl">
        {/* Messages Scroll Area */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center max-w-lg mx-auto py-12 space-y-6">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-500 to-cyan-600 shadow-xl shadow-teal-500/20">
                <Sparkles className="h-8 w-8 text-white" />
              </div>

              <div className="space-y-2">
                <h2 className="text-lg font-bold text-white">
                  Technical Document Intelligence
                </h2>
                <p className="text-xs text-slate-400">
                  Ask natural language questions against your uploaded technical docs. Answers are synthesized with verifiable, sentence-level citation anchors.
                </p>
              </div>

              {/* Sample Prompts */}
              <div className="w-full space-y-2 pt-2">
                <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">
                  Suggested Questions
                </span>
                <div className="flex flex-col gap-2">
                  {samplePrompts.map((prompt, i) => (
                    <button
                      key={i}
                      onClick={() => handleSend(prompt)}
                      className="text-left rounded-xl border border-slate-800 bg-slate-950/70 p-3 text-xs text-slate-300 hover:border-teal-500/40 hover:text-teal-300 hover:bg-slate-900 transition-all"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3 text-xs leading-relaxed ${
                  msg.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                {msg.role === "assistant" && (
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-teal-500/15 border border-teal-500/30 text-teal-400 shadow-sm mt-0.5">
                    <Bot className="h-4 w-4" />
                  </div>
                )}

                <div
                  className={`flex flex-col max-w-2xl rounded-2xl p-4 space-y-2.5 ${
                    msg.role === "user"
                      ? "bg-teal-500 text-slate-950 font-medium rounded-tr-sm shadow-md shadow-teal-500/10"
                      : "bg-slate-950/80 border border-slate-800 text-slate-200 rounded-tl-sm shadow-xl"
                  }`}
                >
                  {/* Message body */}
                  <div className="whitespace-pre-wrap font-sans text-xs leading-6">
                    {msg.role === "assistant"
                      ? renderContentWithCitations(msg.content, msg.citations)
                      : msg.content}
                  </div>

                  {/* Insufficient Evidence Warning */}
                  {msg.insufficient_evidence && (
                    <div className="flex items-center gap-2 rounded-lg bg-amber-500/10 border border-amber-500/20 p-2.5 text-[11px] text-amber-300">
                      <AlertTriangle className="h-4 w-4 shrink-0 text-amber-400" />
                      <span>
                        Insufficient evidence: retrieved document passages do not contain high confidence matches for this query.
                      </span>
                    </div>
                  )}

                  {/* Citations Footer & Metrics (Assistant Only) */}
                  {msg.role === "assistant" && (
                    <div className="pt-2 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-400">
                      {/* Latency badge */}
                      {msg.latency_breakdown && (
                        <div className="flex items-center gap-2 font-mono">
                          <span className="flex items-center gap-1 text-slate-400">
                            <Clock className="h-3 w-3 text-teal-400" />
                            {msg.latency_breakdown.total_ms}ms total
                          </span>
                          <span className="text-slate-600">|</span>
                          <span className="text-slate-500">
                            retrieval: {msg.latency_breakdown.retrieval_ms}ms
                          </span>
                          <span className="text-slate-600">|</span>
                          <span className="text-slate-500">
                            gen: {msg.latency_breakdown.generation_ms}ms
                          </span>
                        </div>
                      )}

                      {/* Citations Button */}
                      {msg.citations && msg.citations.length > 0 && (
                        <button
                          onClick={() => onSelectCitation(msg.citations![0], msg.citations!)}
                          className="flex items-center gap-1 text-teal-400 hover:text-teal-300 font-medium underline-offset-2 hover:underline"
                        >
                          <FileText className="h-3 w-3" />
                          {msg.citations.length} citation{msg.citations.length > 1 ? "s" : ""}
                        </button>
                      )}

                      {/* Feedback Buttons */}
                      <div className="flex items-center gap-1 ml-auto">
                        <button
                          onClick={() => handleFeedback(msg.id, 1)}
                          className={`rounded p-1 transition-colors ${
                            msg.feedback_rating === 1
                              ? "text-emerald-400 bg-emerald-500/10"
                              : "text-slate-500 hover:text-slate-300"
                          }`}
                          title="Accurate & helpful"
                        >
                          <ThumbsUp className="h-3.5 w-3.5" />
                        </button>
                        <button
                          onClick={() => handleFeedback(msg.id, -1)}
                          className={`rounded p-1 transition-colors ${
                            msg.feedback_rating === -1
                              ? "text-rose-400 bg-rose-500/10"
                              : "text-slate-500 hover:text-slate-300"
                          }`}
                          title="Inaccurate or unsupported"
                        >
                          <ThumbsDown className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                {msg.role === "user" && (
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-slate-800 text-slate-300 mt-0.5">
                    <User className="h-4 w-4" />
                  </div>
                )}
              </div>
            ))
          )}

          {loading && (
            <div className="flex gap-3 justify-start items-center text-xs text-slate-400">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-teal-500/15 border border-teal-500/30 text-teal-400 shadow-sm">
                <Loader2 className="h-4 w-4 animate-spin" />
              </div>
              <div className="rounded-2xl border border-slate-800 bg-slate-950/80 px-4 py-3 text-slate-400 flex items-center gap-2">
                <span>Retrieving hybrid vectors and synthesizing grounded answer...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="border-t border-slate-800 p-3 sm:p-4 bg-slate-950/80">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-end gap-2"
          >
            <textarea
              ref={textareaRef}
              rows={2}
              value={inputQuestion}
              onChange={(e) => setInputQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder={
                isAuthenticated
                  ? "Ask anything about your uploaded technical documents... (Press Enter to send)"
                  : "Please sign in to ask questions against your documents."
              }
              className="flex-1 resize-none rounded-xl border border-slate-800 bg-slate-900/90 p-3 text-xs text-slate-200 placeholder-slate-500 focus:border-teal-500/50 focus:outline-none focus:ring-1 focus:ring-teal-500/50 leading-relaxed"
            />

            <button
              type="submit"
              disabled={loading || !inputQuestion.trim()}
              className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-r from-teal-500 to-cyan-500 text-slate-950 shadow-md shadow-teal-500/20 hover:opacity-95 disabled:opacity-40 transition-all shrink-0"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </button>
          </form>

          <div className="mt-2 flex items-center justify-between text-[11px] text-slate-500 px-1">
            <span>Powered by Supabase pgvector + all-MiniLM-L6-v2 embeddings</span>
            <span>Shift + Enter for new line</span>
          </div>
        </div>
      </div>
    </div>
  );
};
