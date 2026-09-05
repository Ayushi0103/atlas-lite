import type { DocumentFile, SearchState } from "../types/atlas";
import { AnswerCard } from "./AnswerCard";
import { HomeIcon, SunIcon } from "./Icons";
import { RecentFiles } from "./RecentFiles";
import { RelatedConcepts } from "./RelatedConcepts";
import { RelatedSources } from "./RelatedSources";

type SearchDashboardProps = {
  documents: DocumentFile[];
  error: string | null;
  isLoading: boolean;
  isOpen: boolean;
  onClose: () => void;
  search: SearchState;
};

const INTENT_LABELS: Record<string, string> = {
  knowledge_lookup: "Searched your knowledge base",
  relationship_lookup: "Explored your knowledge graph",
  document_lookup: "Looked through your documents",
  document_summary: "Summarized your documents",
  conversation_lookup: "Checked your conversation history",
  collection_lookup: "Looked through your collections",
  general_question: "Searched your knowledge base",
};

export function SearchDashboard({ documents, error, isLoading, isOpen, onClose, search }: SearchDashboardProps) {
  const intentLabel = search.intent ? INTENT_LABELS[search.intent] : null;

  return (
    <section className={`result-sheet ${isOpen ? "is-open" : ""}`} aria-hidden={!isOpen}>
      <div className="sheet-frame">
        <header className="sheet-header">
          <button className="sheet-home" aria-label="Back home" onClick={onClose} type="button">
            <HomeIcon aria-hidden="true" />
          </button>
          <div className="query-pill" title={search.query}>{search.query || "Ask KORA"}</div>
          <div className="greeting">Good morning <SunIcon aria-hidden="true" /></div>
        </header>
        <div className="sheet-content">
          {!isLoading && !error && intentLabel && (
            <p className="intent-badge">{intentLabel}</p>
          )}
          <AnswerCard answer={search.answer} error={error} isLoading={isLoading} />
          <RelatedConcepts concepts={search.relatedConcepts} />
          <div className="dashboard-grid">
            <RecentFiles documents={documents} />
            <RelatedSources semanticResults={search.semanticResults} sources={search.sources} />
          </div>
        </div>
      </div>
    </section>
  );
}
