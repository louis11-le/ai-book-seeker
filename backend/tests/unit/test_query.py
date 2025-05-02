"""
Unit tests for the query service module.
"""

from unittest.mock import MagicMock, patch

import pytest

from ai_book_seeker.services.query import BookPreferences, get_recommendations
from tests.helpers import create_test_books


@patch("ai_book_seeker.services.query.get_book_recommendations")
def test_get_recommendations_with_query_text(mock_get_book_recs):
    """Test getting recommendations with query text."""
    # Create test data
    test_books = create_test_books(3)
    mock_get_book_recs.return_value = test_books

    # Create preferences with query text
    preferences = BookPreferences(query_text="books about space travel", age="8-12", genre="science fiction")

    # Call the function
    results = get_recommendations(preferences)

    # Check that the right function was called with the query text
    mock_get_book_recs.assert_called_once()
    assert preferences.query_text in mock_get_book_recs.call_args[0]

    # Check that we got the expected results
    assert len(results) == 3
    assert results[0].title == test_books[0].title
    assert results[1].author == test_books[1].author
    assert results[2].genre == test_books[2].genre


@patch("ai_book_seeker.services.query.get_book_recommendations")
def test_get_recommendations_with_preferences_only(mock_get_book_recs):
    """Test getting recommendations with just preferences, no query text."""
    # Create test data
    test_books = create_test_books(2)
    mock_get_book_recs.return_value = test_books

    # Create preferences without query text
    preferences = BookPreferences(age="teen", purpose="entertainment", budget="20", genre="fantasy")

    # Generate expected query text from preferences
    expected_query = "fantasy books for teen readers for entertainment with budget $20"

    # Call the function
    results = get_recommendations(preferences)

    # Check that the right function was called with a generated query
    mock_get_book_recs.assert_called_once()
    call_args = mock_get_book_recs.call_args[0][0]
    assert "fantasy" in call_args
    assert "teen" in call_args
    assert "entertainment" in call_args

    # Check that we got the expected results
    assert len(results) == 2
    assert all(isinstance(book, object) for book in results)


@patch("ai_book_seeker.services.query.get_book_recommendations")
def test_get_recommendations_with_empty_preferences(mock_get_book_recs):
    """Test getting recommendations with empty preferences."""
    # Create test data - empty result
    mock_get_book_recs.return_value = []

    # Create empty preferences
    preferences = BookPreferences()

    # Call the function
    results = get_recommendations(preferences)

    # Check that the function was still called
    mock_get_book_recs.assert_called_once()

    # Check that we got an empty list
    assert isinstance(results, list)
    assert len(results) == 0
