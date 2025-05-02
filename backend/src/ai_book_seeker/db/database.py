"""
Database connection and session management for the AI Book Seeker application.
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.db.connection import engine

# Initialize logger
logger = get_logger(__name__)

# Create session factory using the engine from connection.py
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy models
Base = declarative_base()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Get a database session and ensure it's properly closed.

    Yields:
        SQLAlchemy session
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        logger.error(f"Database error: {e}")
        session.rollback()
        raise
    finally:
        session.close()
