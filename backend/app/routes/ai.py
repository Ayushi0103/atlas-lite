import logging
import json
import time
from collections.abc import Generator
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlmodel import select

from app.database import SessionDep
from app.models import Conversation, Message
from app.routes.conversations import generate_conversation_title
from app.services.rag import (
    LLMUnavailableError,
    NoRelevantContextError,
    RAGResponse,
    answer_question,
    prepare_rag_context,
    stream_answer_from_context,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])


class ChatRequest(BaseModel):
    conversation_id: int | None = None
    question: str = Field(min_length=1)


class AskRequest(BaseModel):
    question: str = Field(min_length=1)


def _get_recent_messages(
    session: SessionDep,
    conversation_id: int,
    limit: int = 8,
) -> list[dict[str, str]]:
    statement = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(limit)
    )
    messages = list(session.exec(statement).all())
    messages.reverse()

    return [
        {
            "role": message.role,
            "content": message.content,
        }
        for message in messages
    ]


def _conversation_has_messages(session: SessionDep, conversation_id: int) -> bool:
    statement = (
        select(Message.id)
        .where(Message.conversation_id == conversation_id)
        .limit(1)
    )
    return session.exec(statement).first() is not None


def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _persist_conversation_messages(
    session: SessionDep,
    conversation: Conversation,
    question: str,
    answer: str,
) -> tuple[int | None, int | None]:
    conversation_id = conversation.id
    user_message = Message(
        conversation_id=conversation_id,  # type: ignore[arg-type]
        role="user",
        content=question,
    )
    assistant_message = Message(
        conversation_id=conversation_id,  # type: ignore[arg-type]
        role="assistant",
        content=answer,
    )
    session.add(user_message)
    session.add(assistant_message)
    conversation.updated_at = datetime.now()
    session.add(conversation)
    session.flush()
    user_message_id = user_message.id
    assistant_message_id = assistant_message.id
    session.commit()

    return user_message_id, assistant_message_id


def _get_or_create_conversation(
    request: ChatRequest,
    cleaned_question: str,
    session: SessionDep,
) -> Conversation:
    if request.conversation_id is None:
        conversation = Conversation(
            title=generate_conversation_title(cleaned_question),
        )
        session.add(conversation)
        session.flush()
        logger.info("Created AI conversation %s", conversation.id)
        return conversation

    conversation = session.get(Conversation, request.conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if not _conversation_has_messages(session, request.conversation_id):
        conversation.title = generate_conversation_title(cleaned_question)

    return conversation


def _handle_ai_error(exc: Exception) -> HTTPException:
    if isinstance(exc, NoRelevantContextError):
        return HTTPException(
            status_code=404,
            detail="I couldn't find anything relevant in your knowledge base.",
        )

    if isinstance(exc, LLMUnavailableError):
        return HTTPException(status_code=503, detail="LLM service unavailable.")

    logger.exception("Unexpected error while answering AI question")
    return HTTPException(status_code=500, detail="Could not answer question.")


@router.post("/ask", response_model=RAGResponse)
def ask_ai(request: AskRequest) -> RAGResponse:
    cleaned_question = request.question.strip()
    if not cleaned_question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        return answer_question(cleaned_question)
    except (NoRelevantContextError, LLMUnavailableError) as exc:
        raise _handle_ai_error(exc) from exc
    except Exception as exc:
        raise _handle_ai_error(exc) from exc


@router.post("/chat")
def chat_ai(request: ChatRequest, session: SessionDep) -> StreamingResponse:
    cleaned_question = request.question.strip()

    try:
        if not cleaned_question:
            raise HTTPException(status_code=400, detail="Question cannot be empty")

        conversation = _get_or_create_conversation(request, cleaned_question, session)

        if conversation.id is None:
            raise RuntimeError("Conversation ID was not created")

        history = _get_recent_messages(session, conversation.id)
        rag_context = prepare_rag_context(cleaned_question)
        logger.info(
            "Conversation %s retrieved document count: %s",
            conversation.id,
            rag_context.retrieved_document_count,
        )
        response_stream = stream_answer_from_context(rag_context, history)
        logger.info(
            "Starting AI stream for conversation %s with %s history messages",
            conversation.id,
            len(history),
        )

        return StreamingResponse(
            _stream_chat_response(
                session=session,
                conversation=conversation,
                question=cleaned_question,
                response_stream=response_stream,
            ),
            media_type="text/event-stream",
        )
    except HTTPException:
        session.rollback()
        raise
    except (NoRelevantContextError, LLMUnavailableError) as exc:
        session.rollback()
        raise _handle_ai_error(exc) from exc
    except Exception as exc:
        session.rollback()
        raise _handle_ai_error(exc) from exc


def _stream_chat_response(
    *,
    session: SessionDep,
    conversation: Conversation,
    question: str,
    response_stream: Generator[str, None, list],
) -> Generator[str, None, None]:
    started_at = time.perf_counter()
    answer_chunks: list[str] = []
    conversation_id = conversation.id

    logger.info("AI stream started for conversation %s", conversation_id)
    yield _sse_event("meta", {"conversation_id": conversation_id})

    try:
        sources = []
        while True:
            try:
                chunk = next(response_stream)
            except StopIteration as stop:
                sources = stop.value or []
                break

            answer_chunks.append(chunk)
            yield _sse_event("token", {"text": chunk})

        answer = "".join(answer_chunks).strip()
        user_message_id, assistant_message_id = _persist_conversation_messages(
            session,
            conversation,
            question,
            answer,
        )
        elapsed_ms = (time.perf_counter() - started_at) * 1000
        source_payload = [
            source.model_dump() if hasattr(source, "model_dump") else source
            for source in sources
        ]

        logger.info(
            (
                "AI stream completed for conversation %s in %.2f ms; "
                "saved message ids user=%s assistant=%s"
            ),
            conversation_id,
            elapsed_ms,
            user_message_id,
            assistant_message_id,
        )
        yield _sse_event(
            "done",
            {
                "conversation_id": conversation_id,
                "sources": source_payload,
            },
        )
    except GeneratorExit:
        session.rollback()
        logger.info("AI stream cancelled for conversation %s", conversation_id)
        raise
    except LLMUnavailableError:
        session.rollback()
        logger.exception("LLM unavailable during AI stream")
        yield _sse_event("error", {"detail": "LLM service unavailable."})
    except Exception:
        session.rollback()
        logger.exception("Unexpected error during AI stream")
        yield _sse_event("error", {"detail": "Could not answer question."})
