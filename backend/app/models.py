from datetime import datetime

# Import SQLModel, Field, and Relationship.
from sqlmodel import SQLModel, Field, Relationship


class CollectionNote(SQLModel, table=True):
    __tablename__ = "collection_note"

    collection_id: int | None = Field(
        default=None, foreign_key="collection.id", primary_key=True
    )
    note_id: int | None = Field(default=None, foreign_key="note.id", primary_key=True)


# Define the Note table.
class Note(SQLModel, table=True):
    # Primary key for each note.
    id: int | None = Field(default=None, primary_key=True)

    # Note title.
    title: str

    # Note content.
    content: str

    # Note tags.
    tags: str = Field(default="")

    created_at: datetime = Field(default_factory=datetime.now)

    updated_at: datetime = Field(default_factory=datetime.now)

    collections: list["Collection"] = Relationship(
        back_populates="notes", link_model=CollectionNote
    )


class Collection(SQLModel, table=True):
    # Primary key for each collection.
    id: int | None = Field(default=None, primary_key=True)

    # Collection name.
    name: str

    # Optional collection description.
    description: str | None = None

    created_at: datetime = Field(default_factory=datetime.now)

    updated_at: datetime = Field(default_factory=datetime.now)

    notes: list[Note] = Relationship(
        back_populates="collections", link_model=CollectionNote
    )
