from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from shutil import copyfileobj
from typing import Annotated
from uuid import uuid4

from docx import Document as DocxDocument
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from pypdf import PdfReader
from sqlmodel import Session, select, or_

from app.database import create_db_and_tables, engine
from app.models import Collection, CollectionNote, Document, Note


ROOT_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = ROOT_DIR / "uploads"
SUPPORTED_DOCUMENT_TYPES = {"txt", "pdf", "docx", "md"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
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


def get_document_file_type(filename: str) -> str:
    file_type = Path(filename).suffix.lower().lstrip(".")
    if file_type not in SUPPORTED_DOCUMENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Upload a TXT, MD, PDF, or DOCX file.",
        )

    return file_type


def save_upload_file(upload_file: UploadFile) -> Path:
    safe_filename = Path(upload_file.filename or "").name
    if not safe_filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    saved_filename = f"{uuid4().hex}_{safe_filename}"
    destination = UPLOAD_DIR / saved_filename

    with destination.open("wb") as buffer:
        copyfileobj(upload_file.file, buffer)

    return destination


def extract_text_from_document(file_path: Path, file_type: str) -> str:
    if file_type in {"txt", "md"}:
        return file_path.read_text(encoding="utf-8", errors="replace")

    if file_type == "pdf":
        reader = PdfReader(str(file_path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if file_type == "docx":
        doc = DocxDocument(str(file_path))
        return "\n".join(paragraph.text for paragraph in doc.paragraphs)

    raise HTTPException(status_code=400, detail="Unsupported file type")


@app.get("/")
def read_root():
    return {"message": "Welcome to Atlas Lite"}


@app.post("/notes")
def save_note(note: NoteCreate, session: SessionDep):
    new_note = Note(title=note.title, content=note.content, tags=note.tags)
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
def search_notes(q: str, session: SessionDep):
    q = q.strip()

    if not q:
        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty",
        )

    statement = select(Note).where(
        or_(
            Note.title.contains(q),
            Note.content.contains(q),
            Note.tags.contains(q),
        )
    )

    return session.exec(statement).all()


@app.get("/notes/{note_id}")
def get_note(note_id: int, session: SessionDep):
    note = session.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")

    return note


@app.post("/documents", status_code=status.HTTP_201_CREATED)
def upload_document(session: SessionDep, file: UploadFile = File(...)):
    if file.filename is None:
        raise HTTPException(status_code=400, detail="Filename is required")

    file_type = get_document_file_type(file.filename)
    saved_path = save_upload_file(file)

    try:
        text_content = extract_text_from_document(saved_path, file_type)
    except Exception as exc:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400, detail=f"Could not extract text from document: {exc}"
        ) from exc

    document = Document(
        filename=Path(file.filename).name,
        file_type=file_type,
        file_path=str(saved_path.relative_to(ROOT_DIR)),
        text_content=text_content,
    )
    session.add(document)
    session.commit()
    session.refresh(document)

    return {
        "status": "saved",
        "document": document,
    }


@app.get("/documents")
def get_documents(session: SessionDep):
    statement = select(Document).order_by(Document.created_at.desc())
    return session.exec(statement).all()


@app.get("/documents/search")
def search_documents(q: str, session: SessionDep):
    q = q.strip()

    if not q:
        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty",
        )

    statement = select(Document).where(
        or_(
            Document.filename.contains(q),
            Document.text_content.contains(q),
        )
    )

    return session.exec(statement).all()


@app.get("/documents/{document_id}")
def get_document(document_id: int, session: SessionDep):
    document = session.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    return document


@app.delete("/documents/{document_id}")
def delete_document(document_id: int, session: SessionDep):
    document = session.get(Document, document_id)

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = ROOT_DIR / document.file_path

    if file_path.exists():
        file_path.unlink()

    session.delete(document)
    session.commit()

    return {
        "status": "deleted",
        "message": "Document deleted successfully",
    }


@app.put("/notes/{note_id}")
def update_note(note_id: int, updated_note: NoteCreate, session: SessionDep):
    note = session.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")

    note.title = updated_note.title
    note.content = updated_note.content
    note.tags = updated_note.tags
    note.updated_at = datetime.now()
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
