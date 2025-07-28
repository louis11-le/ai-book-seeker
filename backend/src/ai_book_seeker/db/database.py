"""
Database connection and session management for the AI Book Seeker application.
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy.orm import Session, declarative_base, sessionmaker

from ai_book_seeker.core.config import AppSettings
from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.db.connection import create_database_engine

# Initialize logger
logger = get_logger(__name__)

# Base class for SQLAlchemy models
Base = declarative_base()


def create_session_factory(settings: AppSettings):
    """
    Create a SQLAlchemy session factory with the provided settings.

    Args:
        settings: Application settings containing database configuration

    Returns:
        sessionmaker: Configured SQLAlchemy session factory
    """
    engine = create_database_engine(settings)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db_session(settings: AppSettings) -> Generator[Session, None, None]:
    """
    Get a database session and ensure it's properly closed.

    Args:
        settings: Application settings containing database configuration

    Yields:
        SQLAlchemy session
    """
    session_factory = create_session_factory(settings)
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception as e:
        logger.error(f"Database error: {e}", exc_info=True)
        raise
    finally:
        session.close()
