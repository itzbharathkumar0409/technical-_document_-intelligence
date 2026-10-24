"use client";

import React from "react";
import { User } from "@/lib/types";
import {
  Sparkles,
  FileText,
  MessageSquare,
  BarChart3,
  Settings,
  LogIn,
  LogOut,
  Database,
  Cpu,
} from "lucide-react";

interface NavbarProps {
  activeTab: "workspace" | "documents" | "analytics" | "settings";
  setActiveTab: (tab: "workspace" | "documents" | "analytics" | "settings") => void;
  currentUser: User | null;
  onOpenAuth: () => void;
  onLogout: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  currentUser,
  onOpenAuth,
  onLogout,
}) => {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand */}
        <div className="flex items-center gap-6">
          <div
            onClick={() => setActiveTab("workspace")}
            className="flex cursor-pointer items-center gap-2.5 transition-opacity hover:opacity-90"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-teal-500 to-cyan-600 shadow-lg shadow-teal-500/20">
              <Sparkles className="h-5 w-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xl font-bold tracking-tight text-white">
                  Doc<span className="text-teal-400">IQ</span>
                </span>
                <span className="rounded-full bg-teal-500/10 px-2 py-0.5 text-[10px] font-semibold tracking-wide text-teal-400 border border-teal-500/20">
                  v0.1
                </span>
              </div>
              <p className="hidden text-[11px] text-slate-400 sm:block">
                Technical Document Intelligence
              </p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1 rounded-xl bg-slate-900/60 p-1 border border-slate-800/60">
            <button
              onClick={() => setActiveTab("workspace")}
              className={`flex items-center gap-2 rounded-lg px-3.5 py-1.5 text-xs font-medium transition-all ${
                activeTab === "workspace"
                  ? "bg-teal-500/15 text-teal-300 border border-teal-500/30 shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
              }`}
            >
              <MessageSquare className="h-3.5 w-3.5" />
              Q&A Workspace
            </button>
            <button
              onClick={() => setActiveTab("documents")}
              className={`flex items-center gap-2 rounded-lg px-3.5 py-1.5 text-xs font-medium transition-all ${
                activeTab === "documents"
                  ? "bg-teal-500/15 text-teal-300 border border-teal-500/30 shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
              }`}
            >
              <FileText className="h-3.5 w-3.5" />
              Documents
            </button>
            <button
              onClick={() => setActiveTab("analytics")}
              className={`flex items-center gap-2 rounded-lg px-3.5 py-1.5 text-xs font-medium transition-all ${
                activeTab === "analytics"
                  ? "bg-teal-500/15 text-teal-300 border border-teal-500/30 shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
              }`}
            >
              <BarChart3 className="h-3.5 w-3.5" />
              Analytics
            </button>
            <button
              onClick={() => setActiveTab("settings")}
              className={`flex items-center gap-2 rounded-lg px-3.5 py-1.5 text-xs font-medium transition-all ${
                activeTab === "settings"
                  ? "bg-teal-500/15 text-teal-300 border border-teal-500/30 shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
              }`}
            >
              <Settings className="h-3.5 w-3.5" />
              Config
            </button>
          </nav>
        </div>

        {/* Right Status & Auth */}
        <div className="flex items-center gap-3">
          {/* Supabase Status Pill */}
          <div className="hidden lg:flex items-center gap-2 rounded-full bg-slate-900/90 px-3 py-1 border border-slate-800 text-xs text-slate-300">
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <Database className="h-3.5 w-3.5 text-teal-400" />
            <span className="text-[11px] text-slate-400">Supabase pgvector</span>
          </div>

          {/* User Section */}
          {currentUser ? (
            <div className="flex items-center gap-3">
              <div className="hidden sm:flex flex-col text-right">
                <span className="text-xs font-semibold text-slate-200">
                  {currentUser.username}
                </span>
                <span className="text-[10px] text-slate-400">{currentUser.email}</span>
              </div>
              <button
                onClick={onLogout}
                title="Log out"
                className="flex items-center gap-1.5 rounded-lg bg-slate-900 border border-slate-800 px-3 py-1.5 text-xs font-medium text-slate-300 transition-colors hover:bg-slate-800 hover:text-rose-300"
              >
                <LogOut className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Logout</span>
              </button>
            </div>
          ) : (
            <button
              onClick={onOpenAuth}
              className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-teal-500 to-cyan-500 px-3.5 py-1.5 text-xs font-semibold text-slate-950 shadow-md shadow-teal-500/20 transition-all hover:opacity-95 hover:shadow-teal-500/30"
            >
              <LogIn className="h-3.5 w-3.5" />
              Sign In / Register
            </button>
          )}
        </div>
      </div>

      {/* Mobile nav */}
      <div className="flex md:hidden border-t border-slate-800/60 bg-slate-950 px-4 py-2 justify-around">
        <button
          onClick={() => setActiveTab("workspace")}
          className={`flex flex-col items-center gap-1 text-[11px] ${
            activeTab === "workspace" ? "text-teal-400 font-semibold" : "text-slate-400"
          }`}
        >
          <MessageSquare className="h-4 w-4" />
          Q&A
        </button>
        <button
          onClick={() => setActiveTab("documents")}
          className={`flex flex-col items-center gap-1 text-[11px] ${
            activeTab === "documents" ? "text-teal-400 font-semibold" : "text-slate-400"
          }`}
        >
          <FileText className="h-4 w-4" />
          Docs
        </button>
        <button
          onClick={() => setActiveTab("analytics")}
          className={`flex flex-col items-center gap-1 text-[11px] ${
            activeTab === "analytics" ? "text-teal-400 font-semibold" : "text-slate-400"
          }`}
        >
          <BarChart3 className="h-4 w-4" />
          Metrics
        </button>
        <button
          onClick={() => setActiveTab("settings")}
          className={`flex flex-col items-center gap-1 text-[11px] ${
            activeTab === "settings" ? "text-teal-400 font-semibold" : "text-slate-400"
          }`}
        >
          <Settings className="h-4 w-4" />
          Config
        </button>
      </div>
    </header>
  );
};
