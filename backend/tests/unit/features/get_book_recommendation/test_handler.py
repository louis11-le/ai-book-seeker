import asyncio
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
from ai_book_seeker.utils.helpers import extract_age_range_from_message


def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_handler_with_valid_params_single_age(test_db, monkeypatch):
    # Insert a test book for a single age
    book = Book(
        title="Test Book Single Age",
        author="Author",
        description="A book for testing single age.",
        from_age=12,
        to_age=12,
        purpose="learning",
        genre="fiction",
        price=9.99,
        tags="test,fiction",
        quantity=5,
    )
    test_db.add(book)
    test_db.commit()
    test_db.refresh(book)

    request = BookRecommendationSchema(
        age=12, age_from=None, age_to=None, purpose="learning", budget=20.0, genre="fiction"
    )

    @contextlib.contextmanager
    def fake_get_db_session():
        yield test_db

    monkeypatch.setattr(
        "ai_book_seeker.features.get_book_recommendation.handler.get_db_session",
        fake_get_db_session,
    )
    result = run_async(get_book_recommendation_handler(request, "I want a book for learning for a 12 year old"))

    assert isinstance(result, BookRecommendationOutputSchema)
    assert len(result.data) == 1
    assert result.data[0].title == "Test Book Single Age"
    assert result.data[0].purpose == "learning"


def test_handler_with_valid_params_range(test_db, monkeypatch):
    # Insert a test book for an age range
    book = Book(
        title="Test Book Range",
        author="Author",
        description="A book for testing range.",
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

    request = BookRecommendationSchema(
        age=None, age_from=10, age_to=15, purpose="learning", budget=20.0, genre="fiction"
    )

    @contextlib.contextmanager
    def fake_get_db_session():
        yield test_db

    monkeypatch.setattr(
        "ai_book_seeker.features.get_book_recommendation.handler.get_db_session",
        fake_get_db_session,
    )
    result = run_async(get_book_recommendation_handler(request, "I want a book for learning for ages 10 to 15"))

    assert isinstance(result, BookRecommendationOutputSchema)
    assert len(result.data) == 1
    assert result.data[0].title == "Test Book Range"
    assert result.data[0].purpose == "learning"


def test_handler_with_no_results(monkeypatch):
    monkeypatch.setattr(
        "ai_book_seeker.features.get_book_recommendation.handler.search_books_by_criteria",
        lambda db, age_from, age_to, purpose, budget, genre: [],
    )
    request = BookRecommendationSchema(
        age=99, age_from=None, age_to=None, purpose="unknown", budget=1.0, genre="nonexistent"
    )
    result = run_async(get_book_recommendation_handler(request, "I want a book for an unknown purpose"))
    assert isinstance(result, BookRecommendationOutputSchema)
    assert result.data == []
    assert "couldn't find any books" in result.text or "I couldn't find any books" in result.text


def test_handler_with_missing_params(monkeypatch):
    # Should still work with all params None
    monkeypatch.setattr(
        "ai_book_seeker.features.get_book_recommendation.handler.search_books_by_criteria",
        lambda db, age_from, age_to, purpose, budget, genre: [],
    )
    request = BookRecommendationSchema(age=None, age_from=None, age_to=None, purpose=None, budget=None, genre=None)
    result = run_async(get_book_recommendation_handler(request, ""))
    assert isinstance(result, BookRecommendationOutputSchema)
    assert isinstance(result.data, list)
    # Purpose should not be inferred
    if result.data:
        for book in result.data:
            assert not book.purpose


def test_schema_validation():
    # Valid instantiation
    schema = BookRecommendationSchema(
        age=10, age_from=None, age_to=None, purpose="learning", budget=15.0, genre="fiction"
    )
    assert schema.age == 10
    assert schema.purpose == "learning"
    assert schema.budget == 15.0
    assert schema.genre == "fiction"
    # Invalid type
    with pytest.raises(ValueError):
        BookRecommendationSchema(age="not-an-int", age_from=None, age_to=None, purpose=None, budget=None, genre=None)  # type: ignore


def test_handler_purpose_only_when_explicit(monkeypatch):
    # If purpose is not explicit, it should not be set in the output
    monkeypatch.setattr(
        "ai_book_seeker.features.get_book_recommendation.handler.search_books_by_criteria",
        lambda db, age_from, age_to, purpose, budget, genre: [
            Book(
                title="Adventure Book",
                author="Author",
                description="A book for adventure.",
                from_age=10,
                to_age=15,
                purpose=None,
                genre="adventure",
                price=12.99,
                tags="adventure",
                quantity=3,
            )
        ],
    )
    request = BookRecommendationSchema(age=12, age_from=None, age_to=None, purpose=None, budget=20.0, genre="adventure")
    result = run_async(get_book_recommendation_handler(request, "I want a book about adventure"))
    assert isinstance(result, BookRecommendationOutputSchema)
    if result.data:
        for book in result.data:
            assert not book.purpose


def test_extract_age_range_from_message_range():
    assert extract_age_range_from_message("from 16 to 31") == (16, 31)
    assert extract_age_range_from_message("16-31") == (16, 31)
    assert extract_age_range_from_message("16 to 31") == (16, 31)


def test_extract_age_range_from_message_less_than():
    assert extract_age_range_from_message("under 33") == (None, 32)
    assert extract_age_range_from_message("less than 20") == (None, 19)
    assert extract_age_range_from_message("below 18") == (None, 17)


def test_extract_age_range_from_message_greater_than():
    assert extract_age_range_from_message("over 33") == (34, None)
    assert extract_age_range_from_message("more than 20") == (21, None)
    assert extract_age_range_from_message("above 18") == (19, None)


def test_extract_age_range_from_message_single_age():
    assert extract_age_range_from_message("age 16") == (16, 16)
    assert extract_age_range_from_message("16 year old") == (16, 16)
    assert extract_age_range_from_message("for a 12 year-old reader") == (12, 12)


def test_extract_age_range_from_message_no_match():
    assert extract_age_range_from_message("I want a book for adults") == (None, None)
