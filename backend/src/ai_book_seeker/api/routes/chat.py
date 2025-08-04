"""
Chat API Routes

This module provides streaming chat endpoints powered by LangGraph orchestrator.
Implements real-time streaming with "updates" mode for workflow state changes.
"""

from typing import Any, AsyncGenerator, Dict, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from langgraph.graph import StateGraph

from ai_book_seeker.api.schemas.chat import ChatRequest, ChatResponse, ChatSessionResponse, EnhancedChatSessionResponse
from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.utils.streaming_utils import has_meaningful_agent_results, sanitize_agent_results
from ai_book_seeker.workflows.orchestrator import get_orchestrator
from ai_book_seeker.workflows.schemas import AgentState, get_state_manager

router = APIRouter()
logger = get_logger(__name__)


def _create_streaming_response(
    session_id: str, output: str, data: Dict[str, Any], correlation_id: Optional[str] = None
) -> str:
    """
    Create a streaming response chunk using Pydantic models.

    Args:
        session_id: Session identifier
        output: Response output content
        data: Additional response data
        correlation_id: Optional correlation ID for tracing

    Returns:
        str: JSON-formatted streaming response chunk
    """
    chat_response = ChatResponse(output=output, data=data)

    # Use EnhancedChatSessionResponse if correlation_id is provided
    if correlation_id:
        response = EnhancedChatSessionResponse(
            session_id=session_id, response=chat_response, correlation_id=correlation_id
        )
    else:
        response = ChatSessionResponse(session_id=session_id, response=chat_response)

    return response.model_dump_json() + "\n"


def _create_error_response(
    session_id: str,
    correlation_id: str,
    error_type: str = "internal_error",
    error_message: str = "Internal server error",
) -> str:
    """
    Create an error streaming response.

    Args:
        session_id: Session identifier
        correlation_id: Request correlation ID for tracing
        error_type: Type of error that occurred
        error_message: Human-readable error message

    Returns:
        str: JSON-formatted error response chunk
    """
    return _create_streaming_response(
        session_id=session_id,
        output=error_message,
        data={"status": "error", "correlation_id": correlation_id, "error_type": error_type},
        correlation_id=correlation_id,
    )


def _extract_message_content(message: Any) -> Optional[str]:
    """
    Extract content from a message object or dictionary.

    Args:
        message: Message object or dictionary

    Returns:
        Optional[str]: Message content if valid, None otherwise
    """
    if not message:
        return None

    # Extract content from message object or dictionary
    content = None
    if hasattr(message, "content"):
        content = message.content
    elif isinstance(message, dict) and "content" in message:
        content = message["content"]

    # Return stripped content if valid, None otherwise
    return content.strip() if content and isinstance(content, str) else None


def _process_workflow_update(
    node_name: str, update: Dict[str, Any], session_id: str, correlation_id: str
) -> Optional[str]:
    """
    Process workflow update and create streaming response if meaningful data found.

    Args:
        node_name: Name of the node that generated the update
        update: Complete update data
        session_id: Session identifier
        correlation_id: Request correlation ID

    Returns:
        Optional[str]: Streaming response chunk if meaningful data found, None otherwise
    """
    # Process messages
    if "messages" in update and update["messages"] is not None:
        logger.debug(f"[{correlation_id}] Messages: {update['messages']}")
        messages = update["messages"]
        # Get the message to process (latest from list or single message)
        message_to_process = messages[-1] if isinstance(messages, list) and messages else messages
        logger.info(f"[{correlation_id}] Message to process: {message_to_process}")
        content = _extract_message_content(message_to_process)
        if content:
            # Optimized: Only include what frontend actually uses
            response_data = {"node": node_name}

            # Include agent_results if available (for structured data)
            if "agent_results" in update and update["agent_results"] is not None:
                response_data["agent_results"] = sanitize_agent_results(update["agent_results"])

            # Include shared_data if available
            if "shared_data" in update and update["shared_data"] is not None:
                shared_data = update["shared_data"]
                response_data["shared_data"] = _sanitize_shared_data(shared_data)

            return _create_streaming_response(
                session_id=session_id,
                output=content,
                data=response_data,
                correlation_id=correlation_id,
            )

    # Process agent results
    if "agent_results" in update and update["agent_results"] is not None:
        logger.info(f"[{correlation_id}] Agent results: {update['agent_results']}")
        agent_results = update["agent_results"]
        if has_meaningful_agent_results(agent_results):
            response_data = {"node": node_name, "agent_results": sanitize_agent_results(agent_results)}

            # Include shared_data if available
            if "shared_data" in update and update["shared_data"] is not None:
                shared_data = update["shared_data"]
                response_data["shared_data"] = _sanitize_shared_data(shared_data)

            return _create_streaming_response(
                session_id=session_id,
                output="Processing...",
                data=response_data,
                correlation_id=correlation_id,
            )

    return None


def _sanitize_shared_data(shared_data: Any) -> Dict[str, Any]:
    """
    Sanitize shared data for frontend consumption.

    Args:
        shared_data: Raw shared data from workflow state

    Returns:
        Dict[str, Any]: Sanitized shared data safe for frontend
    """
    if not shared_data:
        return {}

    try:
        # Convert to dict if it's a Pydantic model
        if hasattr(shared_data, "model_dump"):
            shared_dict = shared_data.model_dump()
        elif isinstance(shared_data, dict):
            shared_dict = shared_data
        else:
            return {}

        # Extract relevant fields for frontend
        sanitized = {}

        # Routing analysis
        if "routing_analysis" in shared_dict and shared_dict["routing_analysis"]:
            routing = shared_dict["routing_analysis"]
            if hasattr(routing, "model_dump"):
                routing_dict = routing.model_dump()
            else:
                routing_dict = routing
            sanitized["routing_analysis"] = {
                "next_node": routing_dict.get("next_node"),
                "participating_agents": routing_dict.get("participating_agents", []),
                "is_multi_purpose": routing_dict.get("is_multi_purpose", False),
                "is_multi_agent": routing_dict.get("is_multi_agent", False),
                "confidence": routing_dict.get("confidence", 0.0),
                "reasoning": routing_dict.get("reasoning", ""),
            }

        # Extracted parameters
        if "extracted_parameters" in shared_dict and shared_dict["extracted_parameters"]:
            sanitized["extracted_parameters"] = shared_dict["extracted_parameters"]

        # Participating agents for parallel execution
        if "participating_agents_for_parallel" in shared_dict and shared_dict["participating_agents_for_parallel"]:
            sanitized["participating_agents_for_parallel"] = shared_dict["participating_agents_for_parallel"]

        # Selected tools for parallel execution
        if "selected_tools_for_parallel" in shared_dict and shared_dict["selected_tools_for_parallel"]:
            sanitized["selected_tools_for_parallel"] = shared_dict["selected_tools_for_parallel"]

        # Agent insights (simplified)
        if "agent_insights" in shared_dict and shared_dict["agent_insights"]:
            insights = shared_dict["agent_insights"]
            if isinstance(insights, list):
                sanitized["agent_insights"] = [
                    {
                        "agent_name": (
                            insight.get("agent_name")
                            if isinstance(insight, dict)
                            else getattr(insight, "agent_name", None)
                        ),
                        "selected_tools": (
                            insight.get("selected_tools", [])
                            if isinstance(insight, dict)
                            else getattr(insight, "selected_tools", [])
                        ),
                        "reasoning": (
                            insight.get("reasoning", "")
                            if isinstance(insight, dict)
                            else getattr(insight, "reasoning", "")
                        ),
                    }
                    for insight in insights
                ]

        # Performance metrics (basic)
        if "performance_metrics" in shared_dict and shared_dict["performance_metrics"]:
            sanitized["performance_metrics"] = shared_dict["performance_metrics"]

        return sanitized

    except Exception as e:
        logger.warning(f"Error sanitizing shared data: {e}")
        return {}


def _create_initial_state(session_id: str, message: str, correlation_id: str) -> AgentState:
    """
    Create initial workflow state for chat session.

    Args:
        session_id: Unique session identifier
        message: User message content
        correlation_id: Request correlation ID for tracing

    Returns:
        AgentState: Initialized workflow state
    """
    state_manager = get_state_manager()
    return state_manager.create_initial_state(
        session_id=session_id, interface="chat", message=message, correlation_id=correlation_id
    )


async def _stream_workflow_events(
    orchestrator: StateGraph, initial_state: AgentState, session_id: str, correlation_id: str
) -> AsyncGenerator[str, None]:
    """
    Stream workflow events from LangGraph orchestrator with enhanced error handling.

    Args:
        orchestrator: LangGraph workflow instance
        initial_state: Initial workflow state
        session_id: Session identifier
        correlation_id: Request correlation ID for tracing

    Yields:
        JSON-formatted streaming response chunks
    """
    try:
        logger.debug(
            f"[{correlation_id}] Starting workflow stream",
            extra={
                "correlation_id": correlation_id,
                "session_id": session_id,
                "interface": initial_state.interface,
            },
        )

        # Stream workflow updates in real-time
        async for chunk in orchestrator.astream(
            initial_state,
            {"configurable": {"thread_id": session_id}},
            stream_mode="updates",
        ):
            # Process each node update
            for node_name, update in chunk.items():
                try:
                    response = _process_workflow_update(node_name, update, session_id, correlation_id)
                    if response:
                        yield response

                except Exception as chunk_error:
                    logger.error(
                        f"[{correlation_id}] Error processing chunk",
                        extra={
                            "correlation_id": correlation_id,
                            "session_id": session_id,
                            "node_name": node_name,
                            "error_type": type(chunk_error).__name__,
                            "error_message": str(chunk_error),
                        },
                        exc_info=True,
                    )
                    # Continue processing other chunks instead of failing completely
                    continue

        # Send completion signal
        yield _create_streaming_response(
            session_id=session_id,
            output="[DONE]",
            data={"status": "completed", "correlation_id": correlation_id},
            correlation_id=correlation_id,
        )
        logger.info(
            f"[{correlation_id}] Workflow stream completed successfully",
            extra={"correlation_id": correlation_id, "session_id": session_id},
        )
    except Exception as e:
        logger.error(
            f"[{correlation_id}] Error in streaming generator",
            extra={
                "correlation_id": correlation_id,
                "session_id": session_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
            exc_info=True,
        )
        yield _create_streaming_response(
            session_id=session_id,
            output=f"Error: {str(e)}",
            data={"status": "error", "correlation_id": correlation_id, "error_type": "streaming_error"},
            correlation_id=correlation_id,
        )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, fastapi_request: Request) -> StreamingResponse:
    """
    Streaming chat endpoint powered by LangGraph orchestrator.

    Uses LangGraph's streaming capabilities with "updates" mode to provide
    real-time streaming of workflow state changes and tool results.

    Args:
        request: Chat request with message and optional session ID
        fastapi_request: FastAPI request object for app state access

    Returns:
        StreamingResponse: Real-time streaming of chat responses

    Raises:
        HTTPException: If request validation fails or processing error occurs
    """
    correlation_id = str(uuid4())
    session_id = request.session_id or str(uuid4())

    try:
        # Validate request
        if not request.message or not request.message.strip():
            logger.warning(f"[{correlation_id}] Empty message received")
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        logger.info(
            f"[{correlation_id}] Streaming chat request received",
            extra={
                "correlation_id": correlation_id,
                "session_id": session_id,
                "message_length": len(request.message),
                "has_session_id": bool(request.session_id),
            },
        )

        # Get orchestrator and create initial state
        orchestrator = await get_orchestrator(fastapi_request.app)
        initial_state = _create_initial_state(session_id, request.message, correlation_id)

        # Create streaming response with optimized headers
        return StreamingResponse(
            _stream_workflow_events(orchestrator, initial_state, session_id, correlation_id),
            media_type="application/json",
            headers={
                "X-Correlation-ID": correlation_id,
                "X-Session-ID": session_id,
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(
            f"[{correlation_id}] Error processing streaming chat request",
            extra={
                "correlation_id": correlation_id,
                "session_id": session_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
            exc_info=True,
        )
        # Return error stream with correlation ID
        return StreamingResponse(
            _create_error_response(session_id, correlation_id),
            media_type="application/json",
            headers={"X-Correlation-ID": correlation_id},
        )
