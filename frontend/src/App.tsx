import { BackgroundLayer } from "./components/BackgroundLayer";
import { HeroSection } from "./components/HeroSection";
import { SearchDashboard } from "./components/SearchDashboard";
import { Sidebar } from "./components/Sidebar";
import { TopToolbar } from "./components/TopToolbar";
import { useAtlasSearch } from "./hooks/useAtlasSearch";

function App() {
  const {
    documents,
    error,
    handleUpload,
    isLoading,
    isSheetOpen,
    isUploading,
    promptSuggestions,
    search,
    setIsSheetOpen,
    submitSearch,
  } = useAtlasSearch();

  return (
    <div className="app-shell">
      <BackgroundLayer />
      <div className={`vision-frame ${isSheetOpen ? "has-sheet" : ""}`}>
        <TopToolbar isUploading={isUploading} onUpload={handleUpload} />
        <Sidebar isSheetOpen={isSheetOpen} onHome={() => setIsSheetOpen(false)} />
        <HeroSection
          isLoading={isLoading}
          onPrompt={submitSearch}
          onSearch={submitSearch}
          prompts={promptSuggestions}
        />
        <SearchDashboard
          documents={documents}
          error={error}
          isLoading={isLoading}
          isOpen={isSheetOpen}
          onClose={() => setIsSheetOpen(false)}
          search={search}
        />
      </div>
    </div>
  );
}

export default App;
