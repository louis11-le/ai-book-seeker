from pathlib import Path
from typing import List, Tuple

import pytest
import pytest_asyncio
from ai_book_seeker.features.search_faq.faq_service import FAQService
from ai_book_seeker.features.search_faq.handler import faq_handler
from ai_book_seeker.features.search_faq.schema import FAQOutputSchema, FAQSchema

KB_DIR = "src/ai_book_seeker/prompts/voice_assistant/elevenlabs/knowledge_base"
GIFTS_FILE = Path(KB_DIR) / "knowledge_base_gifts_and_gift_services.txt"


@pytest.fixture(scope="module")
def faq_service() -> FAQService:
    return FAQService(KB_DIR)


@pytest.fixture
def empty_kb_dir(tmp_path) -> Path:
    d = tmp_path / "empty_kb"
    d.mkdir()
    return d


@pytest_asyncio.fixture(scope="module")
async def async_faq_service():
    service = await FAQService.async_init(KB_DIR)
    yield service


@pytest.mark.parametrize(
    "faq_file,expected",
    [
        (
            GIFTS_FILE,
            [
                ("Do you offer gift wrapping?", "Yes, we offer complimentary gift wrapping."),
                ("Can I buy a gift card?", "Yes, gift cards are available in-store and online."),
                (
                    "Can I include a personalized message with a gift?",
                    "Yes, we can include a handwritten note with your gift.",
                ),
            ],
        ),
    ],
)
def test_parse_well_formed_faq_file(faq_service: FAQService, faq_file: Path, expected: List[Tuple[str, str]]):
    """Test parsing a well-formed FAQ file."""
    parsed = faq_service._parse_faq_file(faq_file)
    assert parsed == expected


def test_get_all_faqs(faq_service: FAQService):
    """Test loading all FAQs from the knowledge base."""
    faqs = faq_service.get_all_faqs()
    assert isinstance(faqs, dict)
    assert "knowledge_base_gifts_and_gift_services" in faqs
    assert any("gift wrapping" in q for q, _ in faqs["knowledge_base_gifts_and_gift_services"])


@pytest.mark.parametrize(
    "query,expected_found",
    [
        ("gift wrapping", True),
        ("gift card", True),
        ("nonexistent question", False),
    ],
)
def test_search_faqs_exact_and_partial(faq_service: FAQService, query: str, expected_found: bool):
    """Test FAQ keyword search for exact, partial, and no match."""
    results = faq_service.search_faqs(query)
    found = any(query in q for _, q, _ in results)
    assert found == expected_found


def test_search_faqs_empty_kb(empty_kb_dir: Path):
    """Test searching an empty knowledge base directory."""
    service = FAQService(str(empty_kb_dir))
    assert service.get_all_faqs() == {}
    assert service.search_faqs("anything") == []


@pytest.mark.asyncio
async def test_semantic_search_faqs_basic(async_faq_service):
    """Test semantic search returns relevant results for a real query."""
    query = "gift wrapping"
    try:
        results = await async_faq_service.semantic_search_faqs_async(query, top_k=3, threshold=0.1)
    except Exception as e:
        pytest.skip(f"OpenAI API not available: {e}")

    assert results, f"No results returned for query: {query}"
    top_result = results[0]
    assert (
        "gift wrapping" in top_result[1].lower() or "gift wrapping" in top_result[2].lower()
    ), f"Top result not relevant: {top_result}"


@pytest.mark.asyncio
async def test_semantic_search_faqs_no_results(async_faq_service):
    """Test semantic search returns no results for an irrelevant query."""
    query = "this query should not match anything in the FAQ knowledge base"
    try:
        results = await async_faq_service.semantic_search_faqs_async(query, top_k=3, threshold=0.5)
    except Exception as e:
        pytest.skip(f"OpenAI API not available: {e}")
    assert results == [], f"Expected no results, but got: {results}"


def test_parse_malformed_faq_file(tmp_path: Path):
    """Test parsing a malformed FAQ file (missing A: line)."""
    malformed_file = tmp_path / "malformed.txt"
    malformed_file.write_text("Q: Only a question without answer\n\nQ: Another?\nA: Answer here\n")
    service = FAQService(str(tmp_path))
    parsed = service._parse_faq_file(malformed_file)
    assert ("Only a question without answer", "") not in parsed
    assert ("Another?", "Answer here") in parsed


@pytest.mark.asyncio
async def test_faq_handler_valid_query(monkeypatch):
    # Patch FAQService to return a known result
    class DummyService:
        async def semantic_search_faqs_async(self, query, top_k, threshold):
            return [("cat", "Q1", "A1", 0.9)]

        def search_faqs(self, query):
            return [("cat", "Q2", "A2")]

    monkeypatch.setattr("ai_book_seeker.features.search_faq.handler.FAQService", lambda kb_dir: DummyService())
    req = FAQSchema(query="test")
    result = await faq_handler(req)
    assert isinstance(result, FAQOutputSchema)
    assert result.text.startswith("Q: ")
    assert len(result.data) == 2


@pytest.mark.asyncio
async def test_faq_handler_no_results(monkeypatch):
    class DummyService:
        async def semantic_search_faqs_async(self, query, top_k, threshold):
            return []

        def search_faqs(self, query):
            return []

    monkeypatch.setattr("ai_book_seeker.features.search_faq.handler.FAQService", lambda kb_dir: DummyService())
    req = FAQSchema(query="noresults")
    result = await faq_handler(req)
    assert isinstance(result, FAQOutputSchema)
    assert result.text.startswith("Sorry")
    assert result.data == []


@pytest.mark.asyncio
async def test_faq_handler_empty_query():
    with pytest.raises(Exception):
        await faq_handler(FAQSchema(query="   "))


@pytest.mark.asyncio
async def test_faq_handler_internal_error(monkeypatch):
    class DummyService:
        async def semantic_search_faqs_async(self, query, top_k, threshold):
            raise RuntimeError("Simulated error")

        def search_faqs(self, query):
            return []

    monkeypatch.setattr("ai_book_seeker.features.search_faq.handler.FAQService", lambda kb_dir: DummyService())
    req = FAQSchema(query="error")
    result = await faq_handler(req)
    assert isinstance(result, FAQOutputSchema)
    assert result.text.startswith("Internal error")
    assert result.data == []


@pytest.mark.asyncio
async def test_faq_handler_malformed_input():
    # Malformed input: missing required field
    with pytest.raises(Exception):
        await faq_handler({})
