import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlmodel import Session, SQLModel, create_engine, select


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR / "backend"))

from app.models import Conversation, Message  # noqa: E402
from app.routes.ai import ChatRequest, chat_ai  # noqa: E402
from app.routes.conversations import delete_conversation  # noqa: E402
from app.services.rag import RAGResponse, RAGSource  # noqa: E402


class ConversationMemoryTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
        )
        SQLModel.metadata.create_all(self.engine)

    def get_session(self):
        return Session(self.engine)

    def fake_rag_response(self, answer: str = "Assistant answer") -> RAGResponse:
        return RAGResponse(
            answer=answer,
            sources=[RAGSource(type="note", id=1, title="Test note")],
        )

    def test_chat_creates_conversation_and_stores_messages(self):
        calls = []

        def answer_question(question, history=None):
            calls.append((question, history or []))
            return self.fake_rag_response()

        with self.get_session() as session:
            with patch("app.routes.ai.answer_question", side_effect=answer_question):
                response = chat_ai(
                    ChatRequest(question="What should Atlas remember?"),
                    session,
                )

            self.assertEqual(response.conversation_id, 1)
            self.assertEqual(response.answer, "Assistant answer")
            self.assertEqual(calls, [("What should Atlas remember?", [])])

            conversation = session.get(Conversation, response.conversation_id)
            self.assertIsNotNone(conversation)
            self.assertEqual(conversation.title, "What should Atlas remember?")

            messages = session.exec(select(Message).order_by(Message.id)).all()
            self.assertEqual(
                [(message.role, message.content) for message in messages],
                [
                    ("user", "What should Atlas remember?"),
                    ("assistant", "Assistant answer"),
                ],
            )

    def test_chat_includes_recent_history_and_cascades_delete(self):
        calls = []

        def answer_question(question, history=None):
            calls.append((question, history or []))
            return self.fake_rag_response(answer=f"Answer to {question}")

        with self.get_session() as session:
            with patch("app.routes.ai.answer_question", side_effect=answer_question):
                response = chat_ai(ChatRequest(question="Question 1"), session)
                conversation_id = response.conversation_id

                for index in range(2, 7):
                    chat_ai(
                        ChatRequest(
                            conversation_id=conversation_id,
                            question=f"Question {index}",
                        ),
                        session,
                    )

            last_history = calls[-1][1]
            self.assertEqual(len(last_history), 8)
            self.assertEqual(last_history[0], {"role": "user", "content": "Question 2"})
            self.assertEqual(
                last_history[-1],
                {"role": "assistant", "content": "Answer to Question 5"},
            )

            delete_conversation(conversation_id, session)

            self.assertIsNone(session.get(Conversation, conversation_id))
            self.assertEqual(session.exec(select(Message)).all(), [])


if __name__ == "__main__":
    unittest.main()
