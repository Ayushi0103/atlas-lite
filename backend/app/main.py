from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select, or_

from app.database import create_db_and_tables, engine
from app.models import Collection, CollectionNote, Note


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


class NoteCreate(BaseModel):
    title: str
    content: str
    tags: str


class CollectionCreate(BaseModel):
    name: str
    description: str | None = None


@app.get("/")
def read_root():
    return {"message": "Welcome to Atlas Lite"}


@app.post("/notes")
def save_note(note: NoteCreate, session: SessionDep):
    new_note = Note(title=note.title, content=note.content, tags=note.tags,)
    session.add(new_note)
    session.commit()
    session.refresh(new_note)

    return {
        "status": "saved",
        "note": new_note,
    }


@app.get("/notes")
def get_notes(session: SessionDep):
    return session.exec(select(Note)).all()


# Register a GET endpoint for searching notes.
@app.get("/notes/search")
# Define the function that runs when a user searches for notes.
def search_notes(q: str, session: SessionDep):
    statement = select(Note).where(
    or_(
        Note.title.contains(q),
        Note.content.contains(q),
        Note.tags.contains(q),
    )
)

    results = session.exec(statement).all()

    return results


@app.get("/notes/{note_id}")
def get_note(note_id: int, session: SessionDep):
    note = session.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")

    return note


@app.put("/notes/{note_id}")
def update_note(note_id: int, updated_note: NoteCreate, session: SessionDep):
    note = session.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")

    note.title = updated_note.title
    note.content = updated_note.content
    note.tags = updated_note.tags
    session.add(note)
    session.commit()
    session.refresh(note)

    return {
        "status": "updated",
        "note": note,
    }


@app.delete("/notes/{note_id}")
def delete_note(note_id: int, session: SessionDep):
    note = session.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")

    session.delete(note)
    session.commit()

    return {
        "status": "deleted",
        "message": "Note deleted successfully",
    }


@app.post("/collections")
def create_collection(collection: CollectionCreate, session: SessionDep):
    new_collection = Collection(
        name=collection.name,
        description=collection.description,
    )
    session.add(new_collection)
    session.commit()
    session.refresh(new_collection)

    return {
        "status": "saved",
        "collection": new_collection,
    }


@app.get("/collections")
def get_collections(session: SessionDep):
    return session.exec(select(Collection)).all()


@app.get("/collections/{collection_id}")
def get_collection(collection_id: int, session: SessionDep):
    collection = session.get(Collection, collection_id)
    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    return collection


@app.put("/collections/{collection_id}")
def update_collection(
    collection_id: int, updated_collection: CollectionCreate, session: SessionDep
):
    collection = session.get(Collection, collection_id)
    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    collection.name = updated_collection.name
    collection.description = updated_collection.description
    collection.updated_at = datetime.now()
    session.add(collection)
    session.commit()
    session.refresh(collection)

    return {
        "status": "updated",
        "collection": collection,
    }


@app.delete("/collections/{collection_id}")
def delete_collection(collection_id: int, session: SessionDep):
    collection = session.get(Collection, collection_id)
    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    session.delete(collection)
    session.commit()

    return {
        "status": "deleted",
        "message": "Collection deleted successfully",
    }


@app.post("/collections/{collection_id}/notes/{note_id}")
def attach_note_to_collection(collection_id: int, note_id: int, session: SessionDep):
    collection = session.get(Collection, collection_id)
    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    note = session.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")

    existing_link = session.exec(
        select(CollectionNote).where(
            CollectionNote.collection_id == collection_id,
            CollectionNote.note_id == note_id,
        )
    ).first()
    if existing_link is not None:
        return {
            "status": "attached",
            "message": "Note already belongs to collection",
        }

    collection_note = CollectionNote(collection_id=collection_id, note_id=note_id)
    session.add(collection_note)
    session.commit()

    return {
        "status": "attached",
        "message": "Note attached to collection successfully",
    }


@app.delete("/collections/{collection_id}/notes/{note_id}")
def detach_note_from_collection(collection_id: int, note_id: int, session: SessionDep):
    collection = session.get(Collection, collection_id)
    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    note = session.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")

    collection_note = session.exec(
        select(CollectionNote).where(
            CollectionNote.collection_id == collection_id,
            CollectionNote.note_id == note_id,
        )
    ).first()
    if collection_note is None:
        raise HTTPException(status_code=404, detail="Note is not in collection")

    session.delete(collection_note)
    session.commit()

    return {
        "status": "detached",
        "message": "Note detached from collection successfully",
    }


@app.get("/collections/{collection_id}/notes")
def get_collection_notes(collection_id: int, session: SessionDep):
    collection = session.get(Collection, collection_id)
    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    statement = (
        select(Note)
        .join(CollectionNote, CollectionNote.note_id == Note.id)
        .where(CollectionNote.collection_id == collection_id)
    )

    return session.exec(statement).all()
