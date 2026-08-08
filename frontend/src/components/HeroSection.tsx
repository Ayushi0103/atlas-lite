import { forwardRef } from "react";
import { PromptChip } from "./PromptChip";
import { SearchBar, type SearchBarHandle } from "./SearchBar";

type HeroSectionProps = {
  isLoading: boolean;
  prompts: string[];
  onPrompt: (prompt: string) => void;
  onSearch: (query: string) => void;
};

export const HeroSection = forwardRef<SearchBarHandle, HeroSectionProps>(function HeroSection(
  { isLoading, prompts, onPrompt, onSearch },
  ref,
) {
  return (
    <main className="hero-section" aria-label="Atlas Lite home">
      <h1>Atlas lite</h1>
      <p>Your second brain.</p>
      <p>Ask anything — find everything.</p>
      <SearchBar disabled={isLoading} onSubmit={onSearch} ref={ref} />
      <div className="prompt-row" aria-label="Suggested prompts">
        {prompts.length > 0 ? (
          <>
            <span className="try-label">Try asking</span>
            {prompts.map((prompt) => <PromptChip key={prompt} label={prompt} onSelect={onPrompt} />)}
          </>
        ) : (
          <span className="try-label">Suggestions appear after your files are indexed</span>
        )}
      </div>
    </main>
  );
});
