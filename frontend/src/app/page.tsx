"use client";

import React, { useState, useEffect } from "react";
import { User, DocumentItem, CitationDetail } from "@/lib/types";
import { api, getToken } from "@/lib/api";
import { Navbar } from "@/components/Navbar";
import { ChatWorkspace } from "@/components/ChatWorkspace";
import { DocumentManager } from "@/components/DocumentManager";
import { AnalyticsView } from "@/components/AnalyticsView";
import { SettingsView } from "@/components/SettingsView";
import { CitationDrawer } from "@/components/CitationDrawer";
import { ChunkViewerModal } from "@/components/ChunkViewerModal";
import { AuthModal } from "@/components/AuthModal";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"workspace" | "documents" | "analytics" | "settings">("workspace");
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [authModalOpen, setAuthModalOpen] = useState(false);

  // Citation inspection drawer
  const [inspectedCitations, setInspectedCitations] = useState<CitationDetail[]>([]);
  const [activeCitation, setActiveCitation] = useState<CitationDetail | null>(null);

  // Document chunk inspection modal
  const [inspectedDocument, setInspectedDocument] = useState<DocumentItem | null>(null);

  // Initial auth check
  useEffect(() => {
    const token = getToken();
    if (token) {
      api
        .getMe()
        .then((user) => setCurrentUser(user))
        .catch(() => {
          api.logout();
          setCurrentUser(null);
        });
    }
  }, []);

  const handleOpenCitation = (
    citation: CitationDetail,
    allCitations: CitationDetail[]
  ) => {
    setInspectedCitations(allCitations);
    setActiveCitation(citation);
  };

  const handleCloseCitation = () => {
    setActiveCitation(null);
    setInspectedCitations([]);
  };

  const handleLogout = () => {
    api.logout();
    setCurrentUser(null);
  };

  return (
    <div className="flex min-h-screen flex-col bg-[#090d16] text-slate-100 selection:bg-teal-500/30 selection:text-teal-200">
      {/* Navigation */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        currentUser={currentUser}
        onOpenAuth={() => setAuthModalOpen(true)}
        onLogout={handleLogout}
      />

      {/* Main Content Area */}
      <main className="flex-1">
        {activeTab === "workspace" && (
          <ChatWorkspace
            onSelectCitation={handleOpenCitation}
            onOpenAuth={() => setAuthModalOpen(true)}
            isAuthenticated={!!currentUser}
          />
        )}

        {activeTab === "documents" && (
          <DocumentManager
            onInspectDocument={(doc) => setInspectedDocument(doc)}
            onOpenAuth={() => setAuthModalOpen(true)}
            isAuthenticated={!!currentUser}
          />
        )}

        {activeTab === "analytics" && (
          <AnalyticsView
            isAuthenticated={!!currentUser}
            onOpenAuth={() => setAuthModalOpen(true)}
          />
        )}

        {activeTab === "settings" && <SettingsView />}
      </main>

      {/* Modals & Drawers */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        onSuccess={(user) => {
          setCurrentUser(user);
        }}
      />

      <CitationDrawer
        citations={inspectedCitations}
        activeCitation={activeCitation}
        onClose={handleCloseCitation}
        onSelectCitation={(c) => setActiveCitation(c)}
      />

      <ChunkViewerModal
        document={inspectedDocument}
        onClose={() => setInspectedDocument(null)}
      />
    </div>
  );
}
