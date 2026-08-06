import sys
import unittest
from pathlib import Path
from unittest.mock import ANY, patch

from fastapi.testclient import TestClient


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR / "backend"))

from app.database import get_session  # noqa: E402
from app.main import app  # noqa: E402
from app.services.groq_client import (  # noqa: E402
    GroqConfigurationError,
    GroqServiceError,
)


class AgentRouterTests(unittest.TestCase):
    def setUp(self):
        self.session = object()

        def override_session():
            yield self.session

        app.dependency_overrides[get_session] = override_session
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_agent_chat_returns_200(self):
        mocked_response = {
            "intent": "knowledge_lookup",
            "tools_used": ["SemanticSearch", "Groq"],
            "context": "Relevant context",
            "answer": "AI Engineering is a discipline.",
        }

        with patch("app.routes.agent.run_agent", return_value=mocked_response) as run_agent:
            response = self.client.post(
                "/agent/chat",
                json={"question": "What is AI Engineering?"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), mocked_response)
        run_agent.assert_called_once_with(
            question="What is AI Engineering?",
            session=ANY,
            conversation_id=None,
        )

    def test_agent_chat_returns_mocked_relationship_data(self):
        mocked_response = {
            "intent": "relationship_lookup",
            "tools_used": ["KnowledgeGraph", "Groq"],
            "context": "AI Engineering relates to RAG.",
            "answer": "AI Engineering is related to RAG.",
        }

        with patch("app.routes.agent.run_agent", return_value=mocked_response):
            response = self.client.post(
                "/agent/chat",
                json={"question": "What is related to AI Engineering?"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), mocked_response)

    def test_agent_chat_passes_conversation_id(self):
        mocked_response = {
            "intent": "conversation_lookup",
            "tools_used": ["ConversationMemory", "Groq"],
            "context": "Conversation history",
            "answer": "We discussed Atlas Agent.",
        }

        with patch("app.routes.agent.run_agent", return_value=mocked_response) as run_agent:
            response = self.client.post(
                "/agent/chat",
                json={
                    "question": "What did we discuss?",
                    "conversation_id": 42,
                },
            )

        self.assertEqual(response.status_code, 200)
        run_agent.assert_called_once_with(
            question="What did we discuss?",
            session=ANY,
            conversation_id=42,
        )

    def test_agent_chat_handles_groq_configuration_error(self):
        with patch(
            "app.routes.agent.run_agent",
            side_effect=GroqConfigurationError("missing key"),
        ):
            response = self.client.post(
                "/agent/chat",
                json={"question": "What is AI Engineering?"},
            )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"detail": "Groq configuration error"})

    def test_agent_chat_handles_groq_service_error(self):
        with patch(
            "app.routes.agent.run_agent",
            side_effect=GroqServiceError("service down"),
        ):
            response = self.client.post(
                "/agent/chat",
                json={"question": "What is AI Engineering?"},
            )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"detail": "Groq service unavailable"})


if __name__ == "__main__":
    unittest.main()
