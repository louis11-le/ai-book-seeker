"""
Modular workflow orchestrator for AI Book Seeker.

This module provides a clean, modular implementation of the LangGraph workflow orchestrator.
Follows industry best practices and context7 standards for LangGraph orchestration.

The orchestrator implements a streaming-first, parallel execution pattern with:
- Intelligent query routing and agent coordination
- Multi-agent and multi-tool parallel execution
- Robust error handling and recovery mechanisms
- Optimized state management and memory usage
- Comprehensive logging and monitoring

Key Features:
- LLM-powered query analysis (LLM required)
- Dynamic agent and tool selection based on query intent
- Conditional edge routing for parallel execution
- Structured response formatting and error handling
- Memory-efficient state management with automatic cleanup
"""

from typing import Any

from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph

from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.workflows.registration.edge_registration import (
    entrypoint_edges,
    error_edges,
    merge_to_format_end_edges,
    register_edges,
    router_to_agent_edges,
    tool_to_merge_edges,
)
from ai_book_seeker.workflows.registration.node_registration import (
    create_agent_node_map,
    create_tool_node_map,
    register_nodes,
)
from ai_book_seeker.workflows.schemas import AgentState

logger = get_logger(__name__)

# Workflow configuration constants
WORKFLOW_ENTRY_POINT = "router_node"  # The first node after START
WORKFLOW_EXIT_POINT = "format_response"  # The last node before END


async def get_orchestrator(app: Any) -> StateGraph:
    """
    Create and configure the LangGraph workflow orchestrator.

    This function orchestrates the complete workflow setup including:
    - LLM initialization with application configuration
    - State graph creation and configuration
    - Node and edge registration for all workflow components
    - Conditional edge setup for parallel execution
    - Memory management and checkpointing configuration

    The orchestrator implements a streaming-first pattern where:
    - Tools execute in parallel using conditional edge routing
    - Results are streamed as soon as they complete
    - No blocking occurs at merge nodes
    - Comprehensive error handling ensures graceful degradation

    Args:
        app: FastAPI application instance containing configuration and state

    Returns:
        CompiledStateGraph: Fully configured and compiled LangGraph workflow

    Raises:
        ValueError: If required configuration is missing
        RuntimeError: If workflow compilation fails

    Example:
        ```python
        # In FastAPI route
        orchestrator = await get_orchestrator(request.app)
        result = await orchestrator.ainvoke(initial_state)
        ```
    """
    logger.info("Creating modular workflow orchestrator")

    try:
        # Validate application configuration
        if not hasattr(app, "state") or not hasattr(app.state, "config"):
            raise ValueError("Application missing required configuration state")

        config = app.state.config
        if not hasattr(config, "openai"):
            raise ValueError("Missing OpenAI configuration")

        # Initialize LLM with application configuration
        logger.debug("Initializing LLM with application configuration")
        llm = init_chat_model(
            model=config.openai.model,
            temperature=config.openai.temperature,
            openai_api_key=config.openai.api_key.get_secret_value(),
        )
        if not llm:
            raise ValueError("LLM is required for workflow initialization")

        logger.debug(f"LLM initialized with model: {config.openai.model}")

        # Create state graph with AgentState schema
        logger.debug("Creating StateGraph with AgentState schema")
        builder = StateGraph(AgentState)

        # Create node mappings for agents and tools
        logger.debug("Creating agent and tool node mappings")

        # Get FAQ service from app state for dependency injection
        faq_service = getattr(app.state, "faq_service", None)
        if not faq_service:
            raise ValueError("FAQ service not available in application state")

        # Get ChromaDB service from app state for dependency injection
        chromadb_service = getattr(app.state, "chromadb_service", None)
        if not chromadb_service:
            raise ValueError("ChromaDB service not available in application state")

        agent_node_map = create_agent_node_map(llm=llm)
        tool_node_map = create_tool_node_map(faq_service, config, chromadb_service)

        # Register all nodes in the workflow graph
        logger.debug("Registering nodes in workflow graph")
        register_nodes(builder, agent_node_map, tool_node_map)

        # Define edge groups for workflow routing
        logger.debug("Defining edge groups for workflow routing")
        edge_groups = [
            entrypoint_edges(),
            router_to_agent_edges(),
            tool_to_merge_edges(),
            error_edges(),
            merge_to_format_end_edges(),
        ]

        # Register all edges including conditional edges for parallel execution
        logger.debug("Registering edges and conditional edges")
        register_edges(builder, edge_groups)

        # Configure workflow entry and exit points
        logger.debug(f"Setting workflow entry point: {WORKFLOW_ENTRY_POINT}")
        builder.set_entry_point(WORKFLOW_ENTRY_POINT)

        logger.debug(f"Setting workflow exit point: {WORKFLOW_EXIT_POINT}")
        builder.set_finish_point(WORKFLOW_EXIT_POINT)

        # Configure memory management and checkpointing
        logger.debug("Configuring memory management with MemorySaver")
        checkpointer = MemorySaver()

        # Compile the workflow graph
        logger.debug("Compiling workflow graph")
        workflow = builder.compile(checkpointer=checkpointer)

        logger.info("Modular workflow orchestrator created successfully")
        logger.debug(f"Workflow compiled with {len(agent_node_map)} agent nodes and {len(tool_node_map)} tool nodes")

        return workflow

    except ValueError as e:
        logger.error(f"Configuration error in orchestrator creation: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in orchestrator creation: {e}")
        raise RuntimeError(f"Failed to create workflow orchestrator: {e}") from e
