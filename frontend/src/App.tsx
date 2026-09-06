import { useRef, useState } from "react";
import { AuthPage } from "./components/AuthPage";
import { ChatPage } from "./components/ChatPage";
import { CollectionsPage } from "./components/CollectionsPage";
import { Dashboard } from "./components/Dashboard";
import { KnowledgeMapPage } from "./components/KnowledgeMapPage";
import { LibraryPage } from "./components/LibraryPage";
import type { SearchBarHandle } from "./components/SearchBar";
import { SearchDashboard } from "./components/SearchDashboard";
import { Sidebar } from "./components/Sidebar";
import { TopToolbar } from "./components/TopToolbar";
import { useAuth } from "./context/AuthContext";
import { useAtlasSearch } from "./hooks/useAtlasSearch";
import type { AppView } from "./types/atlas";

function AtlasApp() {
  const { user } = useAuth();
  const {
    documents,
    error,
    filters,
    handleUpload,
    isLoading,
    isUploading,
    promptSuggestions,
    search,
    setFilters,
    submitSearch,
  } = useAtlasSearch();

  const [view, setView] = useState<AppView>("home");
  const searchBarRef = useRef<SearchBarHandle>(null);
  const uploadInputRef = useRef<HTMLInputElement>(null);

  function goHome() {
    setView("home");
  }

  function handleAskAI() {
    setView("home");
    requestAnimationFrame(() => searchBarRef.current?.focus());
  }

  function handleSearchSubmit(query: string) {
    setView("search");
    void submitSearch(query);
  }

  function openUploadPicker() {
    uploadInputRef.current?.click();
  }

  return (
    <div className="app-shell">
      <div className="workspace-frame">
        <input
          className="visually-hidden"
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) handleUpload(file);
            event.currentTarget.value = "";
          }}
          ref={uploadInputRef}
          type="file"
        />
        <TopToolbar
          filters={filters}
          isUploading={isUploading}
          onAskAI={handleAskAI}
          onFiltersChange={setFilters}
          onSearch={handleSearchSubmit}
          onUpload={handleUpload}
        />
        <Sidebar currentView={view} onNavigate={setView} />
        <Dashboard
          documents={documents}
          isLoading={isLoading}
          isUploading={isUploading}
          onNavigateChat={() => setView("chat")}
          onNavigateCollections={() => setView("collections")}
          onNavigateKnowledgeMap={() => setView("knowledge-map")}
          onNavigateLibrary={() => setView("library")}
          onSearch={handleSearchSubmit}
          onUpload={openUploadPicker}
          prompts={promptSuggestions}
          searchRef={searchBarRef}
          user={user}
        />
        <SearchDashboard
          documents={documents}
          error={error}
          isLoading={isLoading}
          isOpen={view === "search"}
          onClose={goHome}
          onSearch={handleSearchSubmit}
          search={search}
        />
        <LibraryPage
          documents={documents}
          isOpen={view === "library"}
          isUploading={isUploading}
          onClose={goHome}
          onUpload={openUploadPicker}
        />
        <KnowledgeMapPage isOpen={view === "knowledge-map"} onClose={goHome} />
        <CollectionsPage isOpen={view === "collections"} onClose={goHome} />
        <ChatPage isOpen={view === "chat"} onClose={goHome} />
      </div>
    </div>
  );
}

function App() {
  const { user, isInitializing } = useAuth();

  if (isInitializing) {
    return (
      <div className="app-shell auth-shell">
      </div>
    );
  }

  if (!user) {
    return <AuthPage />;
  }

  return <AtlasApp />;
}

export default App;
