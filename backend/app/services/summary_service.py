import json
import logging
import re
from datetime import datetime

from pydantic import BaseModel, Field, ValidationError, field_validator
from sqlmodel import Session

from app.models import Document
from app.services.groq_client import generate_chat_completion


logger = logging.getLogger(__name__)

MAX_SUMMARY_INPUT_CHARS = 24000

SUMMARY_SYSTEM_PROMPT = """You are Atlas Lite's AI knowledge summarization engine.

Generate accurate metadata only from the supplied source text.
Return only valid JSON with these exact keys:
short_summary, detailed_summary, key_concepts, keywords, suggested_questions."""


class SummaryGenerationError(RuntimeError):
    pass


class DocumentSummary(BaseModel):
    short_summary: str = Field(min_length=1)
    detailed_summary: str = Field(min_length=1)
    key_concepts: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)

    @field_validator(
        "key_concepts",
        "keywords",
        "suggested_questions",
        mode="before",
    )
    @classmethod
    def ensure_string_list(cls, value):
        if value is None:
            return []

        if isinstance(value, str):
            return [value]

        if not isinstance(value, list):
            return []

        return [str(item).strip() for item in value if str(item).strip()]


def generate_document_summary(document: Document) -> DocumentSummary:
    text = _prepare_source_text(document.text_content)
    if not text:
        raise SummaryGenerationError("Document has no text content to summarize")

    prompt = "\n".join(
        [
            f"Filename: {document.filename}",
            f"File type: {document.file_type}",
            "",
            "Source text:",
            text,
            "",
            "JSON requirements:",
            "- short_summary: 1-2 concise sentences.",
            "- detailed_summary: 2-4 paragraphs covering the core ideas.",
            "- key_concepts: 5-10 important concepts or entities.",
            "- keywords: 8-15 search-friendly keywords.",
            "- suggested_questions: 5-8 useful questions this source can answer.",
        ]
    )

    response = generate_chat_completion(
        [
            {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
    )

    return _parse_summary_response(response)


def summarize_and_store_document_metadata(
    document: Document,
    session: Session,
) -> DocumentSummary:
    summary = generate_document_summary(document)

    document.short_summary = summary.short_summary
    document.detailed_summary = summary.detailed_summary
    document.key_concepts = json.dumps(summary.key_concepts)
    document.keywords = json.dumps(summary.keywords)
    document.suggested_questions = json.dumps(summary.suggested_questions)
    document.updated_at = datetime.now()

    session.add(document)
    session.commit()
    session.refresh(document)

    logger.info("Stored AI summary metadata for document %s", document.id)
    return summary


def build_document_embedding_text(document: Document) -> str:
    parts = [
        document.filename,
        document.text_content,
        document.short_summary,
        document.detailed_summary,
        _json_list_to_text(document.key_concepts),
        _json_list_to_text(document.keywords),
        _json_list_to_text(document.suggested_questions),
    ]

    return "\n\n".join(part.strip() for part in parts if part and part.strip())


def _prepare_source_text(text: str) -> str:
    cleaned_text = text.strip()
    if len(cleaned_text) <= MAX_SUMMARY_INPUT_CHARS:
        return cleaned_text

    half = MAX_SUMMARY_INPUT_CHARS // 2
    return "\n\n".join(
        [
            cleaned_text[:half],
            "[Middle of source omitted for summarization input length.]",
            cleaned_text[-half:],
        ]
    )


def _parse_summary_response(response: str) -> DocumentSummary:
    try:
        payload = json.loads(_extract_json_object(response))
        return DocumentSummary.model_validate(payload)
    except (json.JSONDecodeError, ValidationError, TypeError) as exc:
        logger.exception("Could not parse Groq summary response")
        raise SummaryGenerationError("Could not parse summary response") from exc


def _extract_json_object(response: str) -> str:
    cleaned_response = response.strip()
    fenced_match = re.search(
        r"```(?:json)?\s*(\{.*?\})\s*```",
        cleaned_response,
        flags=re.DOTALL,
    )
    if fenced_match:
        return fenced_match.group(1)

    start = cleaned_response.find("{")
    end = cleaned_response.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return cleaned_response

    return cleaned_response[start : end + 1]


def _json_list_to_text(value: str | None) -> str:
    if not value:
        return ""

    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return value

    if not isinstance(parsed, list):
        return ""

    return "\n".join(str(item).strip() for item in parsed if str(item).strip())
