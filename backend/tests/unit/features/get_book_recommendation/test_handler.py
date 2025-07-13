import contextlib

import pytest
from ai_book_seeker.db.models import Book
from ai_book_seeker.features.get_book_recommendation.handler import (
    get_book_recommendation_handler,
)
from ai_book_seeker.features.get_book_recommendation.schema import (
    BookRecommendationOutputSchema,
    BookRecommendationSchema,
)


def test_handler_with_valid_params(test_db, monkeypatch):
    # Insert a test book into the test DB
    book = Book(
        title="Test Book",
        author="Author",
        description="A book for testing.",
        from_age=10,
        to_age=15,
        purpose="learning",
        genre="fiction",
        price=9.99,
        tags="test,fiction",
        quantity=5,
    )
    test_db.add(book)
    test_db.commit()
    test_db.refresh(book)

    request = BookRecommendationSchema(age=12, purpose="learning", budget=20.0, genre="fiction")

    # Patch get_db_session to yield our test_db as a context manager
    @contextlib.contextmanager
    def fake_get_db_session():
        yield test_db

    monkeypatch.setattr(
        "ai_book_seeker.features.get_book_recommendation.handler.get_db_session",
        fake_get_db_session,
    )
    result = get_book_recommendation_handler(request)

    assert isinstance(result, BookRecommendationOutputSchema)
    assert len(result.data) == 1
    assert result.data[0].title == "Test Book"
    assert "matching your preferences" in result.text


def test_handler_with_no_results(monkeypatch):
    monkeypatch.setattr(
        "ai_book_seeker.features.get_book_recommendation.handler.search_books_by_criteria",
        lambda db, age, purpose, budget, genre: [],
    )
    request = BookRecommendationSchema(age=99, purpose="unknown", budget=1.0, genre="nonexistent")
    result = get_book_recommendation_handler(request)
    assert isinstance(result, BookRecommendationOutputSchema)
    assert result.data == []
    assert "couldn't find any books" in result.text


def test_handler_with_missing_params(monkeypatch):
    # Should still work with all params None
    monkeypatch.setattr(
        "ai_book_seeker.features.get_book_recommendation.handler.search_books_by_criteria",
        lambda db, age, purpose, budget, genre: [],
    )
    request = BookRecommendationSchema(age=None, purpose=None, budget=None, genre=None)
    result = get_book_recommendation_handler(request)
    assert isinstance(result, BookRecommendationOutputSchema)
    assert isinstance(result.data, list)


def test_schema_validation():
    # Valid instantiation
    schema = BookRecommendationSchema(age=10, purpose="learning", budget=15.0, genre="fiction")
    assert schema.age == 10
    assert schema.purpose == "learning"
    assert schema.budget == 15.0
    assert schema.genre == "fiction"
    # Invalid type
    with pytest.raises(ValueError):
        BookRecommendationSchema(age="not-an-int", purpose=None, budget=None, genre=None)  # type: ignore
