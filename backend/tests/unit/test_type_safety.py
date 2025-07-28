"""
Unit tests for type safety utilities.
"""

import pytest
from ai_book_seeker.workflows.schemas.agents import AgentResults
from ai_book_seeker.workflows.schemas.state import SharedData
from ai_book_seeker.workflows.utils.type_safety import (
    ensure_type_safety,
    validate_merge_function,
)


class TestRuntimeValidationDecorators:
    """Test runtime validation decorators."""

    def test_validate_merge_function_success(self):
        """Test successful merge function validation."""

        @validate_merge_function
        def test_merge(left: AgentResults, right: AgentResults) -> AgentResults:
            return left

        left = AgentResults()
        right = AgentResults()
        result = test_merge(left, right)
        assert isinstance(result, AgentResults)

    def test_validate_merge_function_wrong_type(self):
        """Test merge function validation with wrong types."""

        @validate_merge_function
        def test_merge(left: AgentResults, right: AgentResults) -> AgentResults:
            return left

        left = AgentResults()
        right = "not_agent_results"

        with pytest.raises(TypeError, match="Right parameter must be"):
            test_merge(left, right)

    def test_validate_merge_function_different_types(self):
        """Test merge function validation with different input types."""

        @validate_merge_function
        def test_merge(left: AgentResults, right: AgentResults) -> AgentResults:
            return left

        left = AgentResults()
        right = SharedData()

        with pytest.raises(TypeError, match="Both parameters must be of the same type"):
            test_merge(left, right)


class TestTypeValidationDecorators:
    """Test type validation decorators."""

    def test_ensure_type_safety(self):
        """Test ensure_type_safety decorator."""

        @ensure_type_safety
        def test_merge(left: AgentResults, right: AgentResults) -> AgentResults:
            return left

        left = AgentResults()
        right = AgentResults()
        result = test_merge(left, right)
        assert isinstance(result, AgentResults)


class TestIntegrationScenarios:
    """Test integration scenarios for type safety."""

    def test_full_type_safety_pipeline(self):
        """Test the complete type safety pipeline."""
        # Create test data
        left_results = AgentResults()
        right_results = AgentResults()

        # Test type-safe merge function
        @ensure_type_safety
        def test_merge(left: AgentResults, right: AgentResults) -> AgentResults:
            return left

        # Execute merge
        result = test_merge(left_results, right_results)

        # Verify result
        assert isinstance(result, AgentResults)

    def test_type_safety_error_handling(self):
        """Test type safety error handling."""

        @ensure_type_safety
        def test_merge(left: AgentResults, right: AgentResults) -> AgentResults:
            return left

        left = AgentResults()
        right = "not_agent_results"

        with pytest.raises(TypeError):
            test_merge(left, right)
