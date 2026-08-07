import type { DocumentFile, SearchState } from "../types/atlas";
import { AnswerCard } from "./AnswerCard";
import { HomeIcon, SunIcon } from "./Icons";
import { RecentFiles } from "./RecentFiles";
import { RelatedSources } from "./RelatedSources";

type SearchDashboardProps = {
  documents: DocumentFile[];
  error: string | null;
  isLoading: boolean;
  isOpen: boolean;
  onClose: () => void;
  search: SearchState;
};

export function SearchDashboard({ documents, error, isLoading, isOpen, onClose, search }: SearchDashboardProps) {
  return (
    <section className={`result-sheet ${isOpen ? "is-open" : ""}`} aria-hidden={!isOpen}>
      <div className="sheet-frame">
        <header className="sheet-header">
          <button className="sheet-home" aria-label="Back home" onClick={onClose} type="button">
            <HomeIcon aria-hidden="true" />
          </button>
          <div className="query-pill" title={search.query}>{search.query || "Ask Atlas Lite"}</div>
          <div className="greeting">Good morning <SunIcon aria-hidden="true" /></div>
        </header>
        <div className="sheet-content">
          <AnswerCard answer={search.answer} error={error} isLoading={isLoading} />
          <div className="dashboard-grid">
            <RecentFiles documents={documents} />
            <RelatedSources semanticResults={search.semanticResults} sources={search.sources} />
          </div>
        </div>
      </div>
    </section>
  );
}
