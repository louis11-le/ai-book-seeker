"""
Node registration functions for workflow orchestration.

This module contains functions for registering nodes in the workflow graph.
Follows LangGraph best practices for node registration.
"""

import functools
from typing import Any, Callable, Dict, List, Union

from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.workflows.agents.general import GeneralAgent
from ai_book_seeker.workflows.agents.general_voice import GeneralVoiceAgent
from ai_book_seeker.workflows.agents.sales import SalesAgent
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
from ai_book_seeker.workflows.nodes.agent_nodes import (
    agent_coordinator_node,
    format_response_node,
    supervisor_router_node,
)
from ai_book_seeker.workflows.nodes.parameter_nodes import parameter_extraction_node
from ai_book_seeker.workflows.nodes.tool_nodes import (
    book_details_tool_node,
    book_recommendation_tool_node,
    faq_tool_node,
    merge_tools_node,
)
from ai_book_seeker.workflows.utils.error_handling import handle_node_error

logger = get_logger(__name__)


def _create_node_mapping(
    node_bindings: List[tuple[str, Union[Callable, tuple[Callable, Dict[str, Any]]]]],
) -> Dict[str, Callable]:
    """
    Create a node mapping with proper dependency binding.

    This is a base function that handles the common pattern of creating
    node mappings with dependency injection using functools.partial.

    Args:
        node_bindings: List of (node_constant, handler) or (node_constant, (handler, kwargs)) tuples

    Returns:
        Dict[str, Callable]: Mapping of node constants to bound handler functions
    """
    mapping = {}

    for node_constant, handler_info in node_bindings:
        if isinstance(handler_info, tuple):
            handler, kwargs = handler_info
            # Create a copy of kwargs to avoid modifying the original
            binding_kwargs = kwargs.copy()
            # Bind with provided kwargs (no conditional logic needed)
            bound_handler = functools.partial(handler, **binding_kwargs)
        else:
            # Direct handler assignment
            bound_handler = handler_info

        mapping[node_constant] = bound_handler

    return mapping


def _register_node_batch(
    builder: Any,
    node_map: Dict[str, Callable],
    node_type: str,
) -> None:
    """
    Register a batch of nodes with consistent logging.

    Args:
        builder: LangGraph StateGraph builder instance
        node_map: Mapping of node names to handler functions
        node_type: Type of nodes being registered (e.g., "agent", "tool")
    """
    for node_name, handler in node_map.items():
        builder.add_node(node_name, handler)
        logger.debug(f"Registered {node_type} node: {node_name}")


def create_agent_node_map(llm: Any) -> Dict[str, Callable]:
    """
    Create agent node mapping for workflow registration.

    This function creates a mapping of agent node names to their handler functions,
    with proper dependency injection for the language model. It uses explicit agent
    classes for clear, maintainable agent definitions.

    Args:
        llm: Language model for agents (required)

    Returns:
        Dict[str, Callable]: Mapping of agent node names to handler functions.
            Keys are node constants (e.g., GENERAL_AGENT_NODE), values are
            callable handler functions or bound partial functions.

    Example:
        ```python
        agent_map = create_agent_node_map(llm=my_llm)
        # Returns: {
        #     'router_node': bound_router_function,
        #     'general_agent': general_agent.handle,
        #     'sales_agent': sales_agent.handle,
        #     ...
        # }
        ```

    Note:
        - Agent instances are created with only required parameters
        - Functions requiring LLM are bound using functools.partial
        - All node names use constants for consistency
    """
    # Create agent instances directly using explicit agent classes
    general_agent = GeneralAgent(llm=llm)
    general_voice_agent = GeneralVoiceAgent(llm=llm)
    sales_agent = SalesAgent(llm=llm)

    # Define node bindings with dependency injection
    agent_bindings = [
        (ROUTER_NODE, (supervisor_router_node, {"llm": llm})),
        (PARAMETER_EXTRACTION_NODE, (parameter_extraction_node, {"llm": llm})),
        (AGENT_COORDINATOR_NODE, agent_coordinator_node),
        (GENERAL_AGENT_NODE, general_agent.handle),
        (GENERAL_VOICE_AGENT_NODE, general_voice_agent.handle),
        (SALES_AGENT_NODE, sales_agent.handle),
        (FORMAT_RESPONSE_NODE, format_response_node),
        (ERROR_NODE, error_node),
    ]

    return _create_node_mapping(agent_bindings)


def create_tool_node_map(faq_service: Any, settings: Any, chromadb_service: Any) -> Dict[str, Callable]:
    """
    Create tool node mapping for workflow registration.

    This function creates a mapping of tool node names to their handler functions,
    with proper dependency injection for application settings and services. It follows
    the factory pattern for tool node creation and ensures consistent tool initialization.

    Args:
        faq_service: FAQ service instance for dependency injection
        settings: Application settings object containing configuration
        chromadb_service: ChromaDB service instance for dependency injection

    Returns:
        Dict[str, Callable]: Mapping of tool node names to handler functions.
            Keys are tool node constants (e.g., FAQ_TOOL_NODE), values are
            callable handler functions or bound partial functions.

    Example:
        ```python
        tool_map = create_tool_node_map(faq_service, app_settings, chromadb_service)
        # Returns: {
        #     'faq_tool': bound_faq_handler_function,
        #     'book_recommendation_tool': bound_book_rec_function,
        #     'book_details_tool': bound_book_details_function,
        #     ...
        # }
        ```

    Note:
        - Tool functions requiring settings or services are bound using functools.partial
        - All tool node names use constants for consistency
        - Uses the same binding pattern as create_agent_node_map
    """
    # Define tool bindings with dependency injection
    tool_bindings = [
        (FAQ_TOOL_NODE, (faq_tool_node, {"faq_service": faq_service})),
        (
            BOOK_RECOMMENDATION_TOOL_NODE,
            (book_recommendation_tool_node, {"settings": settings, "chromadb_service": chromadb_service}),
        ),
        (BOOK_DETAILS_TOOL_NODE, (book_details_tool_node, {"settings": settings})),
        (MERGE_TOOLS_NODE, merge_tools_node),
    ]

    return _create_node_mapping(tool_bindings)


def create_agent_tool_map() -> Dict[str, list[str]]:
    """
    Create agent-tool mapping for conditional edge routing.

    This function defines which tools are available to each agent, enabling
    dynamic conditional edge routing in the workflow. It serves as a single
    source of truth for agent capabilities and tool assignments.

    Returns:
        Dict[str, list[str]]: Mapping of agent nodes to available tool nodes.
            Keys are agent node constants (e.g., GENERAL_AGENT_NODE), values are
            lists of tool node constants that the agent can use.

    Example:
        ```python
        agent_tool_map = create_agent_tool_map()
        # Returns: {
        #     'general_agent': ['faq_tool', 'book_recommendation_tool'],
        #     'general_voice_agent': ['book_recommendation_tool'],
        #     'sales_agent': ['book_details_tool'],
        # }
        ```

    Note:
        - Used by edge registration for dynamic conditional edge generation
        - All node names use constants for consistency
        - Supports parallel tool execution within agents
    """
    agent_tool_config = {
        GENERAL_AGENT_NODE: [FAQ_TOOL_NODE, BOOK_RECOMMENDATION_TOOL_NODE],
        GENERAL_VOICE_AGENT_NODE: [BOOK_RECOMMENDATION_TOOL_NODE],
        SALES_AGENT_NODE: [BOOK_DETAILS_TOOL_NODE],
    }

    return agent_tool_config


def register_nodes(builder: Any, agent_node_map: Dict[str, Callable], tool_node_map: Dict[str, Callable]) -> None:
    """
    Register all nodes in the workflow graph.

    This function registers all agent and tool nodes in the LangGraph StateGraph,
    providing comprehensive logging for debugging and monitoring. It ensures
    all nodes are properly registered before edge registration.

    Args:
        builder: LangGraph StateGraph builder instance
        agent_node_map: Mapping of agent node names to handler functions
        tool_node_map: Mapping of tool node names to handler functions

    Example:
        ```python
        register_nodes(builder, agent_node_map, tool_node_map)
        # Registers all nodes and logs registration details
        ```

    Note:
        - Registers agent nodes first, then tool nodes
        - Provides debug logging for each node registration
        - Logs summary of total nodes registered
        - Must be called before edge registration
    """
    # Register all node batches using consolidated logic
    _register_node_batch(builder, agent_node_map, "agent")
    _register_node_batch(builder, tool_node_map, "tool")

    logger.info(f"Registered {len(agent_node_map)} agent nodes and {len(tool_node_map)} tool nodes")


def error_node(state: Any) -> Any:
    """
    Centralized error handling node for workflow errors.

    Completes workflow with standardized error message.

    Args:
        state: Current workflow state

    Returns:
        Command: Error command completing the workflow
    """
    return handle_node_error(
        error=Exception("Workflow execution error"),
        node_name="error_node",
        state=state,
        custom_content="An error occurred during workflow execution.",
    )
