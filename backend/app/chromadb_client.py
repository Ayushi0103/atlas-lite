from typing import Any

from app.database import ROOT_DIR


CHROMA_DIR = ROOT_DIR / "chroma_db"
COLLECTION_NAME = "atlas_semantic_search"


def get_chroma_collection() -> Any:
    import chromadb
    from chromadb.config import Settings

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False),
    )
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
