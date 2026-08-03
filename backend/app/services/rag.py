import logging
from typing import Literal

from pydantic import BaseModel

from app.services.embedding import SemanticSearchResult, semantic_search
from app.services.groq_client import (
    GroqConfigurationError,
    GroqServiceError,
    generate_answer,
)


logger = logging.getLogger(__name__)

TOP_K = 5
SourceType = Literal["document", "note"]


class RAGSource(BaseModel):
    type: SourceType
    id: int
    title: str


class RAGResponse(BaseModel):
    answer: str
    sources: list[RAGSource]


class NoRelevantContextError(RuntimeError):
    pass


class LLMUnavailableError(RuntimeError):
    pass


def _source_title(result: SemanticSearchResult) -> str:
    if result["type"] == "document":
        return result.get("filename") or f"Document {result['id']}"

    return result.get("title") or f"Note {result['id']}"


def _build_context(results: list[SemanticSearchResult]) -> str:
    context_sections: list[str] = []
    for index, result in enumerate(results, start=1):
        title = _source_title(result)
        context_sections.append(
            "\n".join(
                [
                    f"[Source {index}]",
                    f"Type: {result['type']}",
                    f"ID: {result['id']}",
                    f"Title: {title}",
                    "Content:",
                    result["text"],
                ]
            )
        )

    return "\n\n".join(context_sections)


def _extract_sources(results: list[SemanticSearchResult]) -> list[RAGSource]:
    sources: list[RAGSource] = []
    seen: set[tuple[str, int]] = set()

    for result in results:
        source_type = result["type"]
        if source_type not in {"document", "note"}:
            continue

        key = (source_type, result["id"])
        if key in seen:
            continue

        seen.add(key)
        sources.append(
            RAGSource(
                type=source_type,
                id=result["id"],
                title=_source_title(result),
            )
        )

    return sources


def answer_question(question: str) -> RAGResponse:
    cleaned_question = question.strip()
    logger.info("Incoming AI question: %s", cleaned_question)

    results = semantic_search(cleaned_question, top_k=TOP_K)
    logger.info("Retrieved semantic match count: %s", len(results))

    if not results:
        raise NoRelevantContextError("No relevant context found")

    context = _build_context(results)
    sources = _extract_sources(results)
    logger.info("Retrieved source count: %s", len(sources))

    try:
        answer = generate_answer(cleaned_question, context)
    except (GroqConfigurationError, GroqServiceError) as exc:
        raise LLMUnavailableError("LLM service unavailable") from exc

    return RAGResponse(answer=answer, sources=sources)
