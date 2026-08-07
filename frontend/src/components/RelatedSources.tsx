import type { RagSource, SemanticResult } from "../types/atlas";
import { ArrowRightIcon, ArrowUpRightIcon } from "./Icons";

type RelatedSourcesProps = {
  semanticResults: SemanticResult[];
  sources: RagSource[];
};

export function RelatedSources({ semanticResults, sources }: RelatedSourcesProps) {
  const combined = [
    ...sources.map((source, index) => ({
      id: `rag-${source.id ?? index}`,
      title: source.filename ?? source.title ?? "Source",
      text: source.text ?? "",
      href: source.source_url,
    })),
    ...semanticResults.map((result) => ({
      id: `semantic-${result.type}-${result.id}`,
      title: result.filename ?? result.title ?? result.type,
      text: result.text,
      href: undefined,
    })),
  ].slice(0, 3);

  return (
    <section className="dashboard-panel related-sources">
      <h2>Related sources.</h2>
      <div className="source-list">
        {combined.map((source) => (
          <article className="source-row" key={source.id}>
            <div className="source-thumb" aria-hidden="true" />
            <div>
              <h3>{source.title}</h3>
              <p>{source.text}</p>
            </div>
            {source.href ? (
              <a aria-label={`Open ${source.title}`} href={source.href} rel="noreferrer" target="_blank">
                <ArrowUpRightIcon aria-hidden="true" />
              </a>
            ) : (
              <span className="source-action"><ArrowUpRightIcon aria-hidden="true" /></span>
            )}
          </article>
        ))}
        {combined.length === 0 && <p className="empty-copy">Sources will appear when Atlas finds relevant context.</p>}
      </div>
      <button className="panel-link" type="button">View all sources <ArrowRightIcon aria-hidden="true" /></button>
    </section>
  );
}
