"""
Tool node functions for workflow orchestration.

This module contains tool node functions that execute business logic.
Follows LangGraph best practices for tool node implementation.
"""

import time
from typing import Any

from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.workflows.constants import (
    BOOK_DETAILS_TOOL_NODE,
    BOOK_RECOMMENDATION_TOOL_NODE,
    FAQ_TOOL_NODE,
    MERGE_TOOLS_NODE,
)
from ai_book_seeker.workflows.schemas import AgentState
from ai_book_seeker.workflows.tools.tool_logic import (
    run_book_details_tool,
    run_book_recommendation_tool,
    run_faq_tool,
)
from ai_book_seeker.workflows.utils.error_handling import handle_node_error
from ai_book_seeker.workflows.utils.message_factory import (
    create_system_message,
    create_tool_message,
)
from langgraph.types import Command
from pydantic import ValidationError

logger = get_logger(__name__)


def _create_tool_success_command(tool_name: str, result: Any, state: AgentState, result_field: str) -> Command:
    """
    Create standardized success command for tool execution.

    Args:
        tool_name: Name of the tool
        result: Tool execution result
        state: Current workflow state
        result_field: Field name in agent_results to store result

    Returns:
        Command: Success command with tool message and result
    """
    tool_msg = create_tool_message(
        content=f"{tool_name} executed successfully",
        tool_name=tool_name,
        session_id=state.session_id,
    )

    return Command(
        update={
            "messages": [tool_msg],
            "agent_results": state.agent_results.model_copy(update={result_field: result}),
        },
    )


async def faq_tool_node(state: AgentState, faq_service: Any) -> Command:
    """
    FAQ tool node - executes FAQ tool logic.

    Args:
        state: Current workflow state
        faq_service: FAQ service instance

    Returns:
        Command: Next step in workflow
    """
    trace_id = state.session_id
    logger.info(f"[FAQTool][{trace_id}] Executing for session {trace_id}")

    start_time = time.time()

    try:
        result = await run_faq_tool(state.shared_data.extracted_parameters, faq_service)
        execution_time = time.time() - start_time
        logger.info(f"[FAQTool][{trace_id}] Execution completed in {execution_time:.2f}s (success: True)")

        return _create_tool_success_command(FAQ_TOOL_NODE, result, state, "faq")

    except ValidationError as ve:
        logger.error(f"[FAQTool][{trace_id}] Validation error: {ve}")
        error_msg = create_system_message(
            content=f"FAQ tool validation error: {str(ve)}",
            node_name=FAQ_TOOL_NODE,
            session_id=state.session_id,
            message_type="tool_error",
        )
        return Command(update={"messages": [error_msg]})

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"[FAQTool][{trace_id}] Error: {e} (execution_time: {execution_time:.2f}s)")
        return handle_node_error(e, FAQ_TOOL_NODE, state)


async def book_recommendation_tool_node(state: AgentState, settings: Any, chromadb_service: Any) -> Command:
    """
    Book recommendation tool node - executes book recommendation tool logic.

    Args:
        state: Current workflow state
        settings: Application settings
        chromadb_service: ChromaDB service instance

    Returns:
        Command: Next step in workflow
    """
    trace_id = state.session_id
    logger.info(f"[BookRecTool][{trace_id}] Executing for session {trace_id}")

    start_time = time.time()

    try:
        result = await run_book_recommendation_tool(
            state.shared_data.extracted_parameters, state.messages[-1].content, settings, chromadb_service
        )
        execution_time = time.time() - start_time
        logger.info(f"[BookRecTool][{trace_id}] Execution completed in {execution_time:.2f}s (success: True)")

        return _create_tool_success_command(BOOK_RECOMMENDATION_TOOL_NODE, result, state, "book_recommendation")

    except ValidationError as ve:
        logger.error(f"[BookRecTool][{trace_id}] Validation error: {ve}")
        error_msg = create_system_message(
            content=f"Book recommendation tool validation error: {str(ve)}",
            node_name=BOOK_RECOMMENDATION_TOOL_NODE,
            session_id=state.session_id,
            message_type="tool_error",
        )
        return Command(update={"messages": [error_msg]})

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"[BookRecTool][{trace_id}] Error: {e} (execution_time: {execution_time:.2f}s)")
        return handle_node_error(e, BOOK_RECOMMENDATION_TOOL_NODE, state)


async def book_details_tool_node(state: AgentState, settings: Any) -> Command:
    """
    Book details tool node - executes book details tool logic.

    Args:
        state: Current workflow state
        settings: Application settings

    Returns:
        Command: Next step in workflow
    """
    trace_id = state.session_id
    logger.info(f"[BookDetailsTool][{trace_id}] Executing for session {trace_id}")

    start_time = time.time()

    try:
        result = await run_book_details_tool(state.shared_data.extracted_parameters, settings)
        execution_time = time.time() - start_time
        logger.info(f"[BookDetailsTool][{trace_id}] Execution completed in {execution_time:.2f}s (success: True)")

        return _create_tool_success_command(BOOK_DETAILS_TOOL_NODE, result, state, "book_details")

    except ValidationError as ve:
        logger.error(f"[BookDetailsTool][{trace_id}] Validation error: {ve}")
        error_msg = create_system_message(
            content=f"Book details tool validation error: {str(ve)}",
            node_name=BOOK_DETAILS_TOOL_NODE,
            session_id=state.session_id,
            message_type="tool_error",
        )
        return Command(update={"messages": [error_msg]})

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"[BookDetailsTool][{trace_id}] Error: {e} (execution_time: {execution_time:.2f}s)")
        return handle_node_error(e, BOOK_DETAILS_TOOL_NODE, state)


def merge_tools_node(state: AgentState) -> Command:
    """
    Merge tools node - merges results from parallel tool execution.

    Args:
        state: Current workflow state

    Returns:
        Command: Next step in workflow
    """
    trace_id = state.session_id
    logger.info(f"[MergeTools][{trace_id}] Merging tool results for session {trace_id}")

    # Count executed tools from messages
    tools_executed = len(
        [msg for msg in state.messages if msg.additional_kwargs.get("message_type") == "tool_execution"]
    )

    # Create merge completion message
    merge_msg = create_system_message(
        content="Tool execution completed, merging results",
        node_name=MERGE_TOOLS_NODE,
        session_id=state.session_id,
        message_type="merge_complete",
        additional_kwargs={"tools_executed": tools_executed},
    )

    return Command(update={"messages": [merge_msg]})
