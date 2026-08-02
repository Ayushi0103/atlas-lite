from pydantic import BaseModel, Field
from fastapi import APIRouter

from app.services.embedding import semantic_search


router = APIRouter(prefix="/search", tags=["search"])


class SemanticSearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=50)


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
def search_semantic(request: SemanticSearchRequest) -> SemanticSearchResponse:
    results = semantic_search(request.query, request.top_k)
    return SemanticSearchResponse(results=results)
