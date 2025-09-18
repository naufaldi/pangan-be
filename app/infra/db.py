from __future__ import annotations

from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from app.common.settings import get_settings


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all ORM models."""


def _build_engine_url() -> str:
    settings = get_settings()
    if not settings.DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")
    return settings.DATABASE_URL


def get_engine():
    return create_engine(_build_engine_url(), pool_pre_ping=True, future=True)


SessionLocal = sessionmaker(
    class_=Session,
    autoflush=False,
    autocommit=False,
    bind=None,
    future=True,
)


def get_db_session() -> Iterator[Session]:
    """FastAPI dependency to provide a DB session per-request."""
    engine = get_engine()
    SessionLocal.configure(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
