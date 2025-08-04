"""
Streaming Utilities for Chat API

This module provides utility functions for sanitizing and processing streaming data
from LangGraph workflows, ensuring safe and efficient streaming responses.

Functions:
- sanitize_agent_results: Normalize agent results for consistent streaming format
- has_meaningful_agent_results: Check if agent results contain meaningful data
"""

from typing import Any, Dict


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
