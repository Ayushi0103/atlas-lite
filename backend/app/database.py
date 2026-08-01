from pathlib import Path
from sqlmodel import SQLModel, create_engine

# Project root (Atlas Lite/)
ROOT_DIR = Path(__file__).resolve().parents[2]

DATABASE_PATH = ROOT_DIR / "atlas.db"

DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

engine = create_engine(DATABASE_URL)

print("DATABASE FILE:", DATABASE_PATH)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)