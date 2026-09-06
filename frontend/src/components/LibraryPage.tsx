import type { DocumentFile } from "../types/atlas";
import { RecentlyAddedSection } from "./DocumentCards";
import { HomeIcon, UploadIcon } from "./Icons";

type LibraryPageProps = {
  documents: DocumentFile[];
  isOpen: boolean;
  isUploading: boolean;
  onClose: () => void;
  onUpload: () => void;
};

export function LibraryPage({ documents, isOpen, isUploading, onClose, onUpload }: LibraryPageProps) {
  return (
    <section className={`page-surface ${isOpen ? "is-open" : ""}`} aria-hidden={!isOpen}>
      <header className="page-header">
        <button className="icon-button" aria-label="Back home" onClick={onClose} type="button">
          <HomeIcon aria-hidden="true" />
        </button>
        <div>
          <h1>My Library</h1>
          <p>{documents.length} indexed items</p>
        </div>
        <button className="primary-button" onClick={onUpload} disabled={isUploading} type="button">
          <UploadIcon aria-hidden="true" />
          <span>{isUploading ? "Uploading" : "Upload File"}</span>
        </button>
      </header>
      <RecentlyAddedSection documents={documents} />
    </section>
  );
}
