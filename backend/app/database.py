# Import SQLModel and create_engine.
from sqlmodel import SQLModel, create_engine

# SQLite database file.
DATABASE_URL = "sqlite:///atlas.db"

# Create the database engine.
engine = create_engine(DATABASE_URL)


# Create all database tables.
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)