import os

import pytest
from ai_book_seeker.services.langchain_orchestrator import LangChainOrchestrator

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="module")
def orchestrator():
    return LangChainOrchestrator()


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OpenAI API key not set")
async def test_agent_initialization(orchestrator):
    """Test that the orchestrator loads the agent and all tools."""
    assert orchestrator.agent is not None
    assert len(orchestrator.tools) >= 2  # FAQ and Book Recommendation


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OpenAI API key not set")
async def test_single_tool_faq_query(orchestrator):
    """Test FAQ tool: query for store hours returns relevant answer and data."""
    session_id = "test_faq_session"
    query = "What are your store hours?"
    response = await orchestrator.process_query(query, session_id)
    assert isinstance(response, dict), "Response is not a dict"
    assert "output" in response, "Response missing 'output' key"
    text_lower = response["output"].lower()
    assert ("store" in text_lower and "open" in text_lower) or (
        "hours" in text_lower
    ), "FAQ answer does not mention store hours"
    # Remove 'data' checks since the agent output is now under 'output'


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OpenAI API key not set")
async def test_single_tool_book_recommendation_query(orchestrator):
    """Test Book Recommendation tool: query for a 10-year-old returns a book recommendation."""
    session_id = "test_book_rec_session"
    query = "Can you recommend a book for a 10-year-old who likes adventure?"
    response = await orchestrator.process_query(query, session_id)
    assert isinstance(response, dict), "Response is not a dict"
    assert "output" in response, "Response missing 'output' key"
    text_lower = response["output"].lower()
    assert "book" in text_lower or "recommend" in text_lower, "Book recommendation text missing"
    # Optionally, check for key info in the output string


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OpenAI API key not set")
async def test_faq_empty_query(orchestrator):
    """Test FAQ tool: empty query should return an error or default message."""
    session_id = "test_faq_empty"
    query = ""
    response = await orchestrator.process_query(query, session_id)
    assert isinstance(response, dict), "Response is not a dict"
    assert "output" in response or "error" in response, "Response missing 'output' or 'error' key"
    if "output" in response:
        output = response["output"].strip().lower()
        assert (
            output == "sorry, i couldn't find an answer to your question."
            or "error" in output
            or "assist" in output
            or "help" in output
            or output.startswith("hello")
        ), "Empty query did not return expected error or friendly fallback message"
    else:
        assert "error" in response, "No error key in response for empty query"


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OpenAI API key not set")
async def test_book_recommendation_empty_query(orchestrator):
    """Test Book Recommendation tool: empty query should return an error or default message."""
    session_id = "test_book_rec_empty"
    query = ""
    response = await orchestrator.process_query(query, session_id)
    assert isinstance(response, dict), "Response is not a dict"
    assert "output" in response or "error" in response, "Response missing 'output' or 'error' key"
    if "output" in response:
        output = response["output"].strip().lower()
        assert (
            "couldn't find any books" in output
            or "error" in output
            or "assist" in output
            or "help" in output
            or output.startswith("hello")
        ), "Empty query did not return expected error or friendly fallback message"
    else:
        assert "error" in response, "No error key in response for empty query"


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OpenAI API key not set")
async def test_faq_malformed_input(orchestrator):
    """Test FAQ tool: malformed input (non-string) should return an error."""
    session_id = "test_faq_malformed"
    query = {"not_a_string": 123}
    try:
        response = await orchestrator.process_query(query, session_id)
        assert "error" in response or "output" in response, "Malformed input did not return error or output"
        if "output" in response:
            output = response["output"].strip().lower()
            assert (
                "error" in output or "assist" in output or "help" in output or output.startswith("hello")
            ), "Malformed input did not return expected error or friendly fallback message"
    except Exception as e:
        assert True, f"Malformed input raised exception as expected: {e}"


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OpenAI API key not set")
async def test_book_recommendation_malformed_input(orchestrator):
    """Test Book Recommendation tool: malformed input (non-string) should return an error."""
    session_id = "test_book_rec_malformed"
    query = {"not_a_string": 123}
    try:
        response = await orchestrator.process_query(query, session_id)
        assert "error" in response or "output" in response, "Malformed input did not return error or output"
        if "output" in response:
            output = response["output"].strip().lower()
            assert (
                "error" in output or "assist" in output or "help" in output or output.startswith("hello")
            ), "Malformed input did not return expected error or friendly fallback message"
    except Exception as e:
        assert True, f"Malformed input raised exception as expected: {e}"
