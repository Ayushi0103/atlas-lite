# Import SQLModel and Field.
from sqlmodel import SQLModel, Field


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