"""
Test helpers for AI Book Seeker.

This module provides mock objects and utilities for testing.
"""

import json
from typing import Any


class MockResponse:
    """Mock response object for testing."""

    def __init__(self, content: Any):
        if isinstance(content, dict):
            self.content = json.dumps(content)
        else:
            self.content = str(content)


class MockLLM:
    """Mock LLM for testing - always returns valid responses."""

    async def ainvoke(self, prompt: str) -> MockResponse:
        """Mock LLM invocation that returns structured responses."""
        # Return structured responses for different prompt types
        if "routing" in prompt.lower():
            return MockResponse(
                {
                    "next_node": "general_agent",
                    "participating_agents": ["general_agent"],
                    "is_multi_purpose": False,
                    "is_multi_agent": False,
                    "query_intents": {
                        "faq_requests": [],
                        "book_recommendations": [],
                        "product_inquiries": [],
                        "sales_requests": [],
                    },
                    "reasoning": "Mock routing analysis",
                    "confidence": 0.9,
                }
            )
        elif "parameter" in prompt.lower():
            return MockResponse(
                {
                    "faq_query": "test question",
                    "age": 25,
                    "genre": "fiction",
                    "budget": 20.0,
                    "purpose": "entertainment",
                    "interests": ["adventure", "mystery"],
                    "title": None,
                    "author": None,
                    "isbn": None,
                }
            )
        elif "tool selection" in prompt.lower() or "tools are needed" in prompt.lower():
            return MockResponse(
                {"selected_tools": ["faq_tool"], "reasoning": "Mock tool selection analysis", "confidence": 0.85}
            )
        else:
            # Default response for unknown prompts
            return MockResponse({"result": "mock response", "reasoning": "Mock analysis", "confidence": 0.8})


class MockSettings:
    """Mock settings object for testing."""

    def __init__(self):
        self.openai = MockOpenAISettings()
        self.redis = MockRedisSettings()
        self.vectordb = MockVectordbSettings()


class MockOpenAISettings:
    """Mock OpenAI settings for testing."""

    def __init__(self):
        self.model_name = "gpt-3.5-turbo"
        self.temperature = 0.7
        self.api_key = MockSecretStr("test-api-key")


class MockRedisSettings:
    """Mock Redis settings for testing."""

    def __init__(self):
        self.url = "redis://localhost:6379"
        self.ttl = 3600


class MockVectordbSettings:
    """Mock VectorDB settings for testing."""

    def __init__(self):
        self.path = "/tmp/test_vectordb"
        self.collection_name = "test_collection"


class MockSecretStr:
    """Mock secret string for testing."""

    def __init__(self, value: str):
        self._value = value

    def get_secret_value(self) -> str:
        return self._value


def create_test_book(**kwargs):
    """
    Create a test book with default values that can be overridden.

    Args:
        **kwargs: Override default values for the book

    Returns:
        Book: A test book instance
    """
    from ai_book_seeker.db.models import Book

    defaults = {
        "title": "Test Book",
        "author": "Test Author",
        "publication_year": 2023,
        "isbn": "1234567890",
        "description": "A test book for unit testing",
        "price": 19.99,
        "genre": "Test",
        "target_age": "8-12",
        "metadata": {"tags": ["test", "sample"]},
        "vector_id": "test123",
    }

    # Override defaults with provided kwargs
    defaults.update(kwargs)

    return Book(**defaults)
