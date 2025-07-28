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
from ai_book_seeker.workflows.routing.parameter_extraction import _safe_float, _safe_int
from ai_book_seeker.workflows.schemas.routing import RoutingConstants

logger = get_logger(__name__)


def _clean_criteria_data_types(criteria: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean and convert criteria data types to match schema expectations.

    Args:
        criteria: Raw criteria dictionary from LLM

    Returns:
        Dict[str, Any]: Cleaned criteria with proper data types
    """
    cleaned = criteria.copy()

    # Convert age to integer using existing _safe_int function
    if "age" in cleaned and cleaned["age"] is not None:
        cleaned["age"] = _safe_int(cleaned["age"])

    # Convert budget to float using existing _safe_float function
    if "budget" in cleaned and cleaned["budget"] is not None:
        cleaned["budget"] = _safe_float(cleaned["budget"])

    return cleaned


def _clean_sales_details_data_types(sales_details: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean and convert sales details data types to match schema expectations.

    Args:
        sales_details: Raw sales details dictionary from LLM

    Returns:
        Dict[str, Any]: Cleaned sales details with proper data types
    """
    cleaned = sales_details.copy()

    # Convert budget to float using existing _safe_float function
    if "budget" in cleaned and cleaned["budget"] is not None:
        cleaned["budget"] = _safe_float(cleaned["budget"])

    return cleaned


def _clean_query_intents_data_types(query_intents: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean and convert query intents data types to match schema expectations.

    Args:
        query_intents: Raw query intents dictionary from LLM

    Returns:
        Dict[str, Any]: Cleaned query intents with proper data types
    """
    cleaned = query_intents.copy()

    # Clean book recommendations criteria
    if "book_recommendations" in cleaned:
        for rec in cleaned["book_recommendations"]:
            if "criteria" in rec:
                rec["criteria"] = _clean_criteria_data_types(rec["criteria"])

    # Clean sales requests details
    if "sales_requests" in cleaned:
        for sale in cleaned["sales_requests"]:
            if "sales_details" in sale:
                sale["sales_details"] = _clean_sales_details_data_types(sale["sales_details"])

    return cleaned


def _validate_confidence(confidence: float) -> float:
    """
    Validate and normalize confidence value.

    Args:
        confidence: Raw confidence value from LLM

    Returns:
        float: Normalized confidence value within bounds
    """
    return max(RoutingConstants.MIN_CONFIDENCE, min(RoutingConstants.MAX_CONFIDENCE, confidence))


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

    # Clean query intents data types
    query_intents = analysis.get("query_intents", {})
    cleaned_query_intents = _clean_query_intents_data_types(query_intents)

    return {
        "next_node": next_node,
        "participating_agents": analysis.get("participating_agents", []),
        "is_multi_purpose": analysis.get("is_multi_purpose", False),
        "is_multi_agent": analysis.get("is_multi_agent", False),
        "query_intents": cleaned_query_intents,
        "reasoning": analysis.get("reasoning", ""),
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
            - query_intents: Categorized query intents
            - reasoning: Explanation of routing decision
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
        #     "query_intents": {...},
        #     "reasoning": "Query requires book recommendations",
        #     "confidence": 0.85
        # }
        ```

    Note:
        LLM is required for routing analysis. No fallback mechanism - system fails
        gracefully when LLM is unavailable or returns incomplete analysis.
        The 'next_node' field is REQUIRED and must be provided by the LLM.
        Interface-aware routing ensures voice queries use general_voice_agent and
        chat queries use general_agent.
    """
    try:
        # Use LLM for sophisticated analysis (required - no fallback)
        analysis_prompt = f"""
        Analyze the following user query and determine the appropriate routing.

        Query: "{query}"
        Interface: {interface}

        Determine:
        1. Which agent(s) should handle this query
        2. Whether this is a multi-agent or single-agent query
        3. Whether this is a multi-purpose or single-purpose query
        4. The confidence level of your analysis

        Return a JSON object with the following structure:
        {{
            "next_node": "agent_name or agent_coordinator",
            "participating_agents": ["list", "of", "agents"],
            "is_multi_purpose": true/false,
            "is_multi_agent": true/false,
            "query_intents": {{
                "faq_requests": [{{"intent": "...", "question": "...", "category": "...", "priority": 1}}],
                "book_recommendations": [{{
                    "intent": "...",
                    "criteria": {{
                        "age": 16,  # Single age (integer) - use null for age ranges
                        "age_from": 1,  # Start of age range (integer) - use null for single ages
                        "age_to": 6,  # End of age range (integer) - use null for single ages
                        "budget": 15.0,  # Must be float (not "15$" or "15")
                        "genre": "adventure"  # Must be string
                    }},
                    "category": "...",
                    "priority": 1
                }}],
                "product_inquiries": [{{"intent": "...", "product_details": {{}}, "category": "...", "priority": 1}}],
                "sales_requests": [{{
                    "intent": "...",
                    "sales_details": {{
                        "budget": 15.0  # Must be float (not "15$" or "15")
                    }},
                    "category": "...",
                    "priority": 1
                }}]
            }},
            "reasoning": "explanation of routing decision",
            "confidence": 0.0-1.0
        }}

        IMPORTANT: For numeric fields, use proper JSON types:
        - age: integer (e.g., 16, not "16+" or "16+")
        - budget: float (e.g., 15.0, not "15$" or "15")
        - price: float (e.g., 12.99, not "12.99$")

        AGE RANGE HANDLING:
        - For single ages: Set "age" field, leave "age_from" and "age_to" as null
          Examples: "for a 10-year-old" → age: 10, age_from: null, age_to: null
        - For age ranges: Set "age_from" and "age_to", leave "age" as null
          Examples:
          * "between 1 and 6" → age: null, age_from: 1, age_to: 6
          * "ages 1-6" → age: null, age_from: 1, age_to: 6
          * "1 to 6 years old" → age: null, age_from: 1, age_to: 6
          * "for children 1-6" → age: null, age_from: 1, age_to: 6

        Available agents:
        - general_agent: Handles FAQ, book recommendations, general customer support (CHAT INTERFACE ONLY)
        - general_voice_agent: Handles voice interface queries and book recommendations (VOICE INTERFACE ONLY)

        INTERFACE-SPECIFIC ROUTING RULES:
        - For voice interface: Use general_voice_agent only
        - For chat interface: Use general_agent only
        - Never select both agents for the same interface
        - Never select general_agent for voice interface
        - Never select general_voice_agent for chat interface

        Available tools:
        - faq_tool: For FAQ and customer service questions
        - book_recommendation_tool: For book recommendations based on criteria
        - book_details_tool: For specific book information and availability

        Guidelines:
        - Use "agent_coordinator" for multi-agent queries
        - Use specific agent names for single-agent queries
        - Set confidence between 0.0 and 1.0
        - Provide clear reasoning for routing decisions
        - Always respect interface-specific agent selection rules
        """

        response = await llm.ainvoke(analysis_prompt, response_format={"type": "json_object"})

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
