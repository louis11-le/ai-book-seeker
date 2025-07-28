"""
Edge registration for workflow orchestration.

This module provides modular edge registration for LangGraph workflows with
support for parallel execution, conditional routing, and comprehensive error handling.

Key Features:
- Modular edge group organization for maintainability
- Conditional edge routing for parallel execution
- Comprehensive error handling coverage
- Dynamic agent-tool mapping integration
- Clean and focused edge registration

Architecture:
- Standard edges: Direct node-to-node connections
- Conditional edges: Dynamic routing based on state
- Error edges: Comprehensive error handling coverage
- Parallel execution: Multi-agent and multi-tool parallelism

Usage:
    ```python
    from ai_book_seeker.workflows.registration.edge_registration import register_edges

    # Define edge groups
    edge_groups = [
        entrypoint_edges(),
        router_to_agent_edges(),
        tool_to_merge_edges(),
        error_edges(),
        merge_to_format_end_edges(),
    ]

    # Register all edges
    register_edges(builder, edge_groups)
    ```
"""

from typing import Any, Callable, Dict, List, Tuple

from langgraph.graph import END, START

from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.workflows.constants import (
    AGENT_COORDINATOR_NODE,
    BOOK_DETAILS_TOOL_NODE,
    BOOK_RECOMMENDATION_TOOL_NODE,
    ERROR_NODE,
    FAQ_TOOL_NODE,
    FORMAT_RESPONSE_NODE,
    GENERAL_AGENT_NODE,
    GENERAL_VOICE_AGENT_NODE,
    MERGE_TOOLS_NODE,
    PARAMETER_EXTRACTION_NODE,
    ROUTER_NODE,
    SALES_AGENT_NODE,
)
from ai_book_seeker.workflows.registration.node_registration import create_agent_tool_map
from ai_book_seeker.workflows.schemas.state import AgentState

logger = get_logger(__name__)


def _create_edge_list(*edges: Tuple[str, str]) -> List[Tuple[str, str]]:
    """Create a list of edges from tuples with consistent formatting."""
    return list(edges)


def _create_error_edges_from_nodes(*nodes: str) -> List[Tuple[str, str]]:
    """Create error edges from multiple nodes to ERROR_NODE."""
    return [(node, ERROR_NODE) for node in nodes]


def _safe_routing_targets(routing_logic: Callable[[AgentState], str], state: AgentState, context: str) -> str:
    try:
        result = routing_logic(state)
        logger.debug(f"[RoutingSafe][{context}] Returned: {result}")
        return result
    except Exception as e:
        logger.exception(f"[RoutingSafe][{context}] Exception: {e}")
        return "error"


def _create_conditional_edge_with_error_fallback(
    builder: Any,
    source_node: str,
    routing_function: Callable[[AgentState], str],
    target_mapping: Dict[str, str],
    context: str,
) -> None:
    """
    Create conditional edge with standardized error fallback.

    Provides a consistent pattern for all conditional edge registrations
    with proper error handling and logging.

    Args:
        builder: LangGraph StateGraph builder instance
        source_node: Source node for the conditional edge
        routing_function: Function that determines routing targets
        target_mapping: Mapping of routing keys to target nodes
        context: Context string for logging
    """
    logger.debug(f"Registering {context} conditional edges with error fallback")
    builder.add_conditional_edges(
        source_node,
        lambda state: _safe_routing_targets(routing_function, state, context),
        target_mapping,
    )


def entrypoint_edges() -> List[Tuple[str, str]]:
    """
    Define entrypoint edges for the workflow.

    Routes from workflow start to the router node for initial query analysis.

    Returns:
        List[Tuple[str, str]]: List of (from_node, to_node) edge tuples.
    """
    return _create_edge_list((START, ROUTER_NODE))


def router_to_agent_edges() -> List[Tuple[str, str]]:
    """
    Define edges from router to parameter extraction.

    Routes from router node to parameter extraction for comprehensive
    parameter analysis before agent selection.

    Returns:
        List[Tuple[str, str]]: List of (from_node, to_node) edge tuples.
    """
    return _create_edge_list((ROUTER_NODE, PARAMETER_EXTRACTION_NODE))


def tool_to_merge_edges() -> List[Tuple[str, str]]:
    """
    Define edges from tools to merge node.

    Routes from all tool nodes to the merge node for result aggregation
    and streaming response preparation.

    Returns:
        List[Tuple[str, str]]: List of (from_node, to_node) edge tuples.
    """
    return _create_edge_list(
        (FAQ_TOOL_NODE, MERGE_TOOLS_NODE),
        (BOOK_RECOMMENDATION_TOOL_NODE, MERGE_TOOLS_NODE),
        (BOOK_DETAILS_TOOL_NODE, MERGE_TOOLS_NODE),
    )


def error_edges() -> List[Tuple[str, str]]:
    """
    Define error handling edges.

    Routes from critical nodes to the error node for comprehensive error handling
    and graceful degradation. Only nodes that can actually fail and need error
    protection are included. Nodes with internal error handling or conditional
    edge routing are excluded to prevent conflicts.

    Returns:
        List[Tuple[str, str]]: List of (from_node, to_node) edge tuples.
    """
    # No nodes need static error edges - all use conditional edge routing
    # or internal error handling
    return []


def merge_to_format_end_edges() -> List[Tuple[str, str]]:
    """
    Define edges from merge to format and end.

    Routes from merge node to format response and then to workflow end.
    Error node should not route to END since it's a finish point.

    Returns:
        List[Tuple[str, str]]: List of (from_node, to_node) edge tuples.
    """
    return _create_edge_list(
        (MERGE_TOOLS_NODE, FORMAT_RESPONSE_NODE),
        (FORMAT_RESPONSE_NODE, END),
    )


def _register_standard_edges(builder: Any, edge_groups: List[List[Tuple[str, str]]]) -> None:
    """Register standard edges in the workflow graph with proper logging."""
    logger.debug("Registering standard edges")
    for edge_list in edge_groups:
        for from_node, to_node in edge_list:
            builder.add_edge(from_node, to_node)
            logger.debug(f"Registered edge: {from_node} -> {to_node}")


def _register_conditional_edges(builder: Any) -> None:
    """
    Register conditional edges for parallel execution with enhanced fallback logic.

    Registers dynamic conditional edges that enable parallel agent and tool execution
    based on state analysis and agent-tool mapping. Includes proper error fallback
    and follows LangGraph best practices for explicit, deterministic routing.

    Args:
        builder: LangGraph StateGraph builder instance

    Raises:
        RuntimeError: If conditional edge registration fails
    """
    # Add basic workflow progression conditional edge
    builder.add_conditional_edges(
        ROUTER_NODE,
        lambda state: _get_router_routing_targets(state),  # Check if routing analysis exists
        {
            "parameter_extraction": PARAMETER_EXTRACTION_NODE,
            "error": ERROR_NODE,  # Route to error if analysis failed
        },
    )
    logger.debug(f"Registered conditional edge: {ROUTER_NODE} -> {PARAMETER_EXTRACTION_NODE} or {ERROR_NODE}")

    # Get agent-tool mapping for dynamic edge generation
    agent_tool_map = create_agent_tool_map()

    # Parameter Extraction Conditional Routing
    _create_conditional_edge_with_error_fallback(
        builder,
        PARAMETER_EXTRACTION_NODE,
        _get_parameter_extraction_routing_targets,
        {
            "general_agent": GENERAL_AGENT_NODE,
            "general_voice_agent": GENERAL_VOICE_AGENT_NODE,
            "sales_agent": SALES_AGENT_NODE,
            "agent_coordinator": AGENT_COORDINATOR_NODE,
            "error": ERROR_NODE,
        },
        "parameter extraction",
    )

    # Multi-Agent Parallel Execution
    _create_conditional_edge_with_error_fallback(
        builder,
        AGENT_COORDINATOR_NODE,
        _get_agent_routing_targets,
        {
            "general_agent": GENERAL_AGENT_NODE,
            "general_voice_agent": GENERAL_VOICE_AGENT_NODE,
            "sales_agent": SALES_AGENT_NODE,
            "error": ERROR_NODE,
        },
        "multi-agent parallel execution",
    )

    # Agent-to-Tool Parallel Execution
    logger.debug("Registering agent-to-tool conditional edges with enhanced error handling")
    for agent_node, available_tools in agent_tool_map.items():
        logger.debug(f"Registering conditional edges for {agent_node} with tools: {available_tools}")

        if agent_node == GENERAL_AGENT_NODE:  # Multi-tool agent
            builder.add_conditional_edges(
                agent_node,
                lambda state, tools=available_tools: _get_agent_tool_routing_targets(state, tools),
                {tool: tool for tool in available_tools} | {"error": ERROR_NODE},
            )
            logger.debug(f"Registered multi-tool conditional edges for {agent_node}")
        else:  # Single-tool agents (GeneralVoiceAgent, SalesAgent)
            for tool in available_tools:
                builder.add_conditional_edges(
                    agent_node,
                    lambda state, tool_name=tool: tool_name if _should_use_tool(state, tool_name) else "error",
                    {tool: tool, "error": ERROR_NODE},
                )
                logger.debug(f"Registered single-tool conditional edge for {agent_node} -> {tool}")

    logger.info("Successfully registered conditional edges for parallel execution with error fallback")


def _get_parameter_extraction_routing_targets(state: AgentState) -> str:
    """
    Determine parameter extraction routing targets with enhanced error fallback logic.

    Returns deterministic routing targets or error fallback if no routing analysis.
    Follows LangGraph best practices for explicit, deterministic routing.

    Args:
        state: Current workflow state

    Returns:
        str: Routing target node name or "error" for fallback
    """
    # Primary routing logic
    if state.shared_data.routing_analysis:
        next_node = state.shared_data.routing_analysis.next_node
        logger.debug(f"[Routing][parameter_extraction] next_node: {next_node}")
        logger.debug(
            f"[Routing][parameter_extraction] constants: {[GENERAL_AGENT_NODE, GENERAL_VOICE_AGENT_NODE, SALES_AGENT_NODE, AGENT_COORDINATOR_NODE]}"
        )
        if next_node in {GENERAL_AGENT_NODE, GENERAL_VOICE_AGENT_NODE, SALES_AGENT_NODE, AGENT_COORDINATOR_NODE}:
            logger.debug(f"Routing to next node: {next_node}")
            return next_node

    # Fallback: route to error if no specific routing identified
    logger.error("No routing analysis available - routing to error node")
    return "error"


def _get_router_routing_targets(state: AgentState) -> str:
    """
    Determine router routing targets with enhanced error fallback logic.

    Returns parameter_extraction if routing analysis exists, or error if it doesn't.
    Follows LangGraph best practices for explicit, deterministic routing.

    Args:
        state: Current workflow state

    Returns:
        str: "parameter_extraction" if routing analysis exists, "error" otherwise
    """
    # Check if routing analysis exists
    if state.shared_data.routing_analysis:
        logger.debug("[Routing][router] Routing analysis exists, continuing to parameter_extraction")
        return "parameter_extraction"

    # No routing analysis - route to error
    logger.error("No routing analysis available - routing to error node")
    return "error"


def _get_agent_routing_targets(state: AgentState) -> List[str]:
    """
    Determine agent routing targets for parallel execution with enhanced error fallback logic.

    Returns all participating agents for parallel execution or error fallback if no agents identified.
    Follows LangGraph best practices for explicit, deterministic parallel routing.

    Args:
        state: Current workflow state

    Returns:
        List[str]: List of agent routing target node names or ["error"] for fallback
    """
    # Primary routing logic
    participating_agents = state.shared_data.participating_agents_for_parallel
    if participating_agents and len(participating_agents) > 0:
        logger.debug(f"Routing to participating agents in parallel: {participating_agents}")
        return participating_agents

    # Fallback: route to error if no specific agents identified
    logger.warning("No participating agents identified - routing to error node")
    return ["error"]


def _should_use_tool(state: AgentState, tool_name: str) -> bool:
    """
    Determine if a specific tool should be used based on state analysis.

    Args:
        state: Current workflow state
        tool_name: Name of the tool to check

    Returns:
        bool: True if tool should be used, False otherwise
    """
    try:
        # Check selected tools for parallel execution
        selected_tools = state.shared_data.selected_tools_for_parallel
        if selected_tools and tool_name in selected_tools:
            logger.debug(f"Tool {tool_name} selected for parallel execution")
            return True

        # Check agent insights for tool selection
        agent_insights = state.shared_data.agent_insights
        if agent_insights:
            for insight in agent_insights:
                if tool_name in insight.selected_tools:
                    logger.debug(f"Tool {tool_name} selected by agent insight")
                    return True

        # Default: use the tool if no specific selection logic
        logger.debug(f"Tool {tool_name} not explicitly selected, using default behavior")
        return True

    except Exception as e:
        logger.error(f"Error checking tool usage for {tool_name}: {e}")
        return False  # Don't use tool on error


def _get_agent_tool_routing_targets(state: AgentState, available_tools: List[str]) -> list:
    """
    Determine agent-to-tool routing targets with enhanced error fallback logic.

    Returns deterministic routing targets or error fallback if no tools identified.
    Follows LangGraph best practices for explicit, deterministic routing.

    Args:
        state: Current workflow state
        available_tools: List of tools available to the agent

    Returns:
        list: List of routing target node names or ["error"] for fallback
    """
    logger.debug(f"Agent-tool routing: available tools = {available_tools}")

    # Primary routing logic
    selected_tools = state.shared_data.selected_tools_for_parallel or []
    if selected_tools and len(selected_tools) > 0:
        logger.debug(f"Agent-tool routing: selected tools = {selected_tools}")

        # Intersect selected tools with available tools for this agent
        valid_tools = [tool for tool in selected_tools if tool in available_tools]
        if valid_tools:
            logger.info(f"Agent-tool routing: routing to valid tools = {valid_tools}")
            # Return all valid tools for parallel routing
            return valid_tools
        else:
            logger.warning(
                f"Agent-tool routing: no valid tools found. Selected: {selected_tools}, Available: {available_tools}"
            )
    else:
        logger.warning("Agent-tool routing: no selected tools found in state")

    # Fallback: route to error if no specific tools identified
    logger.error("Agent-tool routing: no valid tools identified - routing to error node")
    return ["error"]


def register_edges(builder: Any, edge_groups: List[List[Tuple[str, str]]]) -> None:
    """
    Register all edges in the workflow graph using pure conditional edge system.

    Registers static edges for non-dynamic routing and conditional edges for all
    dynamic routing scenarios. Follows LangGraph best practices for explicit,
    deterministic routing with proper error fallback.

    Args:
        builder: LangGraph StateGraph builder instance
        edge_groups: List of edge group functions returning edge lists

    Raises:
        ValueError: If edge registration fails
        RuntimeError: If conditional edge registration fails

    Example:
        ```python
        edge_groups = [
            entrypoint_edges(),
            router_to_agent_edges(),
            # ... other edge groups
        ]
        register_edges(builder, edge_groups)
        ```
    """
    try:
        # Register static edges (no conflicts with conditional edges)
        _register_standard_edges(builder, edge_groups)

        # Register conditional edges for all dynamic routing scenarios
        logger.debug("Registering conditional edges for dynamic routing with error fallback")
        _register_conditional_edges(builder)

        logger.info("Successfully registered all workflow edges using pure conditional edge system")

    except Exception as e:
        logger.error(f"Failed to register edges: {e}")
        raise ValueError(f"Edge registration failed: {e}") from e
