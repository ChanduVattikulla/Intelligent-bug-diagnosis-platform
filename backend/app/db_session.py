"""SQLAlchemy engine and session management for Neon PostgreSQL."""

import sys

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.config import DATABASE_URL
from app.db_models import Base


def _database_error(message: str) -> None:
    print(f"Database initialization failed: {message}", file=sys.stderr)
    print("Check DATABASE_URL in backend/.env.", file=sys.stderr)


if DATABASE_URL:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
else:
    engine = None
    SessionLocal = None


def get_session() -> Session:
    """Return a database session, with a clear error when configuration is absent."""
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL is missing. Check DATABASE_URL in backend/.env.")
    return SessionLocal()


def create_all_tables() -> bool:
    """Create the application tables and report connection errors without a traceback."""
    if engine is None:
        _database_error("DATABASE_URL is missing")
        return False

    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        Base.metadata.create_all(bind=engine)
    except SQLAlchemyError as exc:
        _database_error(f"could not connect to PostgreSQL ({exc})")
        return False
    return True