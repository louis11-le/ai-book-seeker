"""
FAQ Tool: Registration for LangChain

This module provides registration logic for the FAQ tool.
All input and output schemas are defined in schema.py.
It is designed for modular, feature-based integration with the LangChain agent.
"""

from typing import Any, Dict

from ai_book_seeker.features.search_faq.handler import get_faq_handler_with_app
from ai_book_seeker.features.search_faq.schema import FAQOutputSchema, FAQSchema


def register_tool(app) -> Dict[str, Any]:
    """
    Register the FAQ tool for LangChain agent use.
    Returns a dict with tool name, input schema, output schema, handler, and description.
    Input and output validation are handled by Pydantic schemas directly.
    The handler always uses the singleton FAQService from app.state.
    """
    return {
        "name": "search_faq",
        "description": "Search the FAQ knowledge base for answers to user questions using hybrid semantic and keyword search.",
        "input_schema": FAQSchema,
        "output_schema": FAQOutputSchema,
        "handler": get_faq_handler_with_app(app),
    }
