"""
Base agent implementation for workflow orchestration.

This module provides the BaseAgent class that implements the Template Method pattern
for agent behavior. All agents extend this base class to inherit common functionality
while implementing their specific roles and capabilities.

Follows LangGraph best practices for agent implementation with:
- Template Method pattern for extensible agent behavior
- Comprehensive error handling and logging
- Async LLM operations with proper validation
- Structured state management and message creation
"""

import json
from typing import Any, Dict, List, Optional

from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.workflows.schemas import (
    AgentInsight,
    AgentRole,
    AgentState,
    RoutingAnalysis,
)
from ai_book_seeker.workflows.utils.error_handling import (
    create_error_message,
    handle_node_error,
)
from ai_book_seeker.workflows.utils.message_factory import create_ai_message
from ai_book_seeker.workflows.utils.node_utils import create_command
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import AIMessage
from langgraph.types import Command

logger = get_logger(__name__)

# Constants for validation and business logic
MIN_CONFIDENCE = 0.0
MAX_CONFIDENCE = 1.0
REQUIRED_LLM_RESPONSE_KEYS = ["selected_tools", "reasoning", "confidence"]

# Intent mapping for router context building
INTENT_DISPLAY_MAPPINGS = {
    "faq_requests": "FAQ requests",
    "book_recommendations": "book recommendations",
    "product_inquiries": "product inquiries",
    "sales_requests": "sales requests",
}


class BaseAgent:
    """
    Base agent class implementing the Template Method pattern.

    Provides common functionality for all agents including:
    - LLM-based query analysis and tool selection
    - State validation and error handling
    - Message creation and routing
    - Performance tracking and logging

    Each agent must implement:
    - _define_role(): Define the agent's role and capabilities
    - _create_analysis_prompt(): Create agent-specific analysis prompts
    """

    def __init__(self, name: str, llm: BaseLanguageModel) -> None:
        """
        Initialize the base agent with name and language model.

        Args:
            name: Unique identifier for the agent
            llm: Language model for query analysis and tool selection
        """
        self.name = name
        self.llm = llm
        self.role = self._define_role()
        logger.info(f"[{self.name}] Initialized with role: {self.role.role}")

    def _define_role(self) -> AgentRole:
        """
        Define the agent's role. Must be implemented by each agent.

        Returns:
            AgentRole: The agent's role definition including expertise and tools
        """
        raise NotImplementedError("Each agent must implement _define_role()")

    def _create_analysis_prompt(self, query: str, router_context: str) -> str:
        """
        Create agent-specific analysis prompt. Must be implemented by each agent.

        Args:
            query: User query to analyze
            router_context: Router analysis context

        Returns:
            str: Agent-specific analysis prompt
        """
        raise NotImplementedError("Each agent must implement _create_analysis_prompt()")

    def _validate_input_state(self, state: AgentState) -> Optional[Command]:
        """
        Validate input state before processing.

        Args:
            state: Current workflow state to validate

        Returns:
            Optional[Command]: Error command if validation fails, None if valid
        """
        if not state.validate_state_consistency():
            logger.error(f"[{self.name}] Invalid state detected for session {state.session_id}")
            error_msg = create_error_message(ValueError("Invalid state detected"), self.name, state.session_id)
            return create_command(messages=[error_msg], state=state, metric_name=self.name)
        return None

    def _create_agent_message(self, content: str, state: AgentState, message_type: str, **kwargs) -> AIMessage:
        """
        Create standardized agent message with common parameters.

        Args:
            content: Message content
            state: Current workflow state
            message_type: Type of message (e.g., "agent_analysis", "agent_error")
            **kwargs: Additional keyword arguments for the message

        Returns:
            AIMessage: Standardized agent message
        """
        return create_ai_message(
            content=content,
            node_name=self.name,
            session_id=state.session_id,
            message_type=message_type,
            additional_kwargs=kwargs,
        )

    def _create_tool_routing_command(
        self, agent_msg: AIMessage, selected_tools: List[str], state: AgentState
    ) -> Command:
        """
        Create routing command for tool selection with consistent state updates.

        Args:
            agent_msg: Agent analysis message
            selected_tools: List of selected tools for execution
            state: Current workflow state

        Returns:
            Command: Routing command with tool selection
        """
        state.shared_data.selected_tools_for_parallel = selected_tools
        return create_command(messages=[agent_msg], state=state)

    def _create_routing_command(self, insight: AgentInsight, agent_msg: AIMessage, state: AgentState) -> Command:
        """
        Create routing command based on tool selection using conditional edges.

        Args:
            insight: Agent's analysis insight
            agent_msg: Agent analysis message
            state: Current workflow state

        Returns:
            Command: Routing command for next workflow step
        """
        tool_count = len(insight.selected_tools)

        if tool_count == 0:
            logger.warning(f"[{self.name}] No suitable tools found for query")
            error_msg = self._create_agent_message(
                content=f"{self.role.role}: No suitable tools found for this query",
                state=state,
                message_type="agent_error",
                error="No suitable tools found for this query",
            )
            return create_command(messages=[error_msg], state=state)

        log_message = f"Selected {'single tool' if tool_count == 1 else f'{tool_count} tools for parallel execution'}: {insight.selected_tools}"
        logger.info(f"[{self.name}] {log_message}")
        return self._create_tool_routing_command(agent_msg, insight.selected_tools, state)

    def _handle_llm_error(self, error: Exception, error_type: str) -> ValueError:
        """
        Handle LLM errors with consistent logging and error creation.

        Args:
            error: The exception that occurred
            error_type: Type of error for context

        Returns:
            ValueError: Standardized error with context
        """
        logger.error(f"[{self.name}] {error_type}: {error}")
        return ValueError(f"{error_type} for {self.name} agent: {str(error)}")

    async def _llm_based_query_analysis(self, state: AgentState) -> AgentInsight:
        """
        Use LLM to analyze query and select appropriate tools.

        Args:
            state: Current workflow state

        Returns:
            AgentInsight: Analysis result with tool selection and reasoning

        Raises:
            ValueError: If no messages available or LLM analysis fails
        """
        if not state.messages:
            raise ValueError(f"No messages available for {self.name} agent")

        query = state.messages[-1].content
        router_context = self._build_router_context(state.shared_data.routing_analysis)
        prompt = self._create_analysis_prompt(query, router_context)

        try:
            result = await self.llm.ainvoke(prompt, response_format={"type": "json_object"})

            # Handle empty or invalid responses
            if not result.content or not result.content.strip():
                raise ValueError("LLM returned empty response")

            try:
                analysis = json.loads(result.content)
            except json.JSONDecodeError as e:
                logger.error(f"LLM returned invalid JSON: {result.content}")
                raise ValueError(f"LLM returned invalid JSON: {e}")

        except Exception as e:
            raise self._handle_llm_error(e, "LLM invocation failed")

        if not self._validate_llm_response(analysis):
            logger.error(f"[{self.name}] Invalid LLM response structure: {analysis}")
            raise ValueError(f"Invalid LLM response structure from {self.name} agent")

        return AgentInsight(
            agent_name=self.name,
            role=self.role.role,
            query_analysis=f"Query requires {', '.join(analysis['selected_tools'])}",
            selected_tools=analysis["selected_tools"],
            reasoning=analysis["reasoning"],
            confidence=analysis["confidence"],
        )

    def _build_router_context(self, router_analysis: Optional[RoutingAnalysis]) -> str:
        """
        Build router context string from router analysis.

        Args:
            router_analysis: Router analysis data

        Returns:
            str: Formatted router context for LLM prompt
        """
        if not router_analysis:
            return ""

        # Build intent summary using constants
        intent_summary = []
        if router_analysis.query_intents:
            intent_summary = [
                f"{len(getattr(router_analysis.query_intents, key, []))} {display_name}"
                for key, display_name in INTENT_DISPLAY_MAPPINGS.items()
                if getattr(router_analysis.query_intents, key, None)
            ]

        return f"""
Router Analysis:
- Multi-agent query: {router_analysis.is_multi_agent}
- Query intents: {', '.join(intent_summary) if intent_summary else 'None'}
- Router reasoning: {router_analysis.reasoning or 'None'}
- Router confidence: {router_analysis.confidence}
"""

    def _validate_llm_response(self, analysis: Dict[str, Any]) -> bool:
        """
        Validate LLM response structure and tool availability.

        Args:
            analysis: LLM response to validate

        Returns:
            bool: True if response is valid, False otherwise
        """
        # Validate required keys
        if not all(key in analysis for key in REQUIRED_LLM_RESPONSE_KEYS):
            return False

        # Validate confidence value using constants
        confidence = analysis.get("confidence")
        if not isinstance(confidence, (int, float)) or not (MIN_CONFIDENCE <= confidence <= MAX_CONFIDENCE):
            return False

        # Validate selected tools
        selected_tools = analysis.get("selected_tools")
        if not isinstance(selected_tools, list):
            return False

        # Validate tool availability
        available_tools = set(self.role.available_tools)
        selected_tools_set = set(selected_tools)
        if not selected_tools_set.issubset(available_tools):
            logger.warning(f"[{self.name}] LLM selected unavailable tools: {selected_tools_set - available_tools}")
            return False

        return True

    def _update_state_with_insight(self, state: AgentState, insight: AgentInsight) -> None:
        """
        Update state with agent insight and role.

        Args:
            state: Current workflow state
            insight: Agent's analysis insight
        """
        state.shared_data.agent_insights.append(insight)
        state.shared_data.current_agent_role = self.role

    async def handle(self, state: AgentState) -> Command:
        """
        Main entry point for agent processing using Template Method pattern.

        This method orchestrates the complete agent workflow:
        1. Validate LLM availability and input state
        2. Perform LLM-based query analysis
        3. Update state with agent insights
        4. Create routing command for tool execution

        Args:
            state: Current workflow state

        Returns:
            Command: LangGraph command for next workflow step
        """
        if not self.llm:
            logger.error(f"[{self.name}] No LLM available for query analysis")
            return handle_node_error(
                error=ValueError(f"LLM is required for {self.name} agent but not configured"),
                node_name=self.name,
                state=state,
                custom_content=f"{self.role.role}: LLM not configured - cannot process query",
            )

        # Validate input state after critical dependency check
        error_cmd = self._validate_input_state(state)
        if error_cmd:
            return error_cmd

        try:
            insight = await self._llm_based_query_analysis(state)
        except Exception as e:
            logger.error(f"[{self.name}] Query analysis failed: {e}")
            return handle_node_error(
                error=e,
                node_name=self.name,
                state=state,
                custom_content=f"{self.role.role}: Failed to analyze query - {str(e)}",
            )

        self._update_state_with_insight(state, insight)
        agent_msg = self._create_agent_message(
            content=f"{self.role.role}: {insight.query_analysis}",
            state=state,
            message_type="agent_analysis",
            role=self.role.role,
            selected_tools=insight.selected_tools,
            confidence=insight.confidence,
        )
        return self._create_routing_command(insight, agent_msg, state)
