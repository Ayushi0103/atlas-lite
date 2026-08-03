import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException
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
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])


class ChatRequest(BaseModel):
    conversation_id: int | None = None
    question: str = Field(min_length=1)


class ChatResponse(RAGResponse):
    conversation_id: int


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


@router.post("/chat", response_model=ChatResponse)
def chat_ai(request: ChatRequest, session: SessionDep) -> ChatResponse:
    cleaned_question = request.question.strip()
    conversation = None

    try:
        if not cleaned_question:
            raise HTTPException(status_code=400, detail="Question cannot be empty")

        if request.conversation_id is None:
            conversation = Conversation(
                title=generate_conversation_title(cleaned_question),
            )
            session.add(conversation)
            session.flush()
            logger.info("Created AI conversation %s", conversation.id)
        else:
            conversation = session.get(Conversation, request.conversation_id)
            if conversation is None:
                raise HTTPException(status_code=404, detail="Conversation not found")

            if not _conversation_has_messages(session, request.conversation_id):
                conversation.title = generate_conversation_title(cleaned_question)

        if conversation.id is None:
            raise RuntimeError("Conversation ID was not created")

        history = _get_recent_messages(session, conversation.id)
        rag_response = answer_question(cleaned_question, history)

        session.add(
            Message(
                conversation_id=conversation.id,
                role="user",
                content=cleaned_question,
            )
        )
        session.add(
            Message(
                conversation_id=conversation.id,
                role="assistant",
                content=rag_response.answer,
            )
        )
        conversation.updated_at = datetime.now()
        session.add(conversation)
        session.commit()

        return ChatResponse(
            conversation_id=conversation.id,
            answer=rag_response.answer,
            sources=rag_response.sources,
        )
    except HTTPException:
        session.rollback()
        raise
    except NoRelevantContextError as exc:
        session.rollback()
        raise HTTPException(
            status_code=404,
            detail="I couldn't find anything relevant in your knowledge base.",
        ) from exc
    except LLMUnavailableError as exc:
        session.rollback()
        raise HTTPException(status_code=503, detail="LLM service unavailable.") from exc
    except Exception as exc:
        session.rollback()
        logger.exception("Unexpected error while answering AI question")
        raise HTTPException(status_code=500, detail="Could not answer question.") from exc
