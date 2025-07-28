"""
Streaming Utilities for Chat API

This module provides utility functions for sanitizing and processing streaming data
from LangGraph workflows, ensuring safe and efficient streaming responses.

Functions:
- sanitize_update_data: Sanitize workflow update data for safe streaming
- sanitize_agent_results: Normalize agent results for consistent streaming format
- has_meaningful_agent_results: Check if agent results contain meaningful data
"""

from typing import Any, Dict


def sanitize_update_data(update: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize update data for safe streaming.

    Args:
        update: Raw update data from workflow

    Returns:
        Dict[str, Any]: Sanitized update data
    """
    # Remove sensitive or overly verbose data
    sanitized = update.copy()

    # Limit message content length for streaming
    if "messages" in sanitized and sanitized["messages"]:
        for msg in sanitized["messages"]:
            # Handle both object and dictionary message formats
            content = None
            if hasattr(msg, "content"):
                # Object format (e.g., AgentMessage)
                content = msg.content
            elif isinstance(msg, dict) and "content" in msg:
                # Dictionary format
                content = msg["content"]

            # Truncate long content if it exists
            if content and isinstance(content, str) and len(content) > 1000:
                truncated_content = content[:1000] + "..."
                if hasattr(msg, "content"):
                    msg.content = truncated_content
                elif isinstance(msg, dict):
                    msg["content"] = truncated_content

    return sanitized


def sanitize_agent_results(agent_results: Any) -> Dict[str, Any]:
    """
    Sanitize agent results for safe streaming.

    Args:
        agent_results: Raw agent results

    Returns:
        Dict[str, Any]: Sanitized agent results
    """
    if hasattr(agent_results, "model_dump"):
        return agent_results.model_dump()
    elif isinstance(agent_results, dict):
        return agent_results
    else:
        return {"result_type": type(agent_results).__name__}


def has_meaningful_agent_results(agent_results: Any) -> bool:
    """
    Check if agent results contain meaningful data.

    Args:
        agent_results: Agent results to check

    Returns:
        bool: True if results contain meaningful data
    """
    if hasattr(agent_results, "model_dump"):
        results_dict = agent_results.model_dump()
    elif isinstance(agent_results, dict):
        results_dict = agent_results
    else:
        return False

    # Check if any field has non-None, non-empty values
    for value in results_dict.values():
        if value is not None and value != "" and value != {} and value != []:
            return True

    return False
