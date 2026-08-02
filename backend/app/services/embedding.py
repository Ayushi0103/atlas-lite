from functools import lru_cache
from typing import Any, Literal, TypedDict

from app.chromadb_client import get_chroma_collection


EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
CHUNK_SIZE_WORDS = 500
CHUNK_OVERLAP_WORDS = 50

SourceType = Literal["document", "note"]


class SemanticSearchResult(TypedDict):
    type: str
    id: int
    score: float
    text: str
    filename: str | None
    title: str | None


@lru_cache(maxsize=1)
def get_embedding_model() -> Any:
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def get_embedding(text: str) -> list[float]:
    cleaned_text = text.strip()
    if not cleaned_text:
        return []

    model = get_embedding_model()
    embedding = model.encode(cleaned_text, normalize_embeddings=True)
    return embedding.tolist()


def chunk_text(text: str) -> list[str]:
    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    step = CHUNK_SIZE_WORDS - CHUNK_OVERLAP_WORDS
    for start in range(0, len(words), step):
        chunk_words = words[start : start + CHUNK_SIZE_WORDS]
        if not chunk_words:
            break

        chunks.append(" ".join(chunk_words))
        if start + CHUNK_SIZE_WORDS >= len(words):
            break

    return chunks


def _source_key(source_type: SourceType, source_id: int) -> str:
    return f"{source_type}:{source_id}"


def _vector_id(source_type: SourceType, source_id: int, chunk_index: int) -> str:
    return f"{_source_key(source_type, source_id)}:{chunk_index}"


def _delete_existing_vectors(source_type: SourceType, source_id: int) -> None:
    collection = get_chroma_collection()
    existing = collection.get(where={"source_key": _source_key(source_type, source_id)})
    ids = existing.get("ids", [])
    if ids:
        collection.delete(ids=ids)


def _upsert_source_embeddings(
    *,
    source_type: SourceType,
    source_id: int,
    text: str,
    title: str | None = None,
    filename: str | None = None,
) -> None:
    _delete_existing_vectors(source_type, source_id)

    chunks = chunk_text(text)
    if not chunks:
        return

    ids: list[str] = []
    embeddings: list[list[float]] = []
    metadatas: list[dict[str, Any]] = []

    for chunk_index, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        if not embedding:
            continue

        ids.append(_vector_id(source_type, source_id, chunk_index))
        embeddings.append(embedding)
        metadatas.append(
            {
                "source_key": _source_key(source_type, source_id),
                "source_type": source_type,
                "source_id": source_id,
                "document_id": source_id if source_type == "document" else 0,
                "note_id": source_id if source_type == "note" else 0,
                "chunk_index": chunk_index,
                "title": title or "",
                "filename": filename or "",
            }
        )

    if ids:
        collection = get_chroma_collection()
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=chunks[: len(ids)],
            metadatas=metadatas,
        )


def add_document_embedding(document_id: int, filename: str, text: str) -> None:
    _upsert_source_embeddings(
        source_type="document",
        source_id=document_id,
        filename=filename,
        text=text,
    )


def add_note_embedding(note_id: int, title: str, text: str) -> None:
    _upsert_source_embeddings(
        source_type="note",
        source_id=note_id,
        title=title,
        text=f"{title}\n{text}",
    )


def update_embedding(
    source_type: SourceType,
    source_id: int,
    text: str,
    title: str | None = None,
    filename: str | None = None,
) -> None:
    _upsert_source_embeddings(
        source_type=source_type,
        source_id=source_id,
        text=text,
        title=title,
        filename=filename,
    )


def delete_embedding(source_type: SourceType, source_id: int) -> None:
    _delete_existing_vectors(source_type, source_id)


def semantic_search(query: str, top_k: int = 5) -> list[SemanticSearchResult]:
    cleaned_query = query.strip()
    if not cleaned_query or top_k <= 0:
        return []

    try:
        query_embedding = get_embedding(cleaned_query)
        if not query_embedding:
            return []

        collection = get_chroma_collection()
        matches = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
    except Exception:
        return []

    documents = matches.get("documents", [[]])[0]
    metadatas = matches.get("metadatas", [[]])[0]
    distances = matches.get("distances", [[]])[0]

    results: list[SemanticSearchResult] = []
    for document_text, metadata, distance in zip(documents, metadatas, distances):
        source_type = str(metadata.get("source_type", ""))
        source_id = int(metadata.get("source_id", 0))
        score = max(0.0, min(1.0, 1.0 - float(distance)))

        result: SemanticSearchResult = {
            "type": source_type,
            "id": source_id,
            "score": score,
            "text": document_text,
            "filename": None,
            "title": None,
        }

        if source_type == "document":
            result["filename"] = str(metadata.get("filename", ""))
        elif source_type == "note":
            result["title"] = str(metadata.get("title", ""))

        results.append(result)

    return results
