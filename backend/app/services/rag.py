import logging
from collections.abc import Generator
from typing import Literal, Mapping

from pydantic import BaseModel

from app.services.embedding import SemanticSearchResult, semantic_search
from app.services.groq_client import (
    GroqConfigurationError,
    GroqServiceError,
    generate_answer,
    generate_answer_stream,
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


class RAGContext(BaseModel):
    question: str
    context: str
    sources: list[RAGSource]
    retrieved_document_count: int


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


def prepare_rag_context(question: str) -> RAGContext:
    cleaned_question = question.strip()
    logger.info("Incoming AI question: %s", cleaned_question)

    results = semantic_search(cleaned_question, top_k=TOP_K)
    logger.info("Retrieved semantic match count: %s", len(results))

    if not results:
        raise NoRelevantContextError("No relevant context found")

    context = _build_context(results)
    sources = _extract_sources(results)
    logger.info("Retrieved source count: %s", len(sources))

    return RAGContext(
        question=cleaned_question,
        context=context,
        sources=sources,
        retrieved_document_count=len(results),
    )


def answer_question(
    question: str,
    conversation_history: list[Mapping[str, str]] | None = None,
) -> RAGResponse:
    rag_context = prepare_rag_context(question)

    try:
        answer = generate_answer(
            rag_context.question,
            rag_context.context,
            conversation_history,
        )
    except (GroqConfigurationError, GroqServiceError) as exc:
        raise LLMUnavailableError("LLM service unavailable") from exc

    return RAGResponse(answer=answer, sources=rag_context.sources)


def answer_question_stream(
    question: str,
    conversation_history: list[Mapping[str, str]] | None = None,
) -> Generator[str, None, list[RAGSource]]:
    rag_context = prepare_rag_context(question)
    return stream_answer_from_context(rag_context, conversation_history)


def stream_answer_from_context(
    rag_context: RAGContext,
    conversation_history: list[Mapping[str, str]] | None = None,
) -> Generator[str, None, list[RAGSource]]:
    try:
        for chunk in generate_answer_stream(
            rag_context.question,
            rag_context.context,
            conversation_history,
        ):
            yield chunk
    except (GroqConfigurationError, GroqServiceError) as exc:
        raise LLMUnavailableError("LLM service unavailable") from exc

    return rag_context.sources
