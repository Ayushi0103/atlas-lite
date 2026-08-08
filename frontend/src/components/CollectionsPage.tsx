import { FormEvent, useEffect, useState } from "react";
import { GlassCard, Loader } from "./Glass";
import { ArrowRightIcon, GridIcon, HomeIcon, SunIcon } from "./Icons";
import {
  createCollection,
  deleteCollection,
  getCollectionNotes,
  getCollections,
} from "../services/atlasApi";
import type { Collection, CollectionNoteSummary } from "../types/atlas";

type CollectionsPageProps = {
  isOpen: boolean;
  onClose: () => void;
};

export function CollectionsPage({ isOpen, onClose }: CollectionsPageProps) {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [isCreating, setIsCreating] = useState(false);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [notesById, setNotesById] = useState<Record<number, CollectionNoteSummary[]>>({});
  const [notesLoadingId, setNotesLoadingId] = useState<number | null>(null);
  const [hasLoadedOnce, setHasLoadedOnce] = useState(false);

  async function refresh() {
    setIsLoading(true);
    setError(null);
    try {
      setCollections(await getCollections());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load collections.");
    } finally {
      setIsLoading(false);
      setHasLoadedOnce(true);
    }
  }

  useEffect(() => {
    if (isOpen && !hasLoadedOnce) void refresh();
  }, [isOpen, hasLoadedOnce]);

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    const cleanedName = name.trim();
    if (!cleanedName) return;

    setIsCreating(true);
    setError(null);
    try {
      await createCollection(cleanedName, description.trim() || undefined);
      setName("");
      setDescription("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create collection.");
    } finally {
      setIsCreating(false);
    }
  }

  async function handleDelete(id: number) {
    setError(null);
    try {
      await deleteCollection(id);
      if (expandedId === id) setExpandedId(null);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete collection.");
    }
  }

  async function toggleExpand(id: number) {
    if (expandedId === id) {
      setExpandedId(null);
      return;
    }

    setExpandedId(id);
    if (!notesById[id]) {
      setNotesLoadingId(id);
      try {
        const notes = await getCollectionNotes(id);
        setNotesById((prev) => ({ ...prev, [id]: notes }));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not load notes for this collection.");
      } finally {
        setNotesLoadingId(null);
      }
    }
  }

  return (
    <section className={`result-sheet ${isOpen ? "is-open" : ""}`} aria-hidden={!isOpen}>
      <div className="sheet-frame">
        <header className="sheet-header">
          <button className="sheet-home" aria-label="Back home" onClick={onClose} type="button">
            <HomeIcon aria-hidden="true" />
          </button>
          <div className="query-pill">Collections</div>
          <div className="greeting">Good morning <SunIcon aria-hidden="true" /></div>
        </header>
        <div className="sheet-content">
          <GlassCard className="collections-page">
            <form className="new-collection-form" onSubmit={handleCreate}>
              <input
                aria-label="Collection name"
                onChange={(event) => setName(event.target.value)}
                placeholder="New collection name"
                value={name}
              />
              <input
                aria-label="Collection description"
                onChange={(event) => setDescription(event.target.value)}
                placeholder="Description (optional)"
                value={description}
              />
              <button disabled={isCreating || !name.trim()} type="submit">
                {isCreating ? "Creating..." : "Create"}
              </button>
            </form>

            {isLoading && <Loader label="Loading collections" />}
            {!isLoading && error && <p className="error-copy">{error}</p>}

            {!isLoading && (
              <div className="collection-grid">
                {collections.map((collection) => (
                  <article className="collection-card" key={collection.id}>
                    <div className="collection-card-header">
                      <span className="collection-icon" aria-hidden="true"><GridIcon /></span>
                      <div>
                        <h3>{collection.name}</h3>
                        {collection.description && <p>{collection.description}</p>}
                      </div>
                    </div>
                    <div className="collection-card-actions">
                      <button onClick={() => toggleExpand(collection.id)} type="button">
                        {expandedId === collection.id ? "Hide notes" : "View notes"}
                        <ArrowRightIcon aria-hidden="true" />
                      </button>
                      <button className="danger-link" onClick={() => handleDelete(collection.id)} type="button">
                        Delete
                      </button>
                    </div>
                    {expandedId === collection.id && (
                      <div className="collection-notes">
                        {notesLoadingId === collection.id && <Loader label="Loading notes" />}
                        {notesLoadingId !== collection.id && (notesById[collection.id]?.length ?? 0) === 0 && (
                          <p className="empty-copy">No notes in this collection yet.</p>
                        )}
                        {notesLoadingId !== collection.id &&
                          notesById[collection.id]?.map((note) => (
                            <div className="collection-note-row" key={note.id}>
                              <strong>{note.title}</strong>
                              <p>{note.content}</p>
                            </div>
                          ))}
                      </div>
                    )}
                  </article>
                ))}
                {collections.length === 0 && !error && (
                  <p className="empty-copy">Create your first collection to start grouping notes.</p>
                )}
              </div>
            )}
          </GlassCard>
        </div>
      </div>
    </section>
  );
}