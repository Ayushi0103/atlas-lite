from datetime import datetime
import logging

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import select

from app.database import SessionDep
from app.models import Conversation, Message


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["conversations"])

TITLE_MAX_LENGTH = 50


class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, min_length=1)


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationDetail(ConversationRead):
    messages: list[MessageRead]


def generate_conversation_title(message: str) -> str:
    title = " ".join(message.strip().split())
    if not title:
        return "New conversation"

    if len(title) <= TITLE_MAX_LENGTH:
        return title

    return title[:TITLE_MAX_LENGTH].rstrip() + "..."


@router.post(
    "",
    response_model=ConversationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    session: SessionDep,
    request: ConversationCreate | None = None,
) -> Conversation:
    title = request.title.strip() if request and request.title else "New conversation"
    conversation = Conversation(title=title)

    try:
        session.add(conversation)
        session.commit()
        session.refresh(conversation)
    except Exception as exc:
        session.rollback()
        logger.exception("Failed to create conversation")
        raise HTTPException(
            status_code=500,
            detail="Could not create conversation.",
        ) from exc

    return conversation


@router.get("", response_model=list[ConversationRead])
def get_conversations(session: SessionDep) -> list[Conversation]:
    statement = select(Conversation).order_by(Conversation.updated_at.desc())
    return list(session.exec(statement).all())


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(conversation_id: int, session: SessionDep) -> ConversationDetail:
    conversation = session.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    statement = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc(), Message.id.asc())
    )
    messages = list(session.exec(statement).all())

    return ConversationDetail(
        id=conversation.id,  # type: ignore[arg-type]
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=messages,
    )


@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: int, session: SessionDep):
    conversation = session.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    try:
        session.delete(conversation)
        session.commit()
    except Exception as exc:
        session.rollback()
        logger.exception("Failed to delete conversation %s", conversation_id)
        raise HTTPException(
            status_code=500,
            detail="Could not delete conversation.",
        ) from exc

    return {
        "status": "deleted",
        "message": "Conversation deleted successfully",
    }
