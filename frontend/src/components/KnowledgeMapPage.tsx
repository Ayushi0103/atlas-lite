import { FormEvent, useState } from "react";
import { getKnowledgeGraph } from "../services/atlasApi";
import type { RelatedConcept } from "../types/atlas";
import { ArrowRightIcon, HomeIcon, NetworkIcon } from "./Icons";

type KnowledgeMapPageProps = {
  isOpen: boolean;
  onClose: () => void;
};

export function KnowledgeMapPage({ isOpen, onClose }: KnowledgeMapPageProps) {
  const [concept, setConcept] = useState("");
  const [activeConcept, setActiveConcept] = useState("");
  const [related, setRelated] = useState<RelatedConcept[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const cleaned = concept.trim();
    if (!cleaned) return;

    setIsLoading(true);
    setError(null);
    try {
      const graph = await getKnowledgeGraph(cleaned);
      setActiveConcept(graph.concept);
      setRelated(graph.related);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load this concept.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <section className={`page-surface ${isOpen ? "is-open" : ""}`} aria-hidden={!isOpen}>
      <header className="page-header">
        <button className="icon-button" aria-label="Back home" onClick={onClose} type="button">
          <HomeIcon aria-hidden="true" />
        </button>
        <div>
          <h1>Knowledge Map</h1>
          <p>Explore connections extracted from your indexed sources.</p>
        </div>
      </header>

      <section className="map-workspace">
        <form className="map-search" onSubmit={handleSubmit}>
          <NetworkIcon aria-hidden="true" />
          <input
            aria-label="Search a concept"
            onChange={(event) => setConcept(event.target.value)}
            placeholder="Search a concept from your knowledge base"
            value={concept}
          />
          <button disabled={isLoading || !concept.trim()} type="submit">
            <ArrowRightIcon aria-hidden="true" />
          </button>
        </form>

        {error && <p className="error-copy">{error}</p>}

        <div className="graph-panel">
          <div className="graph-center">
            <span><NetworkIcon aria-hidden="true" /></span>
            <h2>{activeConcept || "Choose a concept"}</h2>
            <p>{isLoading ? "Mapping related ideas..." : related.length ? `${related.length} related ideas found` : "Related ideas will appear here."}</p>
          </div>
          <div className="graph-related">
            {related.map((item, index) => (
              <article key={`${item.target}-${index}`}>
                <strong>{item.target}</strong>
                <span>{item.relationship}</span>
                <small>{item.type}</small>
              </article>
            ))}
          </div>
        </div>
      </section>
    </section>
  );
}
