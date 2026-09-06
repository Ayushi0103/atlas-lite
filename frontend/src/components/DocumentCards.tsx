import type { DocumentFile } from "../types/atlas";
import { FileBadge } from "./FileBadge";
import { MoreIcon, StarIcon } from "./Icons";

type DocumentCardsProps = {
  documents: DocumentFile[];
};

function formatRelativeDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Recently";

  const elapsed = Date.now() - date.getTime();
  const day = 24 * 60 * 60 * 1000;
  if (elapsed < day) return "Today";
  if (elapsed < day * 2) return "Yesterday";
  if (elapsed < day * 7) return `${Math.floor(elapsed / day)} days ago`;

  return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(date);
}

function friendlyType(type: string): string {
  const normalized = type.toLowerCase();
  if (["mp3", "wav", "m4a", "flac", "ogg"].includes(normalized)) return "Audio";
  if (["png", "jpg", "jpeg", "webp"].includes(normalized)) return "Image";
  if (normalized === "docx") return "Document";
  if (normalized === "youtube") return "Transcript";
  return normalized.toUpperCase();
}

export function ContinueWorkingSection({ documents }: DocumentCardsProps) {
  const items = documents.slice(0, 4);

  return (
    <section className="content-section">
      <div className="section-heading">
        <h2>Continue where you left off</h2>
        <button className="text-link" type="button">View all</button>
      </div>
      <div className="continue-grid">
        {items.map((document, index) => (
          <article className={`continue-card tone-${index % 4}`} key={document.id}>
            <div className="card-topline">
              <span className="file-type-pill">{friendlyType(document.file_type)}</span>
              <button aria-label={`More options for ${document.filename}`} type="button">
                <MoreIcon aria-hidden="true" />
              </button>
            </div>
            <FileBadge type={document.file_type} />
            <h3>{document.filename}</h3>
            <p>{document.short_summary || friendlyType(document.file_type)}</p>
            <time dateTime={document.updated_at}>{formatRelativeDate(document.updated_at)}</time>
          </article>
        ))}
        {items.length === 0 && (
          <div className="empty-panel">
            <h3>No files yet</h3>
            <p>Upload a document to start building your KORA workspace.</p>
          </div>
        )}
      </div>
    </section>
  );
}

export function RecentlyAddedSection({ documents }: DocumentCardsProps) {
  const items = documents.slice(0, 6);

  return (
    <section className="content-section recent-table-section">
      <div className="section-heading">
        <h2>Recently added</h2>
        <div className="segmented-tabs" aria-label="File filters">
          <button className="is-active" type="button">All</button>
          <button type="button">Files</button>
          <button type="button">Audio</button>
          <button type="button">Images</button>
        </div>
      </div>
      <div className="recent-table" role="table" aria-label="Recently added files">
        <div className="recent-row recent-head" role="row">
          <span>Name</span>
          <span>Type</span>
          <span>Added</span>
          <span>Source</span>
          <span aria-label="Actions" />
        </div>
        {items.map((document) => (
          <article className="recent-row" role="row" key={document.id}>
            <span className="recent-name">
              <FileBadge type={document.file_type} />
              <strong>{document.filename}</strong>
            </span>
            <span><span className="soft-badge">{friendlyType(document.file_type)}</span></span>
            <time dateTime={document.created_at}>{formatRelativeDate(document.created_at)}</time>
            <span className="source-dot-wrap"><i aria-hidden="true" /> My Library</span>
            <button aria-label={`Save ${document.filename}`} type="button">
              <StarIcon aria-hidden="true" />
            </button>
          </article>
        ))}
        {items.length === 0 && <p className="empty-copy">New uploads will appear here after indexing.</p>}
      </div>
    </section>
  );
}
