"""
Tests to validate that LLM is required throughout the system.

These tests ensure that the system fails fast when LLM is missing,
rather than falling back to basic implementations.
"""

import pytest

from ai_book_seeker.workflows.agents.base import BaseAgent
from ai_book_seeker.workflows.nodes.agent_nodes import agent_coordinator_node, supervisor_router_node
from ai_book_seeker.workflows.nodes.parameter_nodes import parameter_extraction_node
from ai_book_seeker.workflows.registration.node_registration import create_agent_node_map
from ai_book_seeker.workflows.routing.analysis import analyze_query_for_routing
from ai_book_seeker.workflows.routing.parameter_extraction import extract_parameters_with_llm
from tests.helpers import MockLLM


class TestLLMRequirements:
    """Test that LLM is required throughout the system."""

    def test_agent_creation_fails_without_llm(self):
        """Test that agent creation fails without LLM."""
        with pytest.raises(TypeError):
            BaseAgent("test_agent", None)

    def test_agent_creation_succeeds_with_llm(self):
        """Test that agent creation succeeds with LLM."""
        mock_llm = MockLLM()
        # This should not raise an error
        agent = BaseAgent("test_agent", mock_llm)
        assert agent.llm == mock_llm

    @pytest.mark.asyncio
    async def test_parameter_extraction_fails_without_llm(self):
        """Test that parameter extraction fails without LLM."""
        from langchain_core.messages import HumanMessage

        from ai_book_seeker.workflows.schemas import AgentState

        # Create a minimal state
        state = AgentState(session_id="test_session", messages=[HumanMessage(content="test query")], shared_data={})

        with pytest.raises(TypeError):
            await parameter_extraction_node(state, None)

    @pytest.mark.asyncio
    async def test_parameter_extraction_succeeds_with_llm(self):
        """Test that parameter extraction succeeds with LLM."""
        from langchain_core.messages import HumanMessage

        from ai_book_seeker.workflows.schemas import AgentState

        # Create a minimal state
        state = AgentState(session_id="test_session", messages=[HumanMessage(content="test query")], shared_data={})

        mock_llm = MockLLM()
        # This should not raise an error
        result = await parameter_extraction_node(state, mock_llm)
        assert result is not None

    @pytest.mark.asyncio
    async def test_routing_analysis_fails_without_llm(self):
        """Test that routing analysis fails without LLM."""
        with pytest.raises(TypeError):
            await analyze_query_for_routing("test query", None, "chat")

    @pytest.mark.asyncio
    async def test_routing_analysis_succeeds_with_llm(self):
        """Test that routing analysis succeeds with LLM."""
        mock_llm = MockLLM()
        # This should not raise an error
        result = await analyze_query_for_routing("test query", mock_llm, "chat")
        assert result is not None
        assert "next_node" in result

    @pytest.mark.asyncio
    async def test_parameter_extraction_with_llm_fails_without_llm(self):
        """Test that extract_parameters_with_llm fails without LLM."""
        with pytest.raises(TypeError):
            await extract_parameters_with_llm("test query", None)

    @pytest.mark.asyncio
    async def test_parameter_extraction_with_llm_succeeds_with_llm(self):
        """Test that extract_parameters_with_llm succeeds with LLM."""
        mock_llm = MockLLM()
        # This should not raise an error
        result = await extract_parameters_with_llm("test query", mock_llm)
        assert result is not None

    def test_create_agent_node_map_fails_without_llm(self):
        """Test that create_agent_node_map fails without LLM."""
        with pytest.raises(TypeError):
            create_agent_node_map(None)

    def test_create_agent_node_map_succeeds_with_llm(self):
        """Test that create_agent_node_map succeeds with LLM."""
        mock_llm = MockLLM()
        # This should not raise an error
        result = create_agent_node_map(mock_llm)
        assert result is not None
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_supervisor_router_node_fails_without_llm(self):
        """Test that supervisor_router_node fails without LLM."""
        from langchain_core.messages import HumanMessage

        from ai_book_seeker.workflows.schemas import AgentState

        # Create a minimal state
        state = AgentState(session_id="test_session", messages=[HumanMessage(content="test query")], shared_data={})

        with pytest.raises(TypeError):
            await supervisor_router_node(state, None)

    @pytest.mark.asyncio
    async def test_agent_coordinator_node_works_without_llm(self):
        """Test that agent_coordinator_node works without LLM (no longer requires it)."""
        from langchain_core.messages import HumanMessage

        from ai_book_seeker.workflows.schemas import AgentState

        # Create a minimal state
        state = AgentState(session_id="test_session", messages=[HumanMessage(content="test query")], shared_data={})

        # This should not raise an error since agent_coordinator_node no longer requires LLM
        result = await agent_coordinator_node(state)
        assert result is not None


class TestMockLLM:
    """Test that MockLLM works correctly for testing."""

    @pytest.mark.asyncio
    async def test_mock_llm_routing_response(self):
        """Test that MockLLM returns valid routing responses."""
        mock_llm = MockLLM()
        result = await analyze_query_for_routing("test query", mock_llm, "chat")

        assert result is not None
        assert "next_node" in result
        assert "participating_agents" in result
        assert "is_multi_purpose" in result
        assert "is_multi_agent" in result
        assert "query_intents" in result
        assert "reasoning" in result
        assert "confidence" in result

    @pytest.mark.asyncio
    async def test_mock_llm_parameter_response(self):
        """Test that MockLLM returns valid parameter responses."""
        mock_llm = MockLLM()
        result = await extract_parameters_with_llm("test query", mock_llm)

        assert result is not None
        assert "faq_query" in result
        assert "age" in result
        assert "genre" in result
        assert "budget" in result
