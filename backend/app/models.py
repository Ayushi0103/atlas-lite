from datetime import datetime

# Import SQLModel, Field, and Relationship.
from sqlalchemy import Column, String, Text, UniqueConstraint
from sqlmodel import SQLModel, Field, Relationship


class CollectionNote(SQLModel, table=True):
    __tablename__ = "collection_note"

    collection_id: int | None = Field(
        default=None,
        foreign_key="collection.id",
        primary_key=True,
        ondelete="CASCADE",
    )
    note_id: int | None = Field(
        default=None,
        foreign_key="note.id",
        primary_key=True,
        ondelete="CASCADE",
    )


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


class Document(SQLModel, table=True):
    # Primary key for each uploaded document.
    id: int | None = Field(default=None, primary_key=True)

    # Original filename provided at upload time.
    filename: str

    # Normalized file extension for uploaded documents and supported images.
    file_type: str

    # Path to the saved upload on disk.
    file_path: str

    # Original source URL for imported external documents.
    source_url: str | None = Field(default=None, unique=True)

    # Extracted document text.
    text_content: str = Field(sa_column=Column(Text, nullable=False))

    # AI-generated summary metadata.
    short_summary: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )

    detailed_summary: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )

    # JSON-encoded lists.
    key_concepts: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )

    keywords: str | None = Field(default=None, sa_column=Column(Text, nullable=True))

    suggested_questions: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )

    created_at: datetime = Field(default_factory=datetime.now)

    updated_at: datetime = Field(default_factory=datetime.now)


class KnowledgeGraphNode(SQLModel, table=True):
    __tablename__ = "knowledge_graph_node"
    __table_args__ = (
        UniqueConstraint("name", "type", name="uq_knowledge_graph_node_name_type"),
    )

    id: int | None = Field(default=None, primary_key=True)

    name: str = Field(sa_column=Column(String(collation="NOCASE"), nullable=False))

    type: str = Field(sa_column=Column(String(collation="NOCASE"), nullable=False))

    created_at: datetime = Field(default_factory=datetime.now)


class KnowledgeGraphEdge(SQLModel, table=True):
    __tablename__ = "knowledge_graph_edge"
    __table_args__ = (
        UniqueConstraint(
            "source_node_id",
            "target_node_id",
            "relationship",
            name="uq_knowledge_graph_edge_relationship",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)

    source_node_id: int = Field(
        foreign_key="knowledge_graph_node.id",
        index=True,
        ondelete="CASCADE",
    )

    target_node_id: int = Field(
        foreign_key="knowledge_graph_node.id",
        index=True,
        ondelete="CASCADE",
    )

    relationship: str = Field(sa_column=Column(String(collation="NOCASE"), nullable=False))

    created_at: datetime = Field(default_factory=datetime.now)


class Conversation(SQLModel, table=True):
    # Primary key for each AI conversation.
    id: int | None = Field(default=None, primary_key=True)

    # Human-readable conversation title.
    title: str

    created_at: datetime = Field(default_factory=datetime.now)

    updated_at: datetime = Field(default_factory=datetime.now)

    messages: list["Message"] = Relationship(
        back_populates="conversation",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class Message(SQLModel, table=True):
    # Primary key for each chat message.
    id: int | None = Field(default=None, primary_key=True)

    conversation_id: int = Field(
        foreign_key="conversation.id",
        index=True,
        ondelete="CASCADE",
    )

    # Message author role: user or assistant.
    role: str

    content: str = Field(sa_column=Column(Text, nullable=False))

    created_at: datetime = Field(default_factory=datetime.now)

    conversation: Conversation = Relationship(back_populates="messages")
