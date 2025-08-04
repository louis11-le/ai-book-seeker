"""
Unit tests for workflow fixes and conditional edge system.

This module tests the critical fixes implemented in the LangGraph workflow:
- Node logic fixes (removal of goto parameters)
- Conditional edge system implementation
- Error handling and fallback mechanisms
- Pure conditional edge compliance
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from ai_book_seeker.workflows.constants import (  # SALES_AGENT_NODE,  # Temporarily disabled
    AGENT_COORDINATOR_NODE,
    ERROR_NODE,
    GENERAL_AGENT_NODE,
    GENERAL_VOICE_AGENT_NODE,
    PARAMETER_EXTRACTION_NODE,
)
from ai_book_seeker.workflows.nodes.agent_nodes import agent_coordinator_node, supervisor_router_node
from ai_book_seeker.workflows.nodes.parameter_nodes import parameter_extraction_node
from ai_book_seeker.workflows.registration.edge_registration import (
    _get_agent_routing_targets,
    _get_agent_tool_routing_targets,
    _get_parameter_extraction_routing_targets,
    _should_use_tool,
)
from ai_book_seeker.workflows.schemas import AgentState, RoutingAnalysis, SharedData


class TestNodeLogicFixes:
    """Test that node logic fixes work correctly."""

    @pytest.fixture
    def mock_state(self):
        """Create a mock state for testing."""
        state = MagicMock(spec=AgentState)
        state.session_id = "test_session_123"
        state.interface = "chat"  # Add interface field
        state.messages = [MagicMock(content="test query")]
        state.shared_data = MagicMock(spec=SharedData)
        state.shared_data.performance_metrics = {}
        state.shared_data.access_count = 1
        state.shared_data.last_accessed = "2024-01-01T00:00:00Z"
        state.agent_results = MagicMock()
        return state

    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM for testing."""
        llm = AsyncMock()
        llm.ainvoke.return_value = MagicMock(content='{"next_node": "general_agent"}')
        return llm

    @pytest.mark.asyncio
    async def test_parameter_extraction_node_no_goto(self, mock_state, mock_llm):
        """Test that parameter extraction node doesn't use goto parameter."""
        # Setup routing analysis
        routing_analysis = RoutingAnalysis(
            next_node="general_agent",
            participating_agents=["general_agent"],
            is_multi_purpose=False,
            is_multi_agent=False,
            reasoning="Test reasoning",
            confidence=0.9,
        )
        mock_state.shared_data.routing_analysis = routing_analysis

        # Execute parameter extraction node
        result = await parameter_extraction_node(mock_state, mock_llm)

        # Verify no goto parameter is used
        assert hasattr(result, "update")
        assert "messages" in result.update
        assert not hasattr(result, "goto") or result.goto is None or result.goto == ()

    @pytest.mark.asyncio
    async def test_agent_coordinator_node_no_goto(self, mock_state):
        """Test that agent coordinator node doesn't use goto parameter."""
        # Setup participating agents
        mock_state.shared_data.participating_agents_for_parallel = [
            GENERAL_AGENT_NODE
        ]  # SALES_AGENT_NODE temporarily disabled
        routing_analysis = RoutingAnalysis(
            next_node=GENERAL_AGENT_NODE,
            participating_agents=[GENERAL_AGENT_NODE],  # SALES_AGENT_NODE temporarily disabled
            is_multi_purpose=True,
            is_multi_agent=True,
            reasoning="Test reasoning",
            confidence=0.9,
        )
        mock_state.shared_data.routing_analysis = routing_analysis

        # Execute agent coordinator node
        result = await agent_coordinator_node(mock_state)

        # Verify no goto parameter is used
        assert hasattr(result, "update")
        assert "messages" in result.update
        assert not hasattr(result, "goto") or result.goto is None or result.goto == ()

    @pytest.mark.asyncio
    async def test_supervisor_router_node_no_goto(self, mock_state, mock_llm):
        """Test that supervisor router node doesn't use goto parameter."""
        # Execute supervisor router node
        result = await supervisor_router_node(mock_state, mock_llm)

        # Verify no goto parameter is used
        assert hasattr(result, "update")
        assert "messages" in result.update
        assert not hasattr(result, "goto") or result.goto is None or result.goto == ()


class TestConditionalEdgeSystem:
    """Test that conditional edge system works correctly."""

    @pytest.fixture
    def mock_state(self):
        """Create a mock state for testing."""
        state = MagicMock(spec=AgentState)
        state.session_id = "test_session_123"
        state.interface = "chat"  # Add interface field
        state.shared_data = MagicMock(spec=SharedData)
        state.shared_data.agent_insights = []
        return state

    def test_parameter_extraction_routing_targets(self, mock_state):
        """Test parameter extraction routing targets."""
        # Test with valid routing analysis
        routing_analysis = RoutingAnalysis(
            next_node=GENERAL_AGENT_NODE,
            participating_agents=[GENERAL_AGENT_NODE],
            is_multi_purpose=False,
            is_multi_agent=False,
            reasoning="Test reasoning",
            confidence=0.9,
        )
        mock_state.shared_data.routing_analysis = routing_analysis

        result = _get_parameter_extraction_routing_targets(mock_state)
        assert result == GENERAL_AGENT_NODE

        # Test with agent coordinator
        mock_state.shared_data.routing_analysis.next_node = AGENT_COORDINATOR_NODE
        result = _get_parameter_extraction_routing_targets(mock_state)
        assert result == AGENT_COORDINATOR_NODE

        # Test with no routing analysis
        mock_state.shared_data.routing_analysis = None
        result = _get_parameter_extraction_routing_targets(mock_state)
        assert result == "error"  # Fallback to error node

        # Test with invalid routing analysis
        mock_state.shared_data.routing_analysis = RoutingAnalysis(
            next_node="invalid_node",
            participating_agents=[],
            is_multi_purpose=False,
            is_multi_agent=False,
            reasoning="Test reasoning",
            confidence=0.9,
        )
        result = _get_parameter_extraction_routing_targets(mock_state)
        assert result == "error"  # Fallback to error node

    def test_agent_routing_targets(self, mock_state):
        """Test agent routing targets."""
        # Test with participating agents
        mock_state.shared_data.participating_agents_for_parallel = [
            GENERAL_AGENT_NODE
        ]  # SALES_AGENT_NODE temporarily disabled
        result = _get_agent_routing_targets(mock_state)
        assert result == [GENERAL_AGENT_NODE]  # SALES_AGENT_NODE temporarily disabled

        # Test with no participating agents
        mock_state.shared_data.participating_agents_for_parallel = []
        result = _get_agent_routing_targets(mock_state)
        assert result == ["error"]

        # Test with None participating agents
        mock_state.shared_data.participating_agents_for_parallel = None
        result = _get_agent_routing_targets(mock_state)
        assert result == ["error"]

    def test_agent_tool_routing_targets(self, mock_state):
        """Test agent-to-tool routing targets."""
        available_tools = ["faq_tool", "book_recommendation_tool"]

        # Test with selected tools
        mock_state.shared_data.selected_tools_for_parallel = ["faq_tool"]
        result = _get_agent_tool_routing_targets(mock_state, available_tools)
        assert result == ["faq_tool"]

        # Test with multiple selected tools (should return all valid tools)
        mock_state.shared_data.selected_tools_for_parallel = ["faq_tool", "book_recommendation_tool"]
        result = _get_agent_tool_routing_targets(mock_state, available_tools)
        assert result == ["faq_tool", "book_recommendation_tool"]

        # Test with no selected tools
        mock_state.shared_data.selected_tools_for_parallel = []
        result = _get_agent_tool_routing_targets(mock_state, available_tools)
        assert result == ["error"]

        # Test with invalid selected tools
        mock_state.shared_data.selected_tools_for_parallel = ["invalid_tool"]
        result = _get_agent_tool_routing_targets(mock_state, available_tools)
        assert result == ["error"]

    def test_should_use_tool(self, mock_state):
        """Test tool usage determination."""
        # Test with tool in selected tools
        mock_state.shared_data.selected_tools_for_parallel = ["faq_tool"]
        result = _should_use_tool(mock_state, "faq_tool")
        assert result is True

        # Test with tool not in selected tools
        mock_state.shared_data.selected_tools_for_parallel = ["book_recommendation_tool"]
        result = _should_use_tool(mock_state, "faq_tool")
        assert result is True  # Default behavior

        # Test with no selected tools
        mock_state.shared_data.selected_tools_for_parallel = []
        result = _should_use_tool(mock_state, "faq_tool")
        assert result is True  # Default behavior


class TestErrorHandling:
    """Test error handling and fallback mechanisms."""

    @pytest.fixture
    def mock_state(self):
        """Create a mock state for testing."""
        state = MagicMock(spec=AgentState)
        state.session_id = "test_session_123"
        state.interface = "chat"  # Add interface field
        state.shared_data = MagicMock(spec=SharedData)
        state.shared_data.agent_insights = []
        return state

    def test_parameter_extraction_routing_error_handling(self, mock_state):
        """Test parameter extraction routing error handling."""
        # Test with exception
        mock_state.shared_data.routing_analysis = MagicMock()
        mock_state.shared_data.routing_analysis.next_node = MagicMock(side_effect=Exception("Test error"))

        result = _get_parameter_extraction_routing_targets(mock_state)
        assert result == "error"

    def test_agent_routing_error_handling(self, mock_state):
        """Test agent routing error handling."""
        # Test with exception
        mock_state.shared_data.participating_agents_for_parallel = MagicMock(side_effect=Exception("Test error"))

        result = _get_agent_routing_targets(mock_state)
        assert result == ["error"]

    def test_agent_tool_routing_error_handling(self, mock_state):
        """Test agent-to-tool routing error handling."""
        # Test with exception
        mock_state.shared_data.selected_tools_for_parallel = MagicMock(side_effect=Exception("Test error"))

        result = _get_agent_tool_routing_targets(mock_state, ["faq_tool"])
        assert result == ["error"]


class TestPureConditionalEdgeCompliance:
    """Test that the system follows pure conditional edge principles."""

    def test_no_dual_edge_registration(self):
        """Test that no dual edge registration exists."""
        # This test verifies that the edge registration functions don't create conflicts
        from ai_book_seeker.workflows.registration.edge_registration import (
            entrypoint_edges,
            router_to_agent_edges,
            tool_to_format_edges,
        )

        # Get all static edges
        static_edges = set()
        static_edges.update(entrypoint_edges())
        static_edges.update(router_to_agent_edges())
        static_edges.update(tool_to_format_edges())

        # Verify no dynamic routing edges are in static edges
        dynamic_routing_edges = {
            (PARAMETER_EXTRACTION_NODE, GENERAL_AGENT_NODE),
            (PARAMETER_EXTRACTION_NODE, GENERAL_VOICE_AGENT_NODE),
            # (PARAMETER_EXTRACTION_NODE, SALES_AGENT_NODE),  # Temporarily disabled
            (PARAMETER_EXTRACTION_NODE, AGENT_COORDINATOR_NODE),
            (AGENT_COORDINATOR_NODE, GENERAL_AGENT_NODE),
            (AGENT_COORDINATOR_NODE, GENERAL_VOICE_AGENT_NODE),
            # (AGENT_COORDINATOR_NODE, SALES_AGENT_NODE),  # Temporarily disabled
        }

        # Check for conflicts
        conflicts = static_edges & dynamic_routing_edges
        assert len(conflicts) == 0, f"Found dual edge registration conflicts: {conflicts}"

    def test_conditional_edge_targets(self):
        """Test that conditional edges have proper targets."""
        # This test verifies that conditional edge targets are valid
        valid_targets = {
            GENERAL_AGENT_NODE,
            GENERAL_VOICE_AGENT_NODE,
            # SALES_AGENT_NODE,  # Temporarily disabled
            AGENT_COORDINATOR_NODE,
            ERROR_NODE,
        }

        # Test parameter extraction routing targets
        mock_state = MagicMock(spec=AgentState)
        mock_state.shared_data = MagicMock(spec=SharedData)
        routing_analysis = RoutingAnalysis(
            next_node=GENERAL_AGENT_NODE,
            participating_agents=[GENERAL_AGENT_NODE],
            is_multi_purpose=False,
            is_multi_agent=False,
            reasoning="Test reasoning",
            confidence=0.9,
        )
        mock_state.shared_data.routing_analysis = routing_analysis

        result = _get_parameter_extraction_routing_targets(mock_state)
        assert result in valid_targets

        # Test agent routing targets
        mock_state.shared_data.participating_agents_for_parallel = [
            GENERAL_AGENT_NODE
        ]  # SALES_AGENT_NODE temporarily disabled
        result = _get_agent_routing_targets(mock_state)
        assert all(target in valid_targets for target in result)


if __name__ == "__main__":
    pytest.main([__file__])
