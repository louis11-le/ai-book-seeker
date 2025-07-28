"""
Agent nodes for workflow orchestration.

This module contains agent node functions for the LangGraph workflow.
Follows LangGraph best practices for agent node implementation.

Key Components:
- supervisor_router_node: Analyzes queries and determines routing strategy
- agent_coordinator_node: Coordinates multi-agent parallel execution
- format_response_node: Formats final responses for user consumption

Architecture:
- LLM-powered intelligent routing with confidence scoring
- Multi-agent parallel execution with conditional edge routing
- Streaming-first response formatting with comprehensive error handling
- State management optimization with performance tracking
"""

from typing import Any, List, Optional

from langgraph.types import Command

from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.workflows.constants import (
    AGENT_COORDINATOR_NODE,
    FORMAT_RESPONSE_NODE,
    GENERAL_AGENT_NODE,
    GENERAL_VOICE_AGENT_NODE,
    PARAMETER_EXTRACTION_NODE,
    ROUTER_NODE,
    SALES_AGENT_NODE,
)
from ai_book_seeker.workflows.routing.analysis import analyze_query_for_routing
from ai_book_seeker.workflows.schemas import AgentState
from ai_book_seeker.workflows.schemas.routing import RoutingAnalysis, RoutingConstants
from ai_book_seeker.workflows.utils.error_handling import create_error_message, handle_node_error
from ai_book_seeker.workflows.utils.message_factory import (
    create_coordination_message,
    create_routing_message,
    create_system_message,
)
from ai_book_seeker.workflows.utils.node_utils import create_command, validate_input_state

logger = get_logger(__name__)

# Constants for result extraction (scoped to this module)
RESULT_TEXT_FIELDS = ["text", "answer", "content", "response"]
RESULT_DICT_FIELDS = ["text", "answer", "content", "response", "message"]

# Valid agent nodes for routing validation
VALID_AGENT_NODES = [GENERAL_AGENT_NODE, GENERAL_VOICE_AGENT_NODE, SALES_AGENT_NODE]


def _validate_routing_analysis(state: AgentState, trace_id: str, node_name: str) -> Optional[Command]:
    """
    Validate routing analysis with standardized error handling.

    Args:
        state: Current workflow state
        trace_id: Trace ID for logging
        node_name: Name of the node for error context

    Returns:
        Optional[Command]: Error command if validation fails, None if valid
    """
    if not state.shared_data.routing_analysis:
        logger.error(f"[{node_name}][{trace_id}] No routing analysis found")
        error_msg = create_error_message(ValueError("No routing analysis found"), node_name, trace_id)
        return Command(update={"messages": [error_msg]})

    return None


def _extract_participating_agents(state: AgentState, trace_id: str, node_name: str) -> Optional[List[str]]:
    """
    Extract and validate participating agents with standardized error handling.

    Args:
        state: Current workflow state
        trace_id: Trace ID for logging
        node_name: Name of the node for error context

    Returns:
        Optional[List[str]]: List of participating agents or None if validation fails
    """
    participating_agents = state.shared_data.routing_analysis.participating_agents or []
    if not participating_agents:
        logger.warning(f"[{node_name}][{trace_id}] No participating agents found")
        return None

    return participating_agents


async def supervisor_router_node(state: AgentState, llm) -> Command:
    """
    Supervisor router node for intelligent query routing.

    Analyzes user queries and determines the optimal routing strategy
    for multi-agent parallel execution or single-agent handling.

    Args:
        state: Current workflow state containing messages and shared data
        llm: Language model for query analysis (required - no fallback)

    Returns:
        Command: Next step in workflow with routing decision

    Note:
        LLM is required for routing analysis. No fallback mechanism - system fails
        gracefully when LLM is unavailable.

    Example:
        ```python
        # Routes to parameter extraction or specific agents based on analysis
        command = await supervisor_router_node(state, llm)
        # Returns: Command(goto="parameter_extraction" or "general_agent", etc.)
        ```
    """
    trace_id = state.session_id
    logger.info(f"[{ROUTER_NODE}][{trace_id}] Analyzing query for routing")

    try:
        # Validate input state
        error_cmd = validate_input_state(state, ROUTER_NODE)
        if error_cmd:
            return error_cmd

        query = state.messages[-1].content
        # LLM-based analysis is required for routing (no fallback)
        analysis = await analyze_query_for_routing(query, llm, state.interface)
        if not analysis:
            logger.error(f"[{ROUTER_NODE}][{trace_id}] No analysis result")
            error_msg = create_error_message(ValueError("No analysis result"), ROUTER_NODE, trace_id)
            return Command(update={"messages": [error_msg]})

        # Create routing analysis object
        try:
            routing_analysis = RoutingAnalysis(
                next_node=analysis.get("next_node", PARAMETER_EXTRACTION_NODE),
                participating_agents=analysis.get("participating_agents", []),
                is_multi_purpose=analysis.get("is_multi_purpose", False),
                is_multi_agent=analysis.get("is_multi_agent", False),
                query_intents=analysis.get("query_intents", {}),
                reasoning=analysis.get("reasoning", ""),
                confidence=analysis.get("confidence", RoutingConstants.DEFAULT_CONFIDENCE),
            )
        except Exception as e:
            logger.error(f"[{ROUTER_NODE}][{trace_id}] Error creating RoutingAnalysis: {e}")
            error_msg = create_error_message(e, ROUTER_NODE, trace_id)
            return Command(update={"messages": [error_msg]})

        # Update state with routing analysis
        state.shared_data.routing_analysis = routing_analysis

        # Create routing message using utility
        router_msg = create_routing_message(
            next_node=routing_analysis.next_node or PARAMETER_EXTRACTION_NODE,
            participating_agents=routing_analysis.participating_agents,
            confidence=routing_analysis.confidence,
            session_id=state.session_id,
        )

        return create_command(messages=[router_msg], state=state, metric_name=ROUTER_NODE)
    except Exception as e:
        return handle_node_error(e, ROUTER_NODE, state)


async def agent_coordinator_node(state: AgentState) -> Command:
    """
    Agent coordinator node for multi-agent parallel execution.

    Coordinates parallel execution of multiple agents based on
    routing analysis and query complexity.

    Args:
        state: Current workflow state containing routing analysis and shared data

    Returns:
        Command: Next step in workflow with coordination decision

    Example:
        ```python
        # Coordinates parallel execution of multiple agents
        command = await agent_coordinator_node(state)
        # Returns: Command(goto="merge_tools" or specific agent node)
        ```
    """
    trace_id = state.session_id
    logger.info(f"[{AGENT_COORDINATOR_NODE}][{trace_id}] Coordinating multi-agent execution")

    try:
        # Validate routing analysis
        error_cmd = _validate_routing_analysis(state, trace_id, AGENT_COORDINATOR_NODE)
        if error_cmd:
            return error_cmd

        # Extract and validate participating agents
        participating_agents = _extract_participating_agents(state, trace_id, AGENT_COORDINATOR_NODE)
        if not participating_agents:
            error_msg = create_error_message(
                ValueError("No participating agents found"), AGENT_COORDINATOR_NODE, trace_id
            )
            return Command(update={"messages": [error_msg]})

        logger.info(
            f"[{AGENT_COORDINATOR_NODE}][{trace_id}] Coordinating {len(participating_agents)} agents: {participating_agents}"
        )

        # Update state for parallel execution
        state.shared_data.participating_agents_for_parallel = participating_agents

        # Create coordination message using utility
        coord_msg = create_coordination_message(
            participating_agents=participating_agents,
            intent_summary=[],  # Could be enhanced with intent summary
            session_id=state.session_id,
        )

        # Let conditional edges handle routing decisions
        # No goto parameter - conditional edges will determine next node
        return create_command(messages=[coord_msg], state=state, metric_name=AGENT_COORDINATOR_NODE)

    except Exception as e:
        return handle_node_error(e, AGENT_COORDINATOR_NODE, state)


def format_response_node(state: AgentState) -> Command:
    """
    Format response node for final response preparation.

    Formats and finalizes the workflow response for user consumption.
    Extracts and combines results from multiple tools and agents.

    Args:
        state: Current workflow state containing agent results and shared data

    Returns:
        Command: End of workflow with formatted response

    Example:
        ```python
        # Formats final response from all tool results
        command = format_response_node(state)
        # Returns: Command(goto=END_NODE, update={"messages": [formatted_response]})
        ```
    """
    trace_id = state.session_id
    logger.info(f"[{FORMAT_RESPONSE_NODE}][{trace_id}] Formatting final response")

    try:
        # Define result types and their handlers
        result_types = [
            ("faq", "FAQ"),
            ("book_recommendation", "Book Recommendation"),
            ("book_details", "Book Details"),
        ]

        response_parts = []
        for attr_name, display_name in result_types:
            result = getattr(state.agent_results, attr_name, None)
            if result:
                response_parts.append(_extract_result_text(result, trace_id, display_name))

        # Combine responses
        final_response = "\n\n".join(response_parts) if response_parts else "No results available."

        # Create final response message using utility
        final_msg = create_system_message(
            content=final_response,
            node_name=FORMAT_RESPONSE_NODE,
            session_id=state.session_id,
            message_type="final_response",
            additional_kwargs={
                "results_count": len(response_parts),
                "has_faq": state.agent_results.faq is not None,
                "has_book_recommendation": state.agent_results.book_recommendation is not None,
                "has_book_details": state.agent_results.book_details is not None,
            },
        )

        return create_command(messages=[final_msg], state=state, metric_name=FORMAT_RESPONSE_NODE)
    except Exception as e:
        return handle_node_error(e, FORMAT_RESPONSE_NODE, state)


def _extract_result_text(result: Any, trace_id: str, result_type: str) -> str:
    """
    Extract text from result object with standardized schema handling.

    Provides robust text extraction from various result formats including
    objects, dictionaries, and error cases with comprehensive fallbacks.

    Args:
        result: Result object to extract text from
        trace_id: Trace ID for logging
        result_type: Type of result for logging

    Returns:
        str: Extracted text or error message

    Example:
        ```python
        text = _extract_result_text(result_obj, "session_123", "FAQ")
        # Returns: "FAQ answer text" or "FAQ: No result available"
        ```
    """
    if not result:
        return f"{result_type}: No result available"

    try:
        # Try common text fields on object
        for field in RESULT_TEXT_FIELDS:
            if hasattr(result, field) and getattr(result, field):
                return getattr(result, field)

        # Try dictionary access
        if isinstance(result, dict):
            for field in RESULT_DICT_FIELDS:
                if field in result and result[field]:
                    return result[field]

            # Handle error cases
            if "error" in result:
                return result.get("message", "Error occurred")

        # Fallback to string representation
        return str(result)

    except Exception as e:
        logger.error(f"[FormatResponse][{trace_id}] Error extracting {result_type} text: {e}")
        return f"{result_type}: Error processing response"
