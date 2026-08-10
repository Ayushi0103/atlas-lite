import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import SessionDep
from app.services.atlas_agent import run_agent
from app.services.auth import CurrentUser
from app.services.groq_client import GroqConfigurationError, GroqServiceError


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])


class AgentChatRequest(BaseModel):
    question: str
    conversation_id: int | None = None


@router.post("/chat")
def chat_with_agent(request: AgentChatRequest, session: SessionDep, current_user: CurrentUser):
    try:
        return run_agent(
            question=request.question,
            session=session,
            user_id=current_user.id,  # type: ignore[arg-type]
            conversation_id=request.conversation_id,
        )
    except GroqConfigurationError as exc:
        raise HTTPException(
            status_code=500,
            detail="Groq configuration error",
        ) from exc
    except GroqServiceError as exc:
        raise HTTPException(
            status_code=500,
            detail="Groq service unavailable",
        ) from exc
    except Exception as exc:
        logger.exception("Atlas Agent failed")
        raise HTTPException(status_code=500, detail="Atlas Agent failed") from exc
