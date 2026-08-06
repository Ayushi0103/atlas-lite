import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR / "backend"))

from app.models import Document, KnowledgeGraphEdge, KnowledgeGraphNode  # noqa: E402
from app.routes.knowledge_graph import read_knowledge_graph  # noqa: E402
from app.services.knowledge_graph import (  # noqa: E402
    ExtractedNode,
    ExtractedRelationship,
    KnowledgeGraphExtraction,
    store_knowledge_graph,
)
from app.services.summary_service import (  # noqa: E402
    DocumentSummary,
    summarize_and_store_document_metadata,
)


class KnowledgeGraphTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        SQLModel.metadata.create_all(self.engine)

    def get_session(self):
        return Session(self.engine)

    def test_store_knowledge_graph_avoids_duplicate_nodes_and_edges(self):
        extraction = KnowledgeGraphExtraction(
            entities=[
                ExtractedNode(name="Python", type="Language"),
                ExtractedNode(name="python", type="language"),
            ],
            concepts=[ExtractedNode(name="FastAPI", type="Framework")],
            relationships=[
                ExtractedRelationship(
                    source="Python",
                    source_type="Language",
                    target="FastAPI",
                    target_type="Framework",
                    relationship="uses",
                ),
                ExtractedRelationship(
                    source="python",
                    source_type="language",
                    target="FastAPI",
                    target_type="framework",
                    relationship="USES",
                ),
            ],
        )

        with self.get_session() as session:
            store_knowledge_graph(extraction, session)
            store_knowledge_graph(extraction, session)

            nodes = session.exec(select(KnowledgeGraphNode)).all()
            edges = session.exec(select(KnowledgeGraphEdge)).all()

            self.assertEqual(len(nodes), 2)
            self.assertEqual(len(edges), 1)

            response = read_knowledge_graph("python", session)
            self.assertEqual(
                response,
                {
                    "concept": "Python",
                    "related": [
                        {
                            "relationship": "uses",
                            "target": "FastAPI",
                            "type": "framework",
                        }
                    ],
                },
            )

    def test_summary_returns_when_knowledge_graph_generation_fails(self):
        summary = DocumentSummary(
            short_summary="Short.",
            detailed_summary="Detailed.",
            key_concepts=["Python"],
            keywords=["python"],
            suggested_questions=["What is Python?"],
        )

        with self.get_session() as session:
            document = Document(
                filename="python.txt",
                file_type="txt",
                file_path="uploads/python.txt",
                text_content="Python is a programming language.",
            )
            session.add(document)
            session.commit()
            session.refresh(document)

            with patch(
                "app.services.summary_service.generate_document_summary",
                return_value=summary,
            ):
                with patch(
                    "app.services.summary_service.generate_knowledge_graph_for_document",
                    side_effect=RuntimeError("Groq unavailable"),
                ):
                    result = summarize_and_store_document_metadata(document, session)

            self.assertEqual(result.short_summary, "Short.")
            refreshed = session.get(Document, document.id)
            self.assertIsNotNone(refreshed)
            self.assertEqual(refreshed.short_summary, "Short.")


if __name__ == "__main__":
    unittest.main()
