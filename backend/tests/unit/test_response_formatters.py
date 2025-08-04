"""
Unit tests for response formatters.

Tests the formatting functions for streaming tool responses.
"""

from unittest.mock import Mock

from ai_book_seeker.workflows.utils.response_formatters import (
    format_book_details_response,
    format_book_recommendation_response,
    format_faq_response,
)


class TestFormatFAQResponse:
    """Test cases for FAQ response formatting."""

    def test_format_faq_response_with_answer_attribute(self):
        """Test formatting FAQ response with answer attribute."""
        mock_result = Mock()
        mock_result.answer = "This is the answer"

        result = format_faq_response(mock_result)

        assert result == "FAQ Answer:\nThis is the answer"

    def test_format_faq_response_with_content_attribute(self):
        """Test formatting FAQ response with content attribute."""
        mock_result = Mock()
        mock_result.content = "This is the content"

        result = format_faq_response(mock_result)

        assert result == "FAQ Answer:\nThis is the content"

    def test_format_faq_response_with_dict(self):
        """Test formatting FAQ response with dictionary."""
        result_dict = {"answer": "This is the answer"}

        result = format_faq_response(result_dict)

        assert result == "FAQ Answer:\nThis is the answer"

    def test_format_faq_response_with_dict_content(self):
        """Test formatting FAQ response with dictionary containing content."""
        result_dict = {"content": "This is the content"}

        result = format_faq_response(result_dict)

        assert result == "FAQ Answer:\nThis is the content"

    def test_format_faq_response_with_string(self):
        """Test formatting FAQ response with string."""
        result = format_faq_response("Simple string answer")

        assert result == "FAQ Answer:\nSimple string answer"

    def test_format_faq_response_none(self):
        """Test formatting FAQ response with None."""
        result = format_faq_response(None)

        assert result == "FAQ: No answer available"

    def test_format_faq_response_empty_dict(self):
        """Test formatting FAQ response with empty dict."""
        result = format_faq_response({})

        assert result == "FAQ: No answer available"


class TestFormatBookRecommendationResponse:
    """Test cases for book recommendation response formatting."""

    def test_format_book_recommendation_with_books_attribute(self):
        """Test formatting book recommendation with books attribute."""
        mock_book = Mock()
        mock_book.title = "Test Book"
        mock_book.author = "Test Author"
        mock_book.description = "Test Description"
        mock_book.price = "$10.99"

        mock_result = Mock()
        mock_result.books = [mock_book]

        result = format_book_recommendation_response(mock_result)

        expected = "Book Recommendations:\n📚 Test Book by Test Author\n   Test Description\n   Price: $10.99"
        assert result == expected

    def test_format_book_recommendation_with_recommendations_attribute(self):
        """Test formatting book recommendation with recommendations attribute."""
        mock_book = Mock()
        mock_book.title = "Test Book"
        mock_book.author = "Test Author"
        mock_book.description = "Test Description"
        mock_book.price = "$10.99"

        mock_result = Mock()
        mock_result.recommendations = [mock_book]

        result = format_book_recommendation_response(mock_result)

        expected = "Book Recommendations:\n📚 Test Book by Test Author\n   Test Description\n   Price: $10.99"
        assert result == expected

    def test_format_book_recommendation_with_dict(self):
        """Test formatting book recommendation with dictionary."""
        book_dict = {
            "title": "Test Book",
            "author": "Test Author",
            "description": "Test Description",
            "price": "$10.99",
        }

        result = format_book_recommendation_response(book_dict)

        expected = "Book Recommendations:\n📚 Test Book by Test Author\n   Test Description\n   Price: $10.99"
        assert result == expected

    def test_format_book_recommendation_with_list(self):
        """Test formatting book recommendation with list."""
        books_list = [
            {"title": "Book 1", "author": "Author 1", "description": "Description 1", "price": "$10.99"},
            {"title": "Book 2", "author": "Author 2", "description": "Description 2", "price": "$15.99"},
        ]

        result = format_book_recommendation_response(books_list)

        expected = "Book Recommendations:\n📚 Book 1 by Author 1\n   Description 1\n   Price: $10.99\n\n📚 Book 2 by Author 2\n   Description 2\n   Price: $15.99"
        assert result == expected

    def test_format_book_recommendation_none(self):
        """Test formatting book recommendation with None."""
        result = format_book_recommendation_response(None)

        assert result == "Book Recommendation: No recommendations available"

    def test_format_book_recommendation_empty_list(self):
        """Test formatting book recommendation with empty list."""
        result = format_book_recommendation_response([])

        assert result == "Book Recommendation: No valid recommendations found"


class TestFormatBookDetailsResponse:
    """Test cases for book details response formatting."""

    def test_format_book_details_with_attributes(self):
        """Test formatting book details with attributes."""
        mock_book = Mock()
        mock_book.title = "Test Book"
        mock_book.author = "Test Author"
        mock_book.description = "Test Description"
        mock_book.price = "$10.99"
        mock_book.availability = "In Stock"

        result = format_book_details_response(mock_book)

        expected = (
            "Book Details:\n📚 Test Book by Test Author\n   Test Description\n   "
            "Price: $10.99\n   Availability: In Stock"
        )
        assert result == expected

    def test_format_book_details_with_dict(self):
        """Test formatting book details with dictionary."""
        book_dict = {
            "title": "Test Book",
            "author": "Test Author",
            "description": "Test Description",
            "price": "$10.99",
            "availability": "In Stock",
        }

        result = format_book_details_response(book_dict)

        expected = (
            "Book Details:\n📚 Test Book by Test Author\n   Test Description\n   "
            "Price: $10.99\n   Availability: In Stock"
        )
        assert result == expected

    def test_format_book_details_with_string(self):
        """Test formatting book details with string."""
        result = format_book_details_response("Simple book string")

        assert result == "Book Details:\nSimple book string"

    def test_format_book_details_none(self):
        """Test formatting book details with None."""
        result = format_book_details_response(None)

        assert result == "Book Details: No details available"

    def test_format_book_details_missing_attributes(self):
        """Test formatting book details with missing attributes."""
        mock_book = Mock()
        mock_book.title = "Test Book"
        mock_book.author = "Test Author"
        # Missing description, price, availability

        result = format_book_details_response(mock_book)

        expected = (
            "Book Details:\n📚 Test Book by Test Author\n   No description available\n   "
            "Price: Price not available\n   Availability: Availability unknown"
        )
        assert result == expected
