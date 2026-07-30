from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select, or_

from app.database import create_db_and_tables, engine
from app.models import Note


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
        Note.content.contains(q)
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
