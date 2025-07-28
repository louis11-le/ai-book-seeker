"""
Tool logic functions for workflow orchestration.

This module contains pure business logic functions that are reusable across nodes.
Follows the pattern of separating business logic from orchestration.
"""

from ai_book_seeker.features.get_book_recommendation.handler import (
    get_book_recommendation_handler,
)
from ai_book_seeker.features.get_book_recommendation.schema import (
    BookRecommendationOutputSchema,
    BookRecommendationSchema,
)
from ai_book_seeker.features.search_faq.handler import faq_handler
from ai_book_seeker.features.search_faq.schema import FAQOutputSchema, FAQSchema


async def run_faq_tool(extracted_parameters, faq_service):
    """
    Execute FAQ tool with extracted parameters.

    Args:
        extracted_parameters: Dictionary containing extracted parameters
        faq_service: FAQ service instance

    Returns:
        FAQOutputSchema: FAQ tool result
    """
    faq_query = extracted_parameters.get("faq_query", "") if extracted_parameters else ""
    faq_input = FAQSchema(query=faq_query)
    result: FAQOutputSchema = await faq_handler(faq_input, faq_service)
    return result


async def run_book_recommendation_tool(extracted_parameters, original_message, settings, chromadb_service):
    """
    Execute book recommendation tool with extracted parameters.

    Args:
        extracted_parameters: Dictionary containing extracted parameters
        original_message: Original user message
        settings: Application settings
        chromadb_service: ChromaDB service instance

    Returns:
        BookRecommendationOutputSchema: Book recommendation tool result
    """
    rec_input = BookRecommendationSchema(**(extracted_parameters or {}))
    result: BookRecommendationOutputSchema = await get_book_recommendation_handler(
        rec_input, original_message, settings, chromadb_service
    )
    return result


async def run_book_details_tool(extracted_parameters, settings):
    """
    Execute book details tool with extracted parameters.

    Args:
        extracted_parameters: Dictionary containing extracted parameters
        settings: Application settings

    Returns:
        dict: Book details tool result
    """
    # Extract parameters
    title = extracted_parameters.get("title", "") if extracted_parameters else ""
    author = extracted_parameters.get("author", "") if extracted_parameters else ""
    isbn = extracted_parameters.get("isbn", "") if extracted_parameters else ""

    # FAKE BUSINESS LOGIC for book details tool
    # TODO: Replace with real book details handler and database integration
    if not title and not author and not isbn:
        return {
            "error": "No book details provided",
            "message": "Please provide a book title, author, or ISBN to get book details.",
            "is_fake_data": True,
        }

    # Generate fake book details for testing
    fake_book_details = {
        "title": title or "Sample Book Title",
        "author": author or "Sample Author",
        "isbn": isbn or "978-0-123456-78-9",
        "format": "Hardcover",
        "pages": 320,
        "language": "English",
        "publisher": "Sample Publisher",
        "publication_date": "2023-01-15",
        "genre": "Fiction",
        "rating": 4.5,
        "price": 24.99,
        "currency": "USD",
        "availability": "In Stock",
        "stock_quantity": 15,
        "location": "Main Store",
        "shipping_weight": "1.2 lbs",
        "dimensions": "6.1 x 1.2 x 9.2 inches",
        "description": "A compelling story that explores themes of identity and discovery.",
        "is_fake_data": True,
        "message": "This is fake data for testing purposes. Replace with real database integration.",
    }

    return fake_book_details
