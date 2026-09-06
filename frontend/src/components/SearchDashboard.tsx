import type { DocumentFile, SearchState } from "../types/atlas";
import { AnswerCard } from "./AnswerCard";
import { ArrowRightIcon, HomeIcon, SparkleIcon } from "./Icons";
import { RelatedConcepts } from "./RelatedConcepts";
import { RelatedSources } from "./RelatedSources";
import { SearchBar } from "./SearchBar";

type SearchDashboardProps = {
  documents: DocumentFile[];
  error: string | null;
  isLoading: boolean;
  isOpen: boolean;
  onClose: () => void;
  onSearch: (query: string) => void;
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

export function SearchDashboard({ documents, error, isLoading, isOpen, onClose, onSearch, search }: SearchDashboardProps) {
  const intentLabel = search.intent ? INTENT_LABELS[search.intent] : null;

  return (
    <section className={`search-workspace page-surface ${isOpen ? "is-open" : ""}`} aria-hidden={!isOpen}>
      <header className="page-header">
          <button className="icon-button" aria-label="Back home" onClick={onClose} type="button">
            <HomeIcon aria-hidden="true" />
          </button>
          <div>
            <h1>Search results</h1>
            <p title={search.query}>{search.query || "Ask KORA"}</p>
          </div>
          {intentLabel && !isLoading && !error && <span className="intent-badge">{intentLabel}</span>}
      </header>

      <div className="result-layout">
        <main className="answer-column">
          <section className="result-hero">
            <div>
              <SparkleIcon aria-hidden="true" />
              <h2>Here’s what I found</h2>
              <p>KORA searched across {documents.length} indexed items and synthesized the most relevant answer.</p>
            </div>
          </section>
          <AnswerCard answer={search.answer} error={error} isLoading={isLoading} />
          <div className="follow-up-box">
            <SearchBar
              disabled={isLoading}
              onSubmit={onSearch}
              placeholder="Ask a follow-up..."
              variant="compact"
            />
          </div>
        </main>

        <aside className="result-aside">
          <RelatedSources semanticResults={search.semanticResults} sources={search.sources} />
          <RelatedConcepts concepts={search.relatedConcepts} />
          <section className="dashboard-panel follow-up-panel">
            <h2>You may also ask</h2>
            {search.semanticResults.slice(0, 3).map((result) => {
              const title = result.filename || result.title || "this source";
              const prompt = `What are the key ideas from ${title}?`;
              return (
                <button key={`${result.type}-${result.id}`} onClick={() => onSearch(prompt)} type="button">
                  <span>{prompt}</span>
                  <ArrowRightIcon aria-hidden="true" />
                </button>
              );
            })}
            {search.semanticResults.length === 0 && <p className="empty-copy">Follow-up suggestions appear with source results.</p>}
          </section>
        </aside>
      </div>
    </section>
  );
}
