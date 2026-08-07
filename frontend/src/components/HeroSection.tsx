import { PromptChip } from "./PromptChip";
import { SearchBar } from "./SearchBar";

type HeroSectionProps = {
  isLoading: boolean;
  prompts: string[];
  onPrompt: (prompt: string) => void;
  onSearch: (query: string) => void;
};

export function HeroSection({ isLoading, prompts, onPrompt, onSearch }: HeroSectionProps) {
  return (
    <main className="hero-section" aria-label="Atlas Lite home">
      <h1>Atlas lite</h1>
      <p>Your second brain.</p>
      <p>Ask anything — find everything.</p>
      <SearchBar disabled={isLoading} onSubmit={onSearch} />
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
}
