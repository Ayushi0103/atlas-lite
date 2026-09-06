import { useEffect, useState } from "react";
import type { Ref } from "react";
import { getCollections } from "../services/atlasApi";
import type { AuthUser, Collection, DocumentFile } from "../types/atlas";
import { ContinueWorkingSection, RecentlyAddedSection } from "./DocumentCards";
import {
  ArrowRightIcon,
  ChatIcon,
  FolderIcon,
  GridIcon,
  LightningIcon,
  NetworkIcon,
  PlusIcon,
  SparkleIcon,
  UploadIcon,
  UsersIcon,
} from "./Icons";
import { SearchBar, type SearchBarHandle } from "./SearchBar";

type DashboardProps = {
  documents: DocumentFile[];
  isLoading: boolean;
  isUploading: boolean;
  onNavigateCollections: () => void;
  onNavigateKnowledgeMap: () => void;
  onNavigateLibrary: () => void;
  onNavigateChat: () => void;
  onSearch: (query: string) => void;
  onUpload: () => void;
  prompts: string[];
  searchRef: Ref<SearchBarHandle>;
  user: AuthUser | null;
};

function firstName(user: AuthUser | null): string {
  return user?.name.trim().split(/\s+/)[0] || "there";
}

export function Dashboard({
  documents,
  isLoading,
  isUploading,
  onNavigateChat,
  onNavigateCollections,
  onNavigateKnowledgeMap,
  onNavigateLibrary,
  onSearch,
  onUpload,
  prompts,
  searchRef,
  user,
}: DashboardProps) {
  const [collections, setCollections] = useState<Collection[]>([]);

  useEffect(() => {
    getCollections()
      .then(setCollections)
      .catch(() => setCollections([]));
  }, []);

  const totalDocuments = documents.length;
  const totalCollections = collections.length;
  const totalConcepts = documents.reduce((count, document) => {
    try {
      const parsed = document.key_concepts ? JSON.parse(document.key_concepts) : [];
      return count + (Array.isArray(parsed) ? parsed.length : 0);
    } catch {
      return count;
    }
  }, 0);

  return (
    <main className="dashboard" aria-label="KORA dashboard">
      <section className="dashboard-main">
        <div className="welcome-band">
          <div>
            <h1>Good day, {firstName(user)}.</h1>
            <p>Find, understand, and connect the knowledge in your workspace.</p>
          </div>
          <div className="knowledge-orbit" aria-hidden="true">
            <span />
            <span />
            <span />
          </div>
        </div>

        <ContinueWorkingSection documents={documents} />
        <RecentlyAddedSection documents={documents} />

        <section className="content-section">
          <div className="section-heading">
            <h2>Your spaces</h2>
            <button className="text-link" onClick={onNavigateCollections} type="button">View all</button>
          </div>
          <div className="space-grid">
            {collections.slice(0, 3).map((collection, index) => (
              <article className={`space-card space-tone-${index % 3}`} key={collection.id}>
                <span><UsersIcon aria-hidden="true" /></span>
                <div>
                  <h3>{collection.name}</h3>
                  <p>{collection.description || "Personal collection"}</p>
                </div>
              </article>
            ))}
            <button className="create-space-card" onClick={onNavigateCollections} type="button">
              <PlusIcon aria-hidden="true" />
              <span>Create New Space</span>
            </button>
          </div>
        </section>
      </section>

      <aside className="dashboard-aside" aria-label="KORA tools">
        <section className="ask-panel">
          <div className="panel-title">
            <SparkleIcon aria-hidden="true" />
            <h2>Ask KORA</h2>
          </div>
          <p>Ask anything about your knowledge.</p>
          <SearchBar disabled={isLoading} onSubmit={onSearch} ref={searchRef} variant="compact" />
          <div className="try-list">
            {prompts.slice(0, 4).map((prompt) => (
              <button key={prompt} onClick={() => onSearch(prompt)} type="button">
                <GridIcon aria-hidden="true" />
                <span>{prompt}</span>
              </button>
            ))}
            {prompts.length === 0 && <p className="empty-copy">Suggestions appear after your files are indexed.</p>}
          </div>
        </section>

        <section className="knowledge-card">
          <div>
            <div className="panel-title">
              <NetworkIcon aria-hidden="true" />
              <h2>Knowledge Map</h2>
            </div>
            <p>{totalConcepts > 0 ? `${totalConcepts} extracted concepts across your files.` : "Explore relationships across your indexed knowledge."}</p>
            <button onClick={onNavigateKnowledgeMap} type="button">Open Map <ArrowRightIcon aria-hidden="true" /></button>
          </div>
          <div className="mini-map" aria-hidden="true">
            <span />
            <span />
            <span />
            <span />
          </div>
        </section>

        <section className="quick-panel">
          <div className="panel-title">
            <LightningIcon aria-hidden="true" />
            <h2>Quick Actions</h2>
          </div>
          <div className="quick-grid">
            <button onClick={onUpload} disabled={isUploading} type="button"><UploadIcon /><span>{isUploading ? "Uploading" : "Upload File"}</span></button>
            <button onClick={onNavigateCollections} type="button"><FolderIcon /><span>New Space</span></button>
            <button onClick={onNavigateChat} type="button"><ChatIcon /><span>AI Chat</span></button>
            <button onClick={onNavigateLibrary} type="button"><GridIcon /><span>{totalDocuments} Files</span></button>
          </div>
        </section>
      </aside>
    </main>
  );
}
