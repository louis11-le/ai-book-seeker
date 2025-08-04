"""
Tool node functions for workflow orchestration.

This module contains tool node functions that execute business logic.
Follows LangGraph best practices for tool node implementation.
"""

import time
from typing import Any

from langgraph.types import Command
from pydantic import ValidationError

from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.workflows.constants import (
    BOOK_DETAILS_TOOL_NODE,
    BOOK_RECOMMENDATION_TOOL_NODE,
    FAQ_TOOL_NODE,
    STREAMING_RESPONSE_MESSAGE_TYPE,
    TOOL_ERROR_MESSAGE_TYPE,
)
from ai_book_seeker.workflows.schemas import AgentState
from ai_book_seeker.workflows.tools.tool_logic import run_book_details_tool, run_book_recommendation_tool, run_faq_tool
from ai_book_seeker.workflows.utils.error_handling import handle_node_error
from ai_book_seeker.workflows.utils.message_factory import create_system_message
from ai_book_seeker.workflows.utils.response_formatters import (
    format_book_details_response,
    format_book_recommendation_response,
    format_faq_response,
)

logger = get_logger(__name__)


def _create_streaming_command(
    state: AgentState, result: Any, node_name: str, tool_name: str, result_field: str, formatted_response: str
) -> Command:
    """
    Create streaming command for tool execution with formatted response.

    Args:
        state: Current workflow state
        result: Tool execution result
        node_name: Name of the tool node
        tool_name: Name of the tool for metadata
        result_field: Field name in agent_results to store result
        formatted_response: Formatted response content

    Returns:
        Command: Streaming command with formatted response
    """
    streaming_msg = create_system_message(
        content=formatted_response,
        node_name=node_name,
        session_id=state.session_id,
        message_type=STREAMING_RESPONSE_MESSAGE_TYPE,
        additional_kwargs={"tool_name": tool_name, "streaming": True},
    )

    return Command(
        update={
            "messages": [streaming_msg],
            "agent_results": state.agent_results.model_copy(update={result_field: result}),
        }
    )


def _handle_tool_validation_error(ve: ValidationError, node_name: str, state: AgentState) -> Command:
    """
    Handle validation errors for tool execution.

    Args:
        ve: Validation error
        node_name: Name of the tool node
        state: Current workflow state

    Returns:
        Command: Error command
    """
    logger.error(f"[{node_name}][{state.session_id}] Validation error: {ve}")
    error_msg = create_system_message(
        content=f"{node_name} validation error: {str(ve)}",
        node_name=node_name,
        session_id=state.session_id,
        message_type=TOOL_ERROR_MESSAGE_TYPE,
    )
    return Command(update={"messages": [error_msg]})


async def faq_tool_node(state: AgentState, faq_service: Any) -> Command:
    """
    FAQ tool node - executes FAQ tool logic with streaming response.

    Args:
        state: Current workflow state
        faq_service: FAQ service instance

    Returns:
        Command: Next step in workflow with streaming response
    """
    trace_id = state.session_id
    logger.info(f"[FAQTool][{trace_id}] Executing for session {trace_id}")

    start_time = time.time()
    try:
        result = await run_faq_tool(state.shared_data.extracted_parameters, faq_service)
        execution_time = time.time() - start_time
        logger.info(f"[FAQTool][{trace_id}] Execution completed in {execution_time:.2f}s (success: True)")

        # Format FAQ response for immediate streaming
        formatted_response = format_faq_response(result)
        return _create_streaming_command(
            state=state,
            result=result,
            node_name=FAQ_TOOL_NODE,
            tool_name="faq",
            result_field="faq",
            formatted_response=formatted_response,
        )
    except ValidationError as ve:
        return _handle_tool_validation_error(ve, FAQ_TOOL_NODE, state)
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"[FAQTool][{trace_id}] Error: {e} (execution_time: {execution_time:.2f}s)")
        return handle_node_error(e, FAQ_TOOL_NODE, state)


async def book_recommendation_tool_node(state: AgentState, settings: Any, chromadb_service: Any) -> Command:
    """
    Book recommendation tool node - executes book recommendation tool logic with streaming response.

    Args:
        state: Current workflow state
        settings: Application settings
        chromadb_service: ChromaDB service instance

    Returns:
        Command: Next step in workflow with streaming response
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

        # Format book recommendation response for immediate streaming
        formatted_response = format_book_recommendation_response(result)
        return _create_streaming_command(
            state=state,
            result=result,
            node_name=BOOK_RECOMMENDATION_TOOL_NODE,
            tool_name="book_recommendation",
            result_field="book_recommendation",
            formatted_response=formatted_response,
        )
    except ValidationError as ve:
        return _handle_tool_validation_error(ve, BOOK_RECOMMENDATION_TOOL_NODE, state)
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"[BookRecTool][{trace_id}] Error: {e} (execution_time: {execution_time:.2f}s)")
        return handle_node_error(e, BOOK_RECOMMENDATION_TOOL_NODE, state)


async def book_details_tool_node(state: AgentState, settings: Any) -> Command:
    """
    Book details tool node - executes book details tool logic with streaming response.

    Args:
        state: Current workflow state
        settings: Application settings

    Returns:
        Command: Next step in workflow with streaming response
    """
    trace_id = state.session_id
    logger.info(f"[BookDetailsTool][{trace_id}] Executing for session {trace_id}")

    start_time = time.time()
    try:
        result = await run_book_details_tool(state.shared_data.extracted_parameters, settings)
        execution_time = time.time() - start_time
        logger.info(f"[BookDetailsTool][{trace_id}] Execution completed in {execution_time:.2f}s (success: True)")

        # Format book details response for immediate streaming
        formatted_response = format_book_details_response(result)
        return _create_streaming_command(
            state=state,
            result=result,
            node_name=BOOK_DETAILS_TOOL_NODE,
            tool_name="book_details",
            result_field="book_details",
            formatted_response=formatted_response,
        )
    except ValidationError as ve:
        return _handle_tool_validation_error(ve, BOOK_DETAILS_TOOL_NODE, state)
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"[BookDetailsTool][{trace_id}] Error: {e} (execution_time: {execution_time:.2f}s)")
        return handle_node_error(e, BOOK_DETAILS_TOOL_NODE, state)
