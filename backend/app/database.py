"""SQLite connection, schema creation, and demo seed."""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.models.entities import Base
from app.services.seed import seed_if_empty

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data"

engine: Engine | None = None
SessionLocal: sessionmaker[Session] | None = None


def database_url() -> str:
    configured = os.getenv("DATABASE_URL")
    if configured:
        return configured
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db_path = (DATA_DIR / "monitoring.db").resolve().as_posix()
    return f"sqlite:///{db_path}"


def configure() -> Engine:
    global engine, SessionLocal
    if engine is not None and SessionLocal is not None:
        return engine
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        database_url(),
        connect_args={"check_same_thread": False, "timeout": 30},
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=True, autocommit=False)
    return engine


def reset_connection() -> None:
    """Drop the cached engine so tests can point at a fresh database."""
    global engine, SessionLocal
    if engine is not None:
        engine.dispose()
    engine = None
    SessionLocal = None


def get_session() -> Session:
    configure()
    assert SessionLocal is not None
    return SessionLocal()


def init_db() -> None:
    db_engine = configure()
    Base.metadata.create_all(db_engine)
    session = get_session()
    try:
        seed_if_empty(session)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@event.listens_for(Engine, "connect")
def _sqlite_pragmas(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
