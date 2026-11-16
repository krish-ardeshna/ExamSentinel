"""Database engine, session, and base model for SQLAlchemy 2.x."""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def get_db_url():
    return os.environ.get("DATABASE_URL") or get_settings().DATABASE_URL


def create_app_engine():
    url = get_db_url()
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    try:
        eng = create_engine(url, echo=False)
        with eng.connect():
            pass
        return eng
    except Exception as e:
        # Fallback to local SQLite if postgres server is not running or unreachable
        return create_engine("sqlite:///./oepms_fallback.db", connect_args={"check_same_thread": False})


engine = create_app_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
