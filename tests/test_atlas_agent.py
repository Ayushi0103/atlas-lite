import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR / "backend"))

from app.models import Conversation, Message  # noqa: E402
from app.services.atlas_agent import (  # noqa: E402
    NO_KNOWLEDGE_BASE_ANSWER,
    DEFAULT_INTENT_DETECTOR,
    run_agent,
)


class AtlasAgentTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        SQLModel.metadata.create_all(self.engine)

    def tearDown(self):
        SQLModel.metadata.drop_all(self.engine)

    def get_session(self):
        return Session(self.engine)

    def test_intent_detection(self):
        cases = {
            "What is a transformer?": "knowledge_lookup",
            "How is LoRA related to PEFT?": "relationship_lookup",
            "What books have I uploaded?": "document_lookup",
            "Summarize AI Engineering": "document_summary",
            "What did we discuss yesterday?": "conversation_lookup",
            "Show notes from AI Collection": "collection_lookup",
            "Write a friendly greeting": "general_question",
        }

        for question, expected_intent in cases.items():
            with self.subTest(question=question):
                self.assertEqual(
                    DEFAULT_INTENT_DETECTOR.detect(question),
                    expected_intent,
                )

    def test_knowledge_lookup_uses_semantic_search_then_groq(self):
        semantic_results = [
            {
                "type": "document",
                "id": 1,
                "score": 0.91,
                "text": "Transformers use attention mechanisms.",
                "filename": "ai.txt",
                "title": None,
            }
        ]

        with self.get_session() as session:
            with patch(
                "app.services.atlas_agent.semantic_search",
                return_value=semantic_results,
            ) as semantic_search:
                with patch(
                    "app.services.atlas_agent.generate_answer",
                    return_value="A transformer uses attention.",
                ) as generate_answer:
                    response = run_agent("What is a transformer?", session)

        self.assertEqual(response["intent"], "knowledge_lookup")
        self.assertEqual(response["tools_used"], ["SemanticSearch", "Groq"])
        self.assertIn("Transformers use attention", response["context"])
        self.assertEqual(response["answer"], "A transformer uses attention.")
        semantic_search.assert_called_once()
        generate_answer.assert_called_once()

    def test_semantic_search_falls_back_to_keyword_search(self):
        with self.get_session() as session:
            with patch("app.services.atlas_agent.semantic_search", return_value=[]):
                with patch(
                    "app.services.atlas_agent._keyword_search",
                    return_value=[
                        {
                            "type": "note",
                            "id": 1,
                            "title": "RAG note",
                            "text": "RAG retrieves context before answering.",
                        }
                    ],
                ):
                    with patch(
                        "app.services.atlas_agent.generate_answer",
                        return_value="RAG retrieves context first.",
                    ):
                        response = run_agent("Explain RAG", session)

        self.assertEqual(
            response["tools_used"],
            ["SemanticSearch", "KeywordSearch", "Groq"],
        )
        self.assertIn("Keyword Search Results", response["context"])
        self.assertEqual(response["answer"], "RAG retrieves context first.")

    def test_no_search_results_returns_knowledge_base_message(self):
        with self.get_session() as session:
            with patch("app.services.atlas_agent.semantic_search", return_value=[]):
                with patch("app.services.atlas_agent._keyword_search", return_value=[]):
                    with patch("app.services.atlas_agent.generate_answer") as generate_answer:
                        response = run_agent("Explain missing topic", session)

        self.assertEqual(
            response["tools_used"],
            ["SemanticSearch", "KeywordSearch"],
        )
        self.assertEqual(response["context"], "")
        self.assertEqual(response["answer"], NO_KNOWLEDGE_BASE_ANSWER)
        generate_answer.assert_not_called()

    def test_knowledge_graph_query_uses_graph_context(self):
        graph = {
            "concept": "LoRA",
            "related": [
                {
                    "relationship": "adapts",
                    "target": "PEFT",
                    "type": "method",
                }
            ],
        }

        with self.get_session() as session:
            with patch(
                "app.services.atlas_agent.get_related_concepts",
                return_value=graph,
            ) as get_related:
                with patch(
                    "app.services.atlas_agent.generate_answer",
                    return_value="LoRA is connected to PEFT.",
                ):
                    response = run_agent("How is LoRA related to PEFT?", session)

        self.assertEqual(response["intent"], "relationship_lookup")
        self.assertEqual(response["tools_used"], ["KnowledgeGraph", "Groq"])
        self.assertIn("Knowledge Graph: LoRA", response["context"])
        get_related.assert_called_once_with("LoRA", session)

    def test_conversation_query_uses_memory(self):
        with self.get_session() as session:
            conversation = Conversation(title="Memory")
            session.add(conversation)
            session.commit()
            session.refresh(conversation)

            session.add(
                Message(
                    conversation_id=conversation.id,
                    role="user",
                    content="We discussed local-first RAG.",
                )
            )
            session.add(
                Message(
                    conversation_id=conversation.id,
                    role="assistant",
                    content="Atlas stores private knowledge locally.",
                )
            )
            session.commit()

            with patch(
                "app.services.atlas_agent.generate_answer",
                return_value="We discussed local-first RAG.",
            ):
                response = run_agent(
                    "What did we discuss yesterday?",
                    session,
                    conversation_id=conversation.id,
                )

        self.assertEqual(response["intent"], "conversation_lookup")
        self.assertEqual(response["tools_used"], ["ConversationMemory", "Groq"])
        self.assertIn("We discussed local-first RAG", response["context"])
        self.assertEqual(response["answer"], "We discussed local-first RAG.")


if __name__ == "__main__":
    unittest.main()
