from fastapi import APIRouter, HTTPException

from app.database import SessionDep
from app.services.auth import CurrentUser
from app.services.knowledge_graph import get_related_concepts


router = APIRouter(prefix="/knowledge-graph", tags=["knowledge-graph"])


@router.get("")
def read_knowledge_graph(q: str, session: SessionDep, current_user: CurrentUser):
    concept = q.strip()
    if not concept:
        raise HTTPException(status_code=400, detail="Concept query cannot be empty")

    return get_related_concepts(concept, session, current_user.id)
