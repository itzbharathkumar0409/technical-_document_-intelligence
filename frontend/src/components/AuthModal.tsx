"use client";

import React, { useState } from "react";
import { api } from "@/lib/api";
import { User } from "@/lib/types";
import { X, Lock, Mail, User as UserIcon, Sparkles, Loader2, CheckCircle2 } from "lucide-react";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (user: User) => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isRegister) {
        if (!username) {
          throw new Error("Username is required");
        }
        const res = await api.register({ email, username, password });
        onSuccess(res.user);
        onClose();
      } else {
        const res = await api.login({ email, password });
        onSuccess(res.user);
        onClose();
      }
    } catch (err: any) {
      setError(err.message || "Authentication failed. Please check credentials.");
    } finally {
      setLoading(false);
    }
  };

  const handleQuickDemo = () => {
    setEmail("testuser@example.com");
    setPassword("ValidPassword123!");
    setUsername("testuser");
    setError(null);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900/95 p-6 shadow-2xl shadow-teal-950/30">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors"
        >
          <X className="h-4 w-4" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-teal-500 to-cyan-600 shadow-md shadow-teal-500/20">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">
              {isRegister ? "Create DocIQ Account" : "Sign In to DocIQ"}
            </h2>
            <p className="text-xs text-slate-400">
              Access your documents and citation-backed Q&A
            </p>
          </div>
        </div>

        {/* Tab switch */}
        <div className="flex rounded-xl bg-slate-950/80 p-1 mb-5 border border-slate-800/80">
          <button
            type="button"
            onClick={() => {
              setIsRegister(false);
              setError(null);
            }}
            className={`flex-1 py-1.5 text-xs font-medium rounded-lg transition-all ${
              !isRegister
                ? "bg-teal-500/15 text-teal-300 border border-teal-500/30"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setIsRegister(true);
              setError(null);
            }}
            className={`flex-1 py-1.5 text-xs font-medium rounded-lg transition-all ${
              isRegister
                ? "bg-teal-500/15 text-teal-300 border border-teal-500/30"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Register
          </button>
        </div>

        {/* Error notice */}
        {error && (
          <div className="mb-4 rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-300">
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {isRegister && (
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Username
              </label>
              <div className="relative">
                <UserIcon className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="johndoe"
                  className="w-full rounded-xl border border-slate-800 bg-slate-950/60 py-2 pl-9 pr-3 text-sm text-slate-100 placeholder-slate-500 focus:border-teal-500/50 focus:outline-none focus:ring-1 focus:ring-teal-500/50"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Email Address
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="developer@example.com"
                className="w-full rounded-xl border border-slate-800 bg-slate-950/60 py-2 pl-9 pr-3 text-sm text-slate-100 placeholder-slate-500 focus:border-teal-500/50 focus:outline-none focus:ring-1 focus:ring-teal-500/50"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full rounded-xl border border-slate-800 bg-slate-950/60 py-2 pl-9 pr-3 text-sm text-slate-100 placeholder-slate-500 focus:border-teal-500/50 focus:outline-none focus:ring-1 focus:ring-teal-500/50"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-teal-500 to-cyan-500 py-2.5 text-sm font-semibold text-slate-950 shadow-md shadow-teal-500/20 hover:opacity-95 disabled:opacity-50 transition-all"
          >
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            {isRegister ? "Create Account" : "Sign In"}
          </button>
        </form>

        {/* Demo Fast-Fill */}
        <div className="mt-5 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs">
          <span className="text-slate-400">Quick Testing:</span>
          <button
            type="button"
            onClick={handleQuickDemo}
            className="flex items-center gap-1.5 text-teal-400 hover:text-teal-300 font-medium"
          >
            <CheckCircle2 className="h-3.5 w-3.5" />
            Fill Test Credentials
          </button>
        </div>
      </div>
    </div>
  );
};
