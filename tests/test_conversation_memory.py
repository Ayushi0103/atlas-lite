import sys
import unittest
import asyncio
from pathlib import Path
from unittest.mock import patch

from sqlmodel import Session, SQLModel, create_engine, select


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR / "backend"))

from app.models import Conversation, Message  # noqa: E402
from app.routes.ai import ChatRequest, chat_ai  # noqa: E402
from app.routes.conversations import delete_conversation  # noqa: E402
from app.services.rag import RAGContext, RAGResponse, RAGSource  # noqa: E402


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

    def fake_rag_context(self, question: str) -> RAGContext:
        return RAGContext(
            question=question,
            context="Test context",
            sources=[RAGSource(type="note", id=1, title="Test note")],
            retrieved_document_count=1,
        )

    def collect_stream(self, response):
        async def collect():
            chunks = []
            async for chunk in response.body_iterator:
                chunks.append(chunk.decode() if isinstance(chunk, bytes) else chunk)
            return "".join(chunks)

        return asyncio.run(collect())

    def test_chat_creates_conversation_and_stores_messages(self):
        calls = []

        def stream_answer(rag_context, history=None):
            calls.append((rag_context.question, history or []))
            yield "Assistant "
            yield "answer"
            return rag_context.sources

        with self.get_session() as session:
            with patch("app.routes.ai.prepare_rag_context", side_effect=self.fake_rag_context):
                with patch("app.routes.ai.stream_answer_from_context", side_effect=stream_answer):
                    response = chat_ai(
                        ChatRequest(question="What should Atlas remember?"),
                        session,
                    )
                    body = self.collect_stream(response)

            self.assertIn('event: token\ndata: {"text": "Assistant "}', body)
            self.assertIn('event: done', body)
            self.assertEqual(calls, [("What should Atlas remember?", [])])

            messages = session.exec(select(Message).order_by(Message.id)).all()
            response_conversation_id = messages[0].conversation_id
            self.assertEqual(response_conversation_id, 1)

            conversation = session.get(Conversation, response_conversation_id)
            self.assertIsNotNone(conversation)
            self.assertEqual(conversation.title, "What should Atlas remember?")

            self.assertEqual(
                [(message.role, message.content) for message in messages],
                [
                    ("user", "What should Atlas remember?"),
                    ("assistant", "Assistant answer"),
                ],
            )

    def test_ask_returns_non_streaming_answer(self):
        def answer_question(question, history=None):
            self.assertEqual(question, "What should Atlas remember?")
            self.assertIsNone(history)
            return self.fake_rag_response()

        from app.routes.ai import AskRequest, ask_ai

        with patch("app.routes.ai.answer_question", side_effect=answer_question):
            response = ask_ai(AskRequest(question="What should Atlas remember?"))

        self.assertEqual(response.answer, "Assistant answer")

    def test_chat_includes_recent_history_and_cascades_delete(self):
        calls = []

        def stream_answer(rag_context, history=None):
            calls.append((rag_context.question, history or []))
            yield f"Answer to {rag_context.question}"
            return rag_context.sources

        with self.get_session() as session:
            with patch("app.routes.ai.prepare_rag_context", side_effect=self.fake_rag_context):
                with patch("app.routes.ai.stream_answer_from_context", side_effect=stream_answer):
                    response = chat_ai(ChatRequest(question="Question 1"), session)
                    self.collect_stream(response)
                    conversation_id = session.exec(select(Conversation.id)).one()

                    for index in range(2, 7):
                        response = chat_ai(
                            ChatRequest(
                                conversation_id=conversation_id,
                                question=f"Question {index}",
                            ),
                            session,
                        )
                        self.collect_stream(response)

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

    def test_chat_does_not_persist_partial_cancelled_stream(self):
        def stream_answer(rag_context, history=None):
            yield "Partial answer"
            raise GeneratorExit

        with self.get_session() as session:
            with patch("app.routes.ai.prepare_rag_context", side_effect=self.fake_rag_context):
                with patch("app.routes.ai.stream_answer_from_context", side_effect=stream_answer):
                    response = chat_ai(
                        ChatRequest(question="What should Atlas remember?"),
                        session,
                    )
                    iterator = response.body_iterator

                    async def consume_one():
                        await iterator.__anext__()
                        await iterator.aclose()

                    asyncio.run(consume_one())

            self.assertEqual(session.exec(select(Message)).all(), [])


if __name__ == "__main__":
    unittest.main()
