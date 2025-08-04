"""
Routing analysis logic for workflow orchestration.

This module contains the logic for analyzing queries and determining routing decisions.
Follows LangGraph best practices for routing analysis.

Key Components:
- analyze_query_for_routing: Analyzes user queries to determine routing decisions

Architecture:
- LLM-powered routing analysis with structured output
- Comprehensive error handling and validation
- Integration with workflow state management
- Support for multi-agent and multi-purpose queries
"""

import json
from typing import Any, Dict

from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.workflows.schemas.routing import RoutingConstants

logger = get_logger(__name__)


def _validate_confidence(confidence: float) -> float:
    """
    Validate and normalize confidence value.

    Args:
        confidence: Raw confidence value from LLM

    Returns:
        float: Normalized confidence value within bounds
    """
    return max(RoutingConstants.MIN_CONFIDENCE, min(RoutingConstants.MAX_CONFIDENCE, confidence))


def _validate_reasoning_word_count(reasoning: str, max_words: int = RoutingConstants.MAX_REASONING_WORDS) -> str:
    """
    Validate and truncate reasoning to ensure it's within word limit.

    Args:
        reasoning: Raw reasoning text from LLM
        max_words: Maximum number of words allowed

    Returns:
        str: Validated reasoning text within word limit
    """
    if not reasoning:
        return ""

    words = reasoning.strip().split()
    if len(words) <= max_words:
        return reasoning.strip()

    # Truncate to max_words and add ellipsis
    truncated_words = words[:max_words]
    return " ".join(truncated_words) + "..."


def _validate_and_clean_analysis(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and clean LLM analysis response.

    Args:
        analysis: Raw analysis from LLM

    Returns:
        Dict[str, Any]: Cleaned and validated analysis

    Raises:
        ValueError: If required fields are missing from LLM analysis
    """
    # Validate required next_node field - no fallback
    next_node = analysis.get("next_node")
    if not next_node:
        raise ValueError("LLM analysis missing required 'next_node' field - no fallback mechanism")

    return {
        "next_node": next_node,
        "participating_agents": analysis.get("participating_agents", []),
        "is_multi_purpose": analysis.get("is_multi_purpose", False),
        "is_multi_agent": analysis.get("is_multi_agent", False),
        "reasoning": _validate_reasoning_word_count(analysis.get("reasoning", "")),
        "confidence": _validate_confidence(analysis.get("confidence", RoutingConstants.DEFAULT_CONFIDENCE)),
    }


async def analyze_query_for_routing(query: str, llm: Any, interface: str) -> Dict[str, Any]:
    """
    Analyze user query to determine routing decisions.

    This function performs LLM-based analysis to determine which agents should handle
    a query and provides routing metadata for workflow orchestration.

    Args:
        query: User query string to analyze
        llm: Language model for analysis (required - no fallback)
        interface: Interface type ("chat" or "voice") for agent selection

    Returns:
        Dict[str, Any]: Routing analysis with the following structure:
            - next_node: Target agent or coordinator node (REQUIRED - no fallback)
            - participating_agents: List of agents that should participate
            - is_multi_purpose: Whether query has multiple purposes
            - is_multi_agent: Whether multiple agents are needed
            - reasoning: Brief explanation of routing decision (max 30 words)
            - confidence: Confidence score (0.0-1.0)

    Raises:
        ValueError: If LLM analysis fails or missing required fields - no fallback mechanism

    Example:
        ```python
        # Analyze query for routing decisions
        analysis = await analyze_query_for_routing("I need book recommendations", llm, "chat")
        # Returns: {
        #     "next_node": "general_agent",  # REQUIRED - no fallback
        #     "participating_agents": ["general_agent"],
        #     "is_multi_purpose": False,
        #     "is_multi_agent": False,
        #     "reasoning": "Book recommendation query for chat interface",
        #     "confidence": 0.85
        # }
        ```

    Note:
        LLM is required for routing analysis. No fallback mechanism - system fails
        gracefully when LLM is unavailable or returns incomplete analysis.
        The 'next_node' field is REQUIRED and must be provided by the LLM.
        Interface-aware routing ensures voice queries use general_voice_agent and
        chat queries use general_agent.
        Optimized for minimal token usage with concise prompts.
    """

    try:
        # Use LLM for sophisticated analysis (required - no fallback)
        analysis_prompt = f"""
        Route query: "{query}" (Interface: {interface})

        Agents:
        - general_agent: FAQ, book recommendations (CHAT ONLY)
        - general_voice_agent: Voice queries, book recommendations (VOICE ONLY)

        Rules:
        - Voice interface → general_voice_agent only
        - Chat interface → general_agent only
        - Never mix agents for same interface

        Return JSON:
        {{
            "next_node": "agent_name or agent_coordinator",
            "participating_agents": ["list", "of", "agents"],
            "is_multi_purpose": true/false,
            "is_multi_agent": true/false,
            "reasoning": "brief explanation (max {RoutingConstants.MAX_REASONING_WORDS} words)",
            "confidence": 0.0-1.0
        }}
        """

        response = await llm.ainvoke(
            analysis_prompt,
            response_format={"type": "json_object"},
            max_tokens=400,
        )

        # Handle empty or invalid responses
        if not response.content or not response.content.strip():
            raise ValueError("LLM returned empty response")

        try:
            analysis = json.loads(response.content)
            logger.debug(f"Analyze query for routing LLM response: {analysis}")
        except json.JSONDecodeError as e:
            logger.error(f"LLM returned invalid JSON: {response.content}")
            raise ValueError(f"LLM returned invalid JSON: {e}")

        # Validate and clean the analysis
        return _validate_and_clean_analysis(analysis)
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error(f"LLM analysis failed: {e}")
        raise ValueError(f"Failed to analyze query with LLM: {e}")
    except Exception as e:
        logger.error(f"Routing analysis failed: {e}")
        raise ValueError(f"Routing analysis failed: {e}")
