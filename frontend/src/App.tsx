import { useRef, useState } from "react";
import { BackgroundLayer } from "./components/BackgroundLayer";
import { ChatPage } from "./components/ChatPage";
import { CollectionsPage } from "./components/CollectionsPage";
import { HeroSection } from "./components/HeroSection";
import type { SearchBarHandle } from "./components/SearchBar";
import { SearchDashboard } from "./components/SearchDashboard";
import { Sidebar } from "./components/Sidebar";
import { TopToolbar } from "./components/TopToolbar";
import { useAtlasSearch } from "./hooks/useAtlasSearch";
import type { AppView } from "./types/atlas";

function App() {
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

  const isOverlayOpen = view !== "home";

  return (
    <div className="app-shell">
      <BackgroundLayer />
      <div className={`vision-frame ${isOverlayOpen ? "has-sheet" : ""}`}>
        <TopToolbar
          filters={filters}
          isUploading={isUploading}
          onAskAI={handleAskAI}
          onFiltersChange={setFilters}
          onUpload={handleUpload}
        />
        <Sidebar currentView={view} onNavigate={setView} />
        <HeroSection
          isLoading={isLoading}
          onPrompt={handleSearchSubmit}
          onSearch={handleSearchSubmit}
          prompts={promptSuggestions}
          ref={searchBarRef}
        />
        <SearchDashboard
          documents={documents}
          error={error}
          isLoading={isLoading}
          isOpen={view === "search"}
          onClose={goHome}
          search={search}
        />
        <CollectionsPage isOpen={view === "collections"} onClose={goHome} />
        <ChatPage isOpen={view === "chat"} onClose={goHome} />
      </div>
    </div>
  );
}

export default App;
