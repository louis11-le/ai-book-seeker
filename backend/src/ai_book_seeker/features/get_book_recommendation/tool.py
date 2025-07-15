"""
Book Recommendation Tool: Registration for LangChain

This module provides registration logic for the Book Recommendation tool.
All input and output schemas are defined in schema.py.
It is designed for modular, feature-based integration with the LangChain agent.
"""

from typing import Any, Dict

from ai_book_seeker.features.get_book_recommendation.handler import (
    get_book_recommendation_handler,
)
from ai_book_seeker.features.get_book_recommendation.schema import (
    BookRecommendationOutputSchema,
    BookRecommendationSchema,
)


def register_tool(original_message: str = "") -> Dict[str, Any]:
    async def handler_with_message(request: BookRecommendationSchema):
        return await get_book_recommendation_handler(request, original_message)

    return {
        "name": "get_book_recommendation",
        "description": (
            "Get personalized book recommendations based on user preferences (age or age range, purpose, budget, genre). "
            "You can specify a single age or an age range (e.g., from 16 to 31). "
            "Only fill the 'purpose' field if the user explicitly mentions a purpose (e.g., 'for learning' or 'for entertainment'). Otherwise, leave it blank."
        ),
        "input_schema": BookRecommendationSchema,
        "output_schema": BookRecommendationOutputSchema,
        "handler": handler_with_message,
    }
