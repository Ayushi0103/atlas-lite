from pathlib import Path
from typing import Annotated

from fastapi import Depends
from sqlmodel import SQLModel, Session, create_engine

# Project root (Atlas Lite/)
ROOT_DIR = Path(__file__).resolve().parents[2]

DATABASE_PATH = ROOT_DIR / "atlas.db"

DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

print("DATABASE FILE:", DATABASE_PATH)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
