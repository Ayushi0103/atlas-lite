import json
import logging
import re

from pydantic import BaseModel, Field, ValidationError, field_validator
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models import Document, KnowledgeGraphEdge, KnowledgeGraphNode
from app.services.groq_client import generate_chat_completion


logger = logging.getLogger(__name__)

MAX_GRAPH_INPUT_CHARS = 24000

KNOWLEDGE_GRAPH_SYSTEM_PROMPT = """You are Atlas Lite's knowledge graph extraction engine.

Extract entities, concepts, and relationships only from the supplied document.
Return only valid JSON with these exact keys:
entities, concepts, relationships."""


class KnowledgeGraphGenerationError(RuntimeError):
    pass


class ExtractedNode(BaseModel):
    name: str = Field(min_length=1)
    type: str = Field(min_length=1)

    @field_validator("name", "type", mode="before")
    @classmethod
    def clean_text(cls, value):
        return str(value).strip()


class ExtractedRelationship(BaseModel):
    source: str = Field(min_length=1)
    target: str = Field(min_length=1)
    relationship: str = Field(min_length=1)
    source_type: str | None = None
    target_type: str | None = None

    @field_validator(
        "source",
        "target",
        "relationship",
        "source_type",
        "target_type",
        mode="before",
    )
    @classmethod
    def clean_text(cls, value):
        if value is None:
            return None

        cleaned = str(value).strip()
        return cleaned or None


class KnowledgeGraphExtraction(BaseModel):
    entities: list[ExtractedNode] = Field(default_factory=list)
    concepts: list[ExtractedNode] = Field(default_factory=list)
    relationships: list[ExtractedRelationship] = Field(default_factory=list)

    @field_validator("entities", "concepts", mode="before")
    @classmethod
    def normalize_nodes(cls, value):
        if value is None:
            return []

        if not isinstance(value, list):
            return []

        nodes = []
        for item in value:
            if isinstance(item, ExtractedNode):
                nodes.append(item)
            elif isinstance(item, str):
                nodes.append({"name": item, "type": "concept"})
            elif isinstance(item, dict):
                nodes.append(item)

        return nodes

    @field_validator("relationships", mode="before")
    @classmethod
    def normalize_relationships(cls, value):
        if not isinstance(value, list):
            return []

        return [
            item
            for item in value
            if isinstance(item, dict) or isinstance(item, ExtractedRelationship)
        ]


def generate_knowledge_graph_for_document(
    document: Document,
    session: Session,
) -> KnowledgeGraphExtraction:
    extraction = extract_knowledge_graph(document)
    store_knowledge_graph(extraction, session)

    logger.info(
        "Knowledge graph generated",
        extra={
            "document_id": document.id,
            "entity_count": len(extraction.entities),
            "concept_count": len(extraction.concepts),
            "relationship_count": len(extraction.relationships),
        },
    )
    return extraction


def extract_knowledge_graph(document: Document) -> KnowledgeGraphExtraction:
    source_text = document.short_summary
    if not source_text:
        raise KnowledgeGraphGenerationError("Document has no text content to extract")

    prompt = "\n".join(
        [
            f"Filename: {document.filename}",
            f"File type: {document.file_type}",
            "",
            "Source text:",
            source_text,
            "",
            "JSON requirements:",
            "- entities: objects with name and type for people, products, tools, organizations, places, or named things.",
            "- concepts: objects with name and type for important ideas, topics, methods, or domains.",
            "- relationships: objects with source, target, relationship, source_type, and target_type.",
            "- Keep relationship labels concise, lowercase, and verb-like.",
            "- Use names exactly and consistently across nodes and relationships.",
        ]
    )

    response = generate_chat_completion(
        [
            {"role": "system", "content": KNOWLEDGE_GRAPH_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
    )

    print("\n================ RAW GROQ RESPONSE ================\n")
    print(repr(response))
    print("\n==================================================\n")

    return _parse_graph_response(response)


def store_knowledge_graph(
    extraction: KnowledgeGraphExtraction,
    session: Session,
) -> None:
    nodes_by_key: dict[tuple[str, str], KnowledgeGraphNode] = {}

    for extracted_node in [*extraction.entities, *extraction.concepts]:
        node = _get_or_create_node(
            session,
            extracted_node.name,
            extracted_node.type,
        )
        if node.id is not None:
            nodes_by_key[_node_key(node.name, node.type)] = node

    for relationship in extraction.relationships:
        source_type = relationship.source_type or "entity"
        target_type = relationship.target_type or "concept"

        source = nodes_by_key.get(_node_key(relationship.source, source_type))
        if source is None:
            source = _get_or_create_node(session, relationship.source, source_type)

        target = nodes_by_key.get(_node_key(relationship.target, target_type))
        if target is None:
            target = _get_or_create_node(session, relationship.target, target_type)

        if source.id is None or target.id is None:
            continue

        _get_or_create_edge(
            session,
            source.id,
            target.id,
            relationship.relationship,
        )

    session.commit()


def get_related_concepts(concept: str, session: Session) -> dict:
    concept = concept.strip()
    source_node = session.exec(
        select(KnowledgeGraphNode).where(
            KnowledgeGraphNode.name.ilike(f"%{concept}%")
        )
    ).first()
    if source_node is None or source_node.id is None:
        return {"concept": concept, "related": []}

    edges = session.exec(
        select(KnowledgeGraphEdge, KnowledgeGraphNode)
        .join(
            KnowledgeGraphNode,
            KnowledgeGraphEdge.target_node_id == KnowledgeGraphNode.id,
        )
        .where(KnowledgeGraphEdge.source_node_id == source_node.id)
        .order_by(KnowledgeGraphNode.name)
    ).all()

    return {
        "concept": source_node.name,
        "related": [
            {
                "relationship": edge.relationship,
                "target": target.name,
                "type": target.type,
            }
            for edge, target in edges
        ],
    }


def _get_or_create_node(
    session: Session,
    name: str,
    node_type: str,
) -> KnowledgeGraphNode:
    normalized_name = _normalize_name(name)
    normalized_type = _normalize_type(node_type)

    node = session.exec(
        select(KnowledgeGraphNode).where(
            func.lower(KnowledgeGraphNode.name) == normalized_name.lower(),
            func.lower(KnowledgeGraphNode.type) == normalized_type.lower(),
        )
    ).first()
    if node is not None:
        return node

    node = KnowledgeGraphNode(name=normalized_name, type=normalized_type)
    session.add(node)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        existing_node = session.exec(
            select(KnowledgeGraphNode).where(
                func.lower(KnowledgeGraphNode.name) == normalized_name.lower(),
                func.lower(KnowledgeGraphNode.type) == normalized_type.lower(),
            )
        ).first()
        if existing_node is None:
            raise

        return existing_node

    session.refresh(node)
    logger.info(
        "Knowledge graph node stored",
        extra={"node_id": node.id, "name": node.name, "type": node.type},
    )
    return node


def _get_or_create_edge(
    session: Session,
    source_node_id: int,
    target_node_id: int,
    relationship: str,
) -> KnowledgeGraphEdge:
    normalized_relationship = _normalize_type(relationship)
    edge = session.exec(
        select(KnowledgeGraphEdge).where(
            KnowledgeGraphEdge.source_node_id == source_node_id,
            KnowledgeGraphEdge.target_node_id == target_node_id,
            func.lower(KnowledgeGraphEdge.relationship)
            == normalized_relationship.lower(),
        )
    ).first()
    if edge is not None:
        return edge

    edge = KnowledgeGraphEdge(
        source_node_id=source_node_id,
        target_node_id=target_node_id,
        relationship=normalized_relationship,
    )
    session.add(edge)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        existing_edge = session.exec(
            select(KnowledgeGraphEdge).where(
                KnowledgeGraphEdge.source_node_id == source_node_id,
                KnowledgeGraphEdge.target_node_id == target_node_id,
                func.lower(KnowledgeGraphEdge.relationship)
                == normalized_relationship.lower(),
            )
        ).first()
        if existing_edge is None:
            raise

        return existing_edge

    session.refresh(edge)
    logger.info(
        "Knowledge graph edge stored",
        extra={
            "edge_id": edge.id,
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "relationship": normalized_relationship,
        },
    )
    return edge


def _prepare_source_text(text: str) -> str:
    cleaned_text = text.strip()
    if len(cleaned_text) <= MAX_GRAPH_INPUT_CHARS:
        return cleaned_text

    half = MAX_GRAPH_INPUT_CHARS // 2
    return "\n\n".join(
        [
            cleaned_text[:half],
            "[Middle of source omitted for knowledge graph input length.]",
            cleaned_text[-half:],
        ]
    )


def _parse_graph_response(response: str) -> KnowledgeGraphExtraction:
    try:
        payload = json.loads(_extract_json_object(response))
        return KnowledgeGraphExtraction.model_validate(payload)
    except (json.JSONDecodeError, ValidationError, TypeError) as exc:
        logger.exception("Could not parse Groq knowledge graph response")
        raise KnowledgeGraphGenerationError(
            "Could not parse knowledge graph response"
        ) from exc


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


def _normalize_name(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _normalize_type(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def _node_key(name: str, node_type: str) -> tuple[str, str]:
    return (_normalize_name(name).lower(), _normalize_type(node_type).lower())
