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


def register_tool() -> Dict[str, Any]:
    """
    Register the Book Recommendation tool for LangChain agent use.
    Returns a dict with tool name, input schema, output schema, handler, and description.
    Input and output validation are handled by Pydantic schemas directly.
    """
    return {
        "name": "get_book_recommendation",
        "description": "Get personalized book recommendations based on user preferences (age, purpose, budget, genre).",
        "input_schema": BookRecommendationSchema,
        "output_schema": BookRecommendationOutputSchema,
        "handler": get_book_recommendation_handler,
    }
