import logging
import re
from dataclasses import dataclass, field
from typing import Protocol, TypedDict

from sqlalchemy import or_
from sqlmodel import Session, select

from app.models import Collection, CollectionNote, Conversation, Document, Message, Note
from app.services.embedding import SemanticSearchResult, semantic_search
from app.services.groq_client import (
    GroqConfigurationError,
    GroqServiceError,
    generate_answer,
)
from app.services.knowledge_graph import get_related_concepts


logger = logging.getLogger("AtlasAgent")

TOP_K = 5
NO_KNOWLEDGE_BASE_ANSWER = (
    "I couldn't find this information in your Atlas knowledge base."
)


class AgentResponse(TypedDict):
    intent: str
    tools_used: list[str]
    context: str
    answer: str


@dataclass(frozen=True)
class ToolResult:
    name: str
    context: str = ""
    data: object | None = None
    found: bool = True


@dataclass
class AgentState:
    question: str
    session: Session
    conversation_id: int | None = None
    intent: str = "general_question"
    tool_results: list[ToolResult] = field(default_factory=list)
    context_sections: list[str] = field(default_factory=list)
    answer: str = ""

    @property
    def tools_used(self) -> list[str]:
        return [result.name for result in self.tool_results]

    def add_result(self, result: ToolResult) -> None:
        self.tool_results.append(result)
        if result.context:
            self.context_sections.append(result.context)

    def build_context(self) -> str:
        return "\n\n".join(self.context_sections).strip()


class AgentTool(Protocol):
    name: str

    def run(self, state: AgentState) -> ToolResult:
        ...


@dataclass(frozen=True)
class IntentRule:
    intent: str
    patterns: tuple[str, ...]

    def matches(self, question: str) -> bool:
        return any(re.search(pattern, question, re.IGNORECASE) for pattern in self.patterns)


class IntentDetector:
    def __init__(self, rules: list[IntentRule], default_intent: str) -> None:
        self.rules = rules
        self.default_intent = default_intent

    def detect(self, question: str) -> str:
        cleaned_question = question.strip()
        for rule in self.rules:
            if rule.matches(cleaned_question):
                return rule.intent

        return self.default_intent


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, AgentTool] = {}

    def register(self, tool: AgentTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> AgentTool:
        return self._tools[name]


class SemanticSearchTool:
    name = "SemanticSearch"

    def run(self, state: AgentState) -> ToolResult:
        results = semantic_search(state.question, top_k=TOP_K)
        logger.info("Search returned %s chunks", len(results))

        return ToolResult(
            name=self.name,
            context=_format_search_results("Search Results", results),
            data=results,
            found=bool(results),
        )


class KeywordSearchTool:
    name = "KeywordSearch"

    def run(self, state: AgentState) -> ToolResult:
        results = _keyword_search(state.question, state.session)
        logger.info("Keyword search returned %s results", len(results))

        return ToolResult(
            name=self.name,
            context=_format_keyword_results(results),
            data=results,
            found=bool(results),
        )


class KnowledgeGraphTool:
    name = "KnowledgeGraph"

    def run(self, state: AgentState) -> ToolResult:
        concept = _extract_lookup_subject(state.question)
        graph = get_related_concepts(concept, state.session)
        related = graph.get("related", [])
        logger.info("Knowledge graph returned %s nodes", len(related))

        return ToolResult(
            name=self.name,
            context=_format_knowledge_graph(graph),
            data=graph,
            found=bool(related),
        )


class ConversationMemoryTool:
    name = "ConversationMemory"

    def run(self, state: AgentState) -> ToolResult:
        messages = _get_conversation_messages(state.session, state.conversation_id)
        logger.info("Conversation memory returned %s messages", len(messages))

        return ToolResult(
            name=self.name,
            context=_format_conversation(messages),
            data=messages,
            found=bool(messages),
        )


class DocumentMetadataTool:
    name = "DocumentMetadata"

    def run(self, state: AgentState) -> ToolResult:
        documents = _find_documents(state.question, state.session)
        logger.info("Document metadata returned %s documents", len(documents))

        return ToolResult(
            name=self.name,
            context=_format_documents(documents),
            data=documents,
            found=bool(documents),
        )


class CollectionTool:
    name = "Collections"

    def run(self, state: AgentState) -> ToolResult:
        collections = _find_collections(state.question, state.session)
        logger.info("Collections returned %s collections", len(collections))

        return ToolResult(
            name=self.name,
            context=_format_collections(collections, state.session),
            data=collections,
            found=bool(collections),
        )


class GroqTool:
    name = "Groq"

    def run(self, state: AgentState) -> ToolResult:
        context = state.build_context()
        if not context:
            return ToolResult(name=self.name, found=False)

        try:
            answer = generate_answer(state.question, context)
        except (GroqConfigurationError, GroqServiceError):
            logger.exception("Groq failed while running Atlas Agent")
            raise

        state.answer = answer
        return ToolResult(name=self.name, data=answer, found=bool(answer))


DEFAULT_INTENT_DETECTOR = IntentDetector(
    rules=[
        IntentRule(
            intent="conversation_lookup",
            patterns=(
                r"\bwhat did we discuss\b",
                r"\bprevious conversation\b",
                r"\bconversation history\b",
                r"\bwhat did (i|we) say\b",
                r"\byesterday\b",
            ),
        ),
        IntentRule(
            intent="collection_lookup",
            patterns=(r"\bcollection\b", r"\bcollections\b"),
        ),
        IntentRule(
            intent="document_summary",
            patterns=(r"\bsummarize\b", r"\bsummary\b", r"\btldr\b"),
        ),
        IntentRule(
            intent="document_lookup",
            patterns=(
                r"\bwhat (books|documents|pdfs|files)\b",
                r"\bshow (my )?(books|documents|pdfs|files)\b",
                r"\blist (my )?(books|documents|pdfs|files)\b",
                r"\buploaded\b",
            ),
        ),
        IntentRule(
            intent="relationship_lookup",
            patterns=(
                r"\brelated to\b",
                r"\brelationship\b",
                r"\brelationships\b",
                r"\bconcepts?\b",
                r"\bconnected to\b",
            ),
        ),
        IntentRule(
            intent="knowledge_lookup",
            patterns=(
                r"^\s*what is\b",
                r"^\s*what are\b",
                r"^\s*explain\b",
                r"^\s*define\b",
                r"^\s*how does\b",
                r"^\s*why\b",
            ),
        ),
    ],
    default_intent="general_question",
)


DEFAULT_TOOL_REGISTRY = ToolRegistry()
DEFAULT_TOOL_REGISTRY.register(SemanticSearchTool())
DEFAULT_TOOL_REGISTRY.register(KeywordSearchTool())
DEFAULT_TOOL_REGISTRY.register(KnowledgeGraphTool())
DEFAULT_TOOL_REGISTRY.register(ConversationMemoryTool())
DEFAULT_TOOL_REGISTRY.register(DocumentMetadataTool())
DEFAULT_TOOL_REGISTRY.register(CollectionTool())
DEFAULT_TOOL_REGISTRY.register(GroqTool())


TOOL_PLANS: dict[str, tuple[str, ...]] = {
    "knowledge_lookup": ("SemanticSearch", "Groq"),
    "relationship_lookup": ("KnowledgeGraph", "Groq"),
    "document_lookup": ("DocumentMetadata", "Groq"),
    "document_summary": ("DocumentMetadata", "Groq"),
    "conversation_lookup": ("ConversationMemory", "Groq"),
    "collection_lookup": ("Collections", "Groq"),
    "general_question": ("SemanticSearch", "Groq"),
}


def run_agent(
    question: str,
    session: Session,
    conversation_id: int | None = None,
) -> AgentResponse:
    cleaned_question = question.strip()
    state = AgentState(
        question=cleaned_question,
        session=session,
        conversation_id=conversation_id,
    )
    state.intent = DEFAULT_INTENT_DETECTOR.detect(cleaned_question)
    selected_tools = TOOL_PLANS.get(state.intent, TOOL_PLANS["general_question"])

    logger.info("Intent detected: %s", state.intent)
    logger.info("Selected tools: %s", ", ".join(selected_tools))

    for tool_name in selected_tools:
        if tool_name == "Groq" and not state.build_context():
            state.answer = NO_KNOWLEDGE_BASE_ANSWER
            break

        result = DEFAULT_TOOL_REGISTRY.get(tool_name).run(state)
        state.add_result(result)

        if tool_name == "SemanticSearch" and not result.found:
            fallback_result = DEFAULT_TOOL_REGISTRY.get("KeywordSearch").run(state)
            state.add_result(fallback_result)
            if not fallback_result.found:
                state.answer = NO_KNOWLEDGE_BASE_ANSWER
                break

    if not state.answer and not state.build_context():
        state.answer = NO_KNOWLEDGE_BASE_ANSWER

    return {
        "intent": state.intent,
        "tools_used": state.tools_used,
        "context": state.build_context(),
        "answer": state.answer,
    }


def _keyword_search(query: str, session: Session) -> list[dict[str, object]]:
    cleaned_query = query.strip()
    if not cleaned_query:
        return []

    note_statement = (
        select(Note)
        .where(
            or_(
                Note.title.contains(cleaned_query),
                Note.content.contains(cleaned_query),
                Note.tags.contains(cleaned_query),
            )
        )
        .limit(TOP_K)
    )
    document_statement = (
        select(Document)
        .where(
            or_(
                Document.filename.contains(cleaned_query),
                Document.text_content.contains(cleaned_query),
                Document.short_summary.contains(cleaned_query),
                Document.detailed_summary.contains(cleaned_query),
                Document.key_concepts.contains(cleaned_query),
                Document.keywords.contains(cleaned_query),
                Document.suggested_questions.contains(cleaned_query),
            )
        )
        .limit(TOP_K)
    )

    results: list[dict[str, object]] = []
    for note in session.exec(note_statement).all():
        results.append(
            {
                "type": "note",
                "id": note.id,
                "title": note.title,
                "text": note.content,
            }
        )

    for document in session.exec(document_statement).all():
        results.append(
            {
                "type": "document",
                "id": document.id,
                "title": document.filename,
                "text": document.short_summary or document.text_content,
            }
        )

    return results[:TOP_K]


def _get_conversation_messages(
    session: Session,
    conversation_id: int | None,
    limit: int = 12,
) -> list[Message]:
    statement = select(Message)
    if conversation_id is not None:
        statement = statement.where(Message.conversation_id == conversation_id)

    statement = statement.order_by(Message.created_at.desc(), Message.id.desc()).limit(limit)
    messages = list(session.exec(statement).all())
    messages.reverse()
    return messages


def _find_documents(question: str, session: Session) -> list[Document]:
    subject = _extract_lookup_subject(question)
    statement = select(Document)

    if _is_document_listing_question(question):
        file_type = _extract_file_type(question)
        if file_type:
            statement = statement.where(Document.file_type == file_type)
        return list(session.exec(statement.order_by(Document.created_at.desc())).all())

    statement = statement.where(
        or_(
            Document.filename.contains(subject),
            Document.short_summary.contains(subject),
            Document.detailed_summary.contains(subject),
            Document.key_concepts.contains(subject),
            Document.keywords.contains(subject),
            Document.suggested_questions.contains(subject),
        )
    )
    return list(session.exec(statement.order_by(Document.created_at.desc())).all())


def _find_collections(question: str, session: Session) -> list[Collection]:
    subject = _extract_lookup_subject(question)
    statement = select(Collection)

    if subject and subject.lower() not in {"collection", "collections"}:
        statement = statement.where(
            or_(
                Collection.name.contains(subject),
                Collection.description.contains(subject),
            )
        )

    return list(session.exec(statement.order_by(Collection.updated_at.desc())).all())


def _extract_file_type(question: str) -> str | None:
    lower_question = question.lower()
    file_type_aliases = {
        "pdf": ("pdf", "pdfs"),
        "docx": ("docx", "word documents"),
        "txt": ("txt", "text files"),
        "md": ("md", "markdown"),
        "youtube": ("youtube", "videos", "transcripts"),
    }
    for file_type, aliases in file_type_aliases.items():
        if any(alias in lower_question for alias in aliases):
            return file_type

    return None


def _is_document_listing_question(question: str) -> bool:
    return bool(
        re.search(
            r"\b(show|list|what)\b.*\b(documents|books|pdfs|files|uploaded)\b",
            question,
            re.IGNORECASE,
        )
    )


def _extract_lookup_subject(question: str) -> str:
    subject = question.strip().strip("?.!")
    removals = (
        r"^\s*how is\s+",
        r"^\s*how are\s+",
        r"^\s*show\s+(my\s+)?",
        r"^\s*list\s+(my\s+)?",
        r"^\s*what (is|are|books|documents|pdfs|files|did we discuss)\s+",
        r"^\s*explain\s+",
        r"^\s*define\s+",
        r"^\s*summarize\s+",
        r"\s+related to\s+.*$",
        r"\s+from\s+.*collection$",
        r"\s+collection$",
        r"\s+concepts?$",
    )
    for pattern in removals:
        subject = re.sub(pattern, "", subject, flags=re.IGNORECASE).strip()

    return subject or question.strip().strip("?.!")


def _format_search_results(
    heading: str,
    results: list[SemanticSearchResult],
) -> str:
    if not results:
        return ""

    sections = [f"{heading}:"]
    for index, result in enumerate(results, start=1):
        title = result.get("filename") or result.get("title") or f"Source {result['id']}"
        sections.append(
            "\n".join(
                [
                    f"[{index}] {result['type']} {result['id']}: {title}",
                    f"Score: {result['score']:.2f}",
                    str(result["text"]),
                ]
            )
        )

    return "\n\n".join(sections)


def _format_keyword_results(results: list[dict[str, object]]) -> str:
    if not results:
        return ""

    sections = ["Keyword Search Results:"]
    for index, result in enumerate(results, start=1):
        sections.append(
            "\n".join(
                [
                    f"[{index}] {result['type']} {result['id']}: {result['title']}",
                    str(result["text"]),
                ]
            )
        )

    return "\n\n".join(sections)


def _format_knowledge_graph(graph: dict) -> str:
    related = graph.get("related", [])
    if not related:
        return ""

    lines = [f"Knowledge Graph: {graph.get('concept', '')}"]
    for item in related:
        lines.append(
            "- {relationship}: {target} ({type})".format(
                relationship=item.get("relationship", "related to"),
                target=item.get("target", ""),
                type=item.get("type", ""),
            )
        )

    return "\n".join(lines)


def _format_conversation(messages: list[Message]) -> str:
    if not messages:
        return ""

    lines = ["Conversation:"]
    for message in messages:
        lines.append(f"{message.role}: {message.content}")

    return "\n".join(lines)


def _format_documents(documents: list[Document]) -> str:
    if not documents:
        return ""

    sections = ["Relevant Documents:"]
    for document in documents:
        sections.append(
            "\n".join(
                [
                    f"Document {document.id}: {document.filename}",
                    f"Type: {document.file_type}",
                    f"Short summary: {document.short_summary or ''}",
                    f"Detailed summary: {document.detailed_summary or ''}",
                    f"Keywords: {document.keywords or ''}",
                    f"Concepts: {document.key_concepts or ''}",
                    f"Suggested questions: {document.suggested_questions or ''}",
                ]
            )
        )

    return "\n\n".join(sections)


def _format_collections(collections: list[Collection], session: Session) -> str:
    if not collections:
        return ""

    sections = ["Collections:"]
    for collection in collections:
        note_statement = (
            select(Note)
            .join(CollectionNote, CollectionNote.note_id == Note.id)
            .where(CollectionNote.collection_id == collection.id)
            .order_by(Note.updated_at.desc())
        )
        notes = list(session.exec(note_statement).all())
        note_lines = [f"- {note.title}: {note.content}" for note in notes]
        sections.append(
            "\n".join(
                [
                    f"Collection {collection.id}: {collection.name}",
                    f"Description: {collection.description or ''}",
                    "Notes:",
                    *note_lines,
                ]
            )
        )

    return "\n\n".join(sections)
