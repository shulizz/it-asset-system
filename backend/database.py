from sqlalchemy import create_engine, text
import os
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = os.getenv("IT_ASSET_DATABASE_URL", "sqlite:///./it_assets.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False, "timeout": 30}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_write_db():
    """Serialize SQLite mutations before reading state, including approval races."""
    db = SessionLocal()
    try:
        db.execute(text("BEGIN IMMEDIATE"))
        yield db
    finally:
        db.rollback()
        db.close()
