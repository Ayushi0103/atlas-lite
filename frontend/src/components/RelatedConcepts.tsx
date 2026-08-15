import type { RelatedConcept } from "../types/atlas";
import { SparkleIcon } from "./Icons";

type RelatedConceptsProps = {
  concepts: RelatedConcept[];
};

export function RelatedConcepts({ concepts }: RelatedConceptsProps) {
  if (concepts.length === 0) return null;

  return (
    <section className="dashboard-panel related-concepts">
      <h2>Related concepts.</h2>
      <div className="concept-chip-row">
        {concepts.map((concept, index) => (
          <span className="concept-chip" key={`${concept.target}-${index}`}>
            <SparkleIcon aria-hidden="true" />
            <span className="concept-relationship">{concept.relationship}</span>
            <span className="concept-target">{concept.target}</span>
          </span>
        ))}
      </div>
    </section>
  );
}