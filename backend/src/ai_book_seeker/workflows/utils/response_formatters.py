"""
Response formatters for streaming tool responses.

This module provides formatting functions for immediate streaming of tool results
to improve user experience with progressive response building.
"""

from typing import Any

from ai_book_seeker.core.logging import get_logger

logger = get_logger(__name__)


def format_faq_response(faq_result: Any) -> str:
    """
    Format FAQ response for immediate streaming.

    Args:
        faq_result: FAQ tool result object

    Returns:
        str: Formatted FAQ response for streaming
    """
    if not faq_result:
        return "FAQ: No answer available"

    try:
        # Handle different FAQ result formats
        if hasattr(faq_result, "text"):
            return f"FAQ Answer:\n{faq_result.text}"
        elif hasattr(faq_result, "answer"):
            return f"FAQ Answer:\n{faq_result.answer}"
        elif hasattr(faq_result, "content"):
            return f"FAQ Answer:\n{faq_result.content}"
        elif isinstance(faq_result, dict):
            # Handle the new FAQ result structure with 'text' and 'data' fields
            if "text" in faq_result:
                return f"FAQ Answer:\n{faq_result['text']}"
            elif "answer" in faq_result:
                return f"FAQ Answer:\n{faq_result['answer']}"
            elif "content" in faq_result:
                return f"FAQ Answer:\n{faq_result['content']}"
            else:
                # Fallback to string representation
                return f"FAQ Answer:\n{str(faq_result)}"
        else:
            return f"FAQ Answer:\n{str(faq_result)}"
    except Exception as e:
        logger.error(f"Error formatting FAQ response: {e}")
        return "FAQ: Error formatting response"


def format_book_recommendation_response(book_result: Any) -> str:
    """
    Format book recommendation response for immediate streaming.

    Args:
        book_result: Book recommendation tool result object

    Returns:
        str: Formatted book recommendation response for streaming
    """
    if not book_result:
        return "Book Recommendation: No recommendations available"

    try:
        # Handle BookRecommendationOutputSchema objects first (most common case)
        if hasattr(book_result, "text"):
            return f"Book Recommendations:\n{book_result.text}"
        elif hasattr(book_result, "answer"):
            return f"Book Recommendations:\n{book_result.answer}"
        elif hasattr(book_result, "content"):
            return f"Book Recommendations:\n{book_result.content}"

        # Handle dictionary results
        elif isinstance(book_result, dict):
            if "text" in book_result:
                return f"Book Recommendations:\n{book_result['text']}"
            elif "books" in book_result:
                books = book_result["books"]
            elif "recommendations" in book_result:
                books = book_result["recommendations"]
            else:
                # Fallback to string representation
                return f"Book Recommendations:\n{str(book_result)}"
        elif hasattr(book_result, "books"):
            books = book_result.books
        elif hasattr(book_result, "recommendations"):
            books = book_result.recommendations
        elif isinstance(book_result, list):
            books = book_result
        else:
            books = [book_result]

        # Process individual books if we have a list
        books_text = []
        for book in books:
            if hasattr(book, "title") and hasattr(book, "author"):
                title = book.title
                author = book.author
                description = getattr(book, "description", "No description available")
                price = getattr(book, "price", "Price not available")
                books_text.append(f"📚 {title} by {author}\n   {description}\n   Price: {price}")
            elif isinstance(book, dict):
                title = book.get("title", "Unknown Title")
                author = book.get("author", "Unknown Author")
                description = book.get("description", "No description available")
                price = book.get("price", "Price not available")
                books_text.append(f"📚 {title} by {author}\n   {description}\n   Price: {price}")
            else:
                books_text.append(f"📚 {str(book)}")

        if books_text:
            return "Book Recommendations:\n" + "\n\n".join(books_text)
        else:
            return "Book Recommendation: No valid recommendations found"
    except Exception as e:
        logger.error(f"Error formatting book recommendation response: {e}")
        return "Book Recommendation: Error formatting response"


def format_book_details_response(book_result: Any) -> str:
    """
    Format book details response for immediate streaming.

    Args:
        book_result: Book details tool result object

    Returns:
        str: Formatted book details response for streaming
    """
    if not book_result:
        return "Book Details: No details available"

    try:
        # Handle different book details formats
        if hasattr(book_result, "title") and hasattr(book_result, "author"):
            title = book_result.title
            author = book_result.author
            description = getattr(book_result, "description", "No description available")
            price = getattr(book_result, "price", "Price not available")
            availability = getattr(book_result, "availability", "Availability unknown")

            return f"Book Details:\n📚 {title} by {author}\n   {description}\n   Price: {price}\n   Availability: {availability}"
        elif isinstance(book_result, dict):
            title = book_result.get("title", "Unknown Title")
            author = book_result.get("author", "Unknown Author")
            description = book_result.get("description", "No description available")
            price = book_result.get("price", "Price not available")
            availability = book_result.get("availability", "Availability unknown")

            return f"Book Details:\n📚 {title} by {author}\n   {description}\n   Price: {price}\n   Availability: {availability}"
        else:
            return f"Book Details:\n{str(book_result)}"

    except Exception as e:
        logger.error(f"Error formatting book details response: {e}")
        return "Book Details: Error formatting response"
