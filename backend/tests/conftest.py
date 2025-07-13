"""
PyTest configuration and fixtures for the AI Book Seeker test suite.
"""

import pytest

# Import directly from the ai_book_seeker package
from ai_book_seeker.db.database import Base
from ai_book_seeker.db.models import Book
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from .helpers import create_test_book


@pytest.fixture
def test_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_book(test_db):
    """Create a test book in the database."""
    book = Book(
        title="Test Book",
        author="Test Author",
        publication_year=2023,
        isbn="1234567890",
        description="A test book for unit testing",
        price=19.99,
        genre="Test",
        target_age="8-12",
        metadata={"tags": ["test", "sample"]},
        vector_id="test123",
    )
    test_db.add(book)
    test_db.commit()
    test_db.refresh(book)
    return book


@pytest.fixture
def book_factory():
    """
    Pytest fixture that returns a factory function for creating Book instances with custom values.
    Usage:
        def test_something(book_factory):
            book = book_factory(title="Custom Title", price=9.99)
    """

    def _factory(**kwargs):
        return create_test_book(**kwargs)

    return _factory
