"""
LangChain Tool Central Registry

This module aggregates all feature tool registrations for the LangChain agent.
Each feature (FAQ, Book Recommendation, Purchase Book, etc.) should define its own tool.py
with input/output schemas and a register_tool() function.

This file imports and aggregates all feature tools for agent orchestration.

All tool registry configuration (tool map, enable/disable flags, etc.) is accessed via the centralized AppSettings config object.
Do not use direct environment variable access or hardcoded values; use only AppSettings.
"""

from typing import Any, Dict, List

from ai_book_seeker.core.config import AppSettings
from ai_book_seeker.features.get_book_recommendation.tool import (
    register_tool as register_book_recommendation_tool,
)
from ai_book_seeker.features.search_faq.tool import register_tool as register_faq_tool

# TODO: from ai_book_seeker.features.purchase_book.tool import register_tool as register_purchase_book_tool


def get_all_tools(
    app, interface: str = "chat", original_message: str = "", settings: AppSettings | None = None
) -> List[Dict[str, Any]]:
    """
    Return a list of registered tools for the LangChain agent, filtered by interface type.
    The app instance is passed to each tool registration for dependency injection.
    Only tools enabled for the given interface (per settings.interface_tool_map) are returned.

    Args:
        app: FastAPI app instance for dependency injection
        interface: Interface type (chat, voice, etc.)
        original_message: Original user message for context
        settings: Application settings. If None, will use default interface mapping.
    """
    all_tools = {
        "search_faq": register_faq_tool(app),
        "get_book_recommendation": register_book_recommendation_tool(original_message),
        # "purchase_book": register_purchase_book_tool(app),
    }

    tools = []
    if settings is not None:
        enabled_tool_names = settings.interface_tool_map.get(interface, [])
        tools = [all_tools[name] for name in enabled_tool_names if name in all_tools]

    return tools
