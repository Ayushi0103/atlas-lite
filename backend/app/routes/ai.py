import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.rag import (
    LLMUnavailableError,
    NoRelevantContextError,
    RAGResponse,
    answer_question,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])


class AskRequest(BaseModel):
    question: str = Field(min_length=1)


@router.post("/ask", response_model=RAGResponse)
def ask_ai(request: AskRequest) -> RAGResponse:
    try:
        return answer_question(request.question)
    except NoRelevantContextError as exc:
        raise HTTPException(
            status_code=404,
            detail="I couldn't find anything relevant in your knowledge base.",
        ) from exc
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=503, detail="LLM service unavailable.") from exc
    except Exception as exc:
        logger.exception("Unexpected error while answering AI question")
        raise HTTPException(status_code=500, detail="Could not answer question.") from exc
