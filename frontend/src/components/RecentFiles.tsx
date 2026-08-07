import type { DocumentFile } from "../types/atlas";
import { ArrowRightIcon } from "./Icons";
import { FileBadge } from "./FileBadge";

function formatDate(value?: string) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(date);
}

export function RecentFiles({ documents }: { documents: DocumentFile[] }) {
  return (
    <section className="dashboard-panel recent-files">
      <h2>Recent files.</h2>
      <div className="file-list">
        {documents.slice(0, 4).map((document) => (
          <article className="file-row" key={document.id}>
            <FileBadge type={document.file_type} />
            <div>
              <h3>{document.filename}</h3>
              <p>{document.file_type.toUpperCase()}</p>
            </div>
            <time dateTime={document.created_at}>{formatDate(document.created_at)}</time>
          </article>
        ))}
        {documents.length === 0 && <p className="empty-copy">Uploaded files will appear here after indexing.</p>}
      </div>
      <button className="panel-link" type="button">View all files <ArrowRightIcon aria-hidden="true" /></button>
    </section>
  );
}
