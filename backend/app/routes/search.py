from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.database import SessionDep
from app.services.auth import CurrentUser
from app.services.embedding import semantic_search
from app.services.search_filters import apply_filters


router = APIRouter(prefix="/search", tags=["search"])


class SemanticSearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=50)
    scope: Literal["all", "documents", "notes"] = "all"
    file_type: str | None = None
    since: Literal["all", "today", "week", "month"] = "all"


class SemanticSearchResult(BaseModel):
    type: str
    id: int
    filename: str | None = None
    title: str | None = None
    score: float
    text: str


class SemanticSearchResponse(BaseModel):
    results: list[SemanticSearchResult]


@router.post(
    "/semantic",
    response_model=SemanticSearchResponse,
    response_model_exclude_none=True,
)
def search_semantic(
    request: SemanticSearchRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> SemanticSearchResponse:
    # Overfetch before filtering so we still have top_k results left after
    # scope / file type / recency filters are applied.
    overfetch = max(request.top_k * 4, request.top_k)
    raw_results = semantic_search(request.query, current_user.id, overfetch)

    filtered = apply_filters(
        raw_results,
        session,
        scope=request.scope,
        file_type=request.file_type,
        since=request.since,
    )

    return SemanticSearchResponse(results=filtered[: request.top_k])
