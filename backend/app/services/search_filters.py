from datetime import datetime, timedelta
from typing import Literal

from sqlmodel import Session

from app.models import Document, Note
from app.services.embedding import SemanticSearchResult

Scope = Literal["all", "documents", "notes"]
Since = Literal["all", "today", "week", "month"]

_SINCE_DELTAS: dict[str, timedelta] = {
    "today": timedelta(days=1),
    "week": timedelta(days=7),
    "month": timedelta(days=30),
}

_TEXT_FILE_TYPES = {"txt", "md"}
_IMAGE_FILE_TYPES = {"png", "jpg", "jpeg", "webp"}
_AUDIO_FILE_TYPES = {"mp3", "wav", "m4a", "flac", "ogg"}


def _passes_scope(result: SemanticSearchResult, scope: Scope) -> bool:
    if scope == "all":
        return True
    if scope == "documents":
        return result["type"] == "document"
    if scope == "notes":
        return result["type"] == "note"
    return True


def _passes_file_type(
    result: SemanticSearchResult,
    file_type: str | None,
    session: Session,
) -> bool:
    if not file_type or file_type == "all":
        return True

    # Notes don't have a file type, so any file-type filter excludes them.
    if result["type"] != "document":
        return False

    document = session.get(Document, result["id"])
    if document is None:
        return False

    normalized = document.file_type.lower()
    normalized_filter = file_type.lower()

    if normalized_filter == "txt":
        return normalized in _TEXT_FILE_TYPES
    if normalized_filter == "image":
        return normalized in _IMAGE_FILE_TYPES
    if normalized_filter == "audio":
        return normalized in _AUDIO_FILE_TYPES

    return normalized == normalized_filter


def _passes_since(result: SemanticSearchResult, since: Since, session: Session) -> bool:
    if since == "all":
        return True

    delta = _SINCE_DELTAS.get(since)
    if delta is None:
        return True

    cutoff = datetime.now() - delta

    entity: Document | Note | None
    if result["type"] == "document":
        entity = session.get(Document, result["id"])
    elif result["type"] == "note":
        entity = session.get(Note, result["id"])
    else:
        entity = None

    if entity is None:
        return False

    return entity.created_at >= cutoff


def apply_filters(
    results: list[SemanticSearchResult],
    session: Session,
    *,
    scope: Scope = "all",
    file_type: str | None = None,
    since: Since = "all",
) -> list[SemanticSearchResult]:
    """Filter semantic search results by scope, file type, and recency."""
    filtered: list[SemanticSearchResult] = []

    for result in results:
        if not _passes_scope(result, scope):
            continue
        if not _passes_file_type(result, file_type, session):
            continue
        if not _passes_since(result, since, session):
            continue
        filtered.append(result)

    return filtered