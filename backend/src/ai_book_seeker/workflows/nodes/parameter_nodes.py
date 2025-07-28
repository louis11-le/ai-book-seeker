"""
Parameter extraction nodes for workflow orchestration.

This module contains parameter extraction node functions for the LangGraph workflow.
Follows LangGraph best practices for parameter extraction and routing.

Key Components:
- parameter_extraction_node: Extracts parameters from user queries using LLM

Architecture:
- LLM-powered parameter extraction with structured output
- Intelligent routing based on extracted parameters and analysis
- Comprehensive error handling and validation
- Performance tracking and metrics collection
"""

from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.workflows.constants import (
    AGENT_COORDINATOR_NODE,
    GENERAL_AGENT_NODE,
    GENERAL_VOICE_AGENT_NODE,
    PARAMETER_EXTRACTION_NODE,
    SALES_AGENT_NODE,
)
from ai_book_seeker.workflows.routing.parameter_extraction import (
    extract_parameters_with_llm,
)
from ai_book_seeker.workflows.schemas import AgentState
from ai_book_seeker.workflows.utils.error_handling import handle_node_error
from ai_book_seeker.workflows.utils.message_factory import create_parameter_message
from ai_book_seeker.workflows.utils.node_utils import (
    create_command,
    validate_input_state,
)
from langchain_core.messages import HumanMessage
from langgraph.types import Command

logger = get_logger(__name__)

# Valid routing targets for parameter extraction
VALID_ROUTING_TARGETS = {
    AGENT_COORDINATOR_NODE,
    GENERAL_AGENT_NODE,
    GENERAL_VOICE_AGENT_NODE,
    SALES_AGENT_NODE,
}


async def parameter_extraction_node(state: AgentState, llm) -> Command:
    """
    Parameter extraction node - extracts parameters from user query.

    This node performs LLM-based parameter extraction for all tools and routes
    to the appropriate agent based on routing analysis. LLM is required for
    extraction - no fallback mechanism is provided.

    Args:
        state: Current workflow state containing messages and shared data
        llm: Language model for extraction (required - no fallback)

    Returns:
        Command: Next step in workflow with routing decision

    Note:
        LLM is required for parameter extraction. No fallback mechanism - system fails
        gracefully when LLM is unavailable.

    Example:
        ```python
        # Extract parameters and route to appropriate agent
        command = await parameter_extraction_node(state, llm)
        # Returns Command with goto=agent_node and updated state
        ```
    """
    trace_id = state.session_id
    logger.info(f"[{PARAMETER_EXTRACTION_NODE}][{trace_id}] Extracting parameters from query")

    try:
        # Validate input state before processing
        error_cmd = validate_input_state(state, PARAMETER_EXTRACTION_NODE)
        if error_cmd:
            return error_cmd

        query = next((m.content for m in reversed(state.messages) if isinstance(m, HumanMessage)), None)
        if not query:
            raise ValueError("No valid HumanMessage found for parameter extraction")

        logger.debug(f"[{PARAMETER_EXTRACTION_NODE}] Using query: {query}")
        extracted_params = await extract_parameters_with_llm(query, llm)

        # Update state with extracted parameters
        state.shared_data.extracted_parameters = extracted_params

        # Create parameter extraction message using utility
        param_msg = create_parameter_message(
            extracted_parameters=extracted_params,
            session_id=state.session_id,
        )
        # Let conditional edges handle routing - no goto needed
        # Let add_messages reducer handle message accumulation automatically
        return create_command(
            messages=[param_msg],  # Only pass new messages - reducer handles accumulation
            state=state,
            metric_name="parameter_extraction",
            trace_id=trace_id,
            node_name=PARAMETER_EXTRACTION_NODE,
        )

    except Exception as e:
        return handle_node_error(e, PARAMETER_EXTRACTION_NODE, state)
