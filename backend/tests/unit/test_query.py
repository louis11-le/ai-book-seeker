"""
Unit tests for the query service.

This module tests the book search functionality with various criteria.
"""

import pytest
from ai_book_seeker.features.get_book_recommendation.schema import BookRecommendation
from ai_book_seeker.services.query import search_books_by_criteria


@pytest.fixture
def mock_db(mocker):
    """Fixture to create a mock database session with filtering logic."""

    def _make_db(books, age=None, purpose=None, budget=None, genre=None, query_text=None):
        # Filtering logic to simulate DB behavior
        filtered = books.copy()

        if age is not None:
            filtered = [b for b in filtered if b.from_age <= age <= b.to_age]

        if purpose is not None:
            filtered = [b for b in filtered if b.purpose == purpose]

        if genre is not None:
            filtered = [b for b in filtered if genre.lower() in b.genre.lower()]

        if budget is not None:
            filtered = [b for b in filtered if b.price <= budget]

        if query_text is not None:
            filtered = [b for b in filtered if query_text.lower() in b.title.lower()]

        mock_session = mocker.MagicMock()
        mock_query = mocker.MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = filtered
        return mock_session

    return _make_db


@pytest.fixture
def deterministic_books(book_factory):
    """Fixture for a deterministic list of Book objects."""
    return [
        book_factory(
            book_id=1,
            title="Book A",
            author="Author A",
            genre="Fiction",
            price=10.0,
            from_age=8,
            to_age=12,
            purpose="learning",
            tags="test,book",
            quantity=1,
        ),
        book_factory(
            book_id=2,
            title="Book B",
            author="Author B",
            genre="Science",
            price=15.0,
            from_age=10,
            to_age=14,
            purpose="entertainment",
            tags="test,book",
            quantity=2,
        ),
        book_factory(
            book_id=3,
            title="Book C",
            author="Author C",
            genre="Fantasy",
            price=20.0,
            from_age=12,
            to_age=16,
            purpose="learning",
            tags="test,book",
            quantity=3,
        ),
    ]


@pytest.mark.parametrize(
    "age, purpose, budget, genre, query_text, expected_count",
    [
        (8, None, None, "Fiction", "Book A", 1),
        (10, "entertainment", 20.0, "Science", "Book B", 1),
        (12, "learning", 25.0, "Fantasy", "Book C", 1),
    ],
)
def test_search_books_by_criteria_normal(
    mocker, mock_db, deterministic_books, age, purpose, budget, genre, query_text, expected_count
):
    """Test normal search scenarios with various criteria and deterministic data."""
    db = mock_db(deterministic_books, age=age, purpose=purpose, budget=budget, genre=genre, query_text=query_text)
    mocker.patch("ai_book_seeker.features.vector_search.logic.get_book_vector_matches", return_value=[])
    mocker.patch(
        "ai_book_seeker.services.query.generate_explanations",
        return_value={b.id: f"Explanation for {b.title}" for b in deterministic_books},
    )
    # Create a mock chromadb_service
    mock_chromadb_service = mocker.MagicMock()
    mock_chromadb_service.settings = mocker.MagicMock()
    mock_chromadb_service.settings.batch_size = 3
    results = search_books_by_criteria(
        db,
        mock_chromadb_service,
        age=age,
        purpose=purpose,
        budget=budget,
        genre=genre,
        query_text=query_text,
    )
    assert isinstance(results, list)
    assert len(results) == expected_count
    for book in results:
        assert isinstance(book, BookRecommendation)
        assert hasattr(book, "title")
        assert hasattr(book, "author")
        assert hasattr(book, "genre")
        assert hasattr(book, "reason")
        assert book.reason is not None and book.reason.startswith("Explanation for")


def test_search_books_by_criteria_empty_result(mocker, mock_db):
    """Test that an empty result is returned when no books match."""
    db = mock_db([])
    mocker.patch("ai_book_seeker.features.vector_search.logic.get_book_vector_matches", return_value=[])
    mocker.patch("ai_book_seeker.services.query.generate_explanations", return_value={})
    # Create a mock chromadb_service
    mock_chromadb_service = mocker.MagicMock()
    mock_chromadb_service.settings = mocker.MagicMock()
    mock_chromadb_service.settings.batch_size = 3
    results = search_books_by_criteria(
        db, mock_chromadb_service, age=99, purpose="unknown", budget=0.0, genre="none", query_text="no match"
    )
    assert isinstance(results, list)
    assert len(results) == 0


def test_search_books_by_criteria_missing_explanations(mocker, mock_db, deterministic_books):
    """Test that books without explanations get a default explanation."""
    db = mock_db(deterministic_books)
    mocker.patch("ai_book_seeker.features.vector_search.logic.get_book_vector_matches", return_value=[])
    # Only provide explanation for the first book
    mocker.patch(
        "ai_book_seeker.services.query.generate_explanations",
        return_value={deterministic_books[0].id: "Custom explanation for Book A"},
    )
    # Create a mock chromadb_service
    mock_chromadb_service = mocker.MagicMock()
    mock_chromadb_service.settings = mocker.MagicMock()
    mock_chromadb_service.settings.batch_size = 3
    results = search_books_by_criteria(
        db, mock_chromadb_service, age=8, purpose=None, budget=None, genre="Fiction", query_text="Book A"
    )
    assert results[0].reason == "Custom explanation for Book A"
    for book in results[1:]:
        assert book.reason is not None and book.reason.startswith("This book is")


def test_search_books_by_criteria_invalid_input(mocker, mock_db, deterministic_books):
    """Test that invalid input (negative age) is handled gracefully. Non-numeric budget is not tested due to type constraints."""
    db = mock_db(deterministic_books)
    mocker.patch("ai_book_seeker.features.vector_search.logic.get_book_vector_matches", return_value=[])
    mocker.patch(
        "ai_book_seeker.services.query.generate_explanations",
        return_value={b.id: f"Explanation for {b.title}" for b in deterministic_books},
    )
    # Create a mock chromadb_service
    mock_chromadb_service = mocker.MagicMock()
    mock_chromadb_service.settings = mocker.MagicMock()
    mock_chromadb_service.settings.batch_size = 3
    # Negative age
    results = search_books_by_criteria(
        db, mock_chromadb_service, age=-5, purpose=None, budget=None, genre=None, query_text=None
    )
    assert isinstance(results, list)
    for book in results:
        assert isinstance(book, BookRecommendation)


def test_search_books_by_criteria_partial_match(mocker, mock_db, deterministic_books):
    """Test that partial matches (e.g., genre substring) return correct books."""
    db = mock_db(deterministic_books)
    mocker.patch("ai_book_seeker.features.vector_search.logic.get_book_vector_matches", return_value=[])
    mocker.patch(
        "ai_book_seeker.services.query.generate_explanations",
        return_value={b.id: f"Explanation for {b.title}" for b in deterministic_books},
    )
    # Create a mock chromadb_service
    mock_chromadb_service = mocker.MagicMock()
    mock_chromadb_service.settings = mocker.MagicMock()
    mock_chromadb_service.settings.batch_size = 3
    # 'Fic' should match 'Fiction'
    results = search_books_by_criteria(
        db, mock_chromadb_service, age=8, purpose=None, budget=None, genre="Fic", query_text=None
    )
    assert any(book.genre == "Fiction" for book in results)


def test_search_books_by_criteria_db_error(mocker):
    """Test that an exception in the DB layer is handled gracefully."""
    mock_session = mocker.MagicMock()
    mock_session.query.side_effect = Exception("DB error")
    mocker.patch("ai_book_seeker.features.vector_search.logic.get_book_vector_matches", return_value=[])
    mocker.patch("ai_book_seeker.services.query.generate_explanations", return_value={})
    # Create a mock chromadb_service
    mock_chromadb_service = mocker.MagicMock()
    mock_chromadb_service.settings = mocker.MagicMock()
    mock_chromadb_service.settings.batch_size = 3
    results = search_books_by_criteria(
        mock_session, mock_chromadb_service, age=8, purpose=None, budget=None, genre=None, query_text=None
    )
    assert results == []
