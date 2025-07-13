"""
Unit tests for the explainer service module.
"""

import pytest
from ai_book_seeker.db.models import Book
from ai_book_seeker.services.explainer import generate_explanations
from ai_book_seeker.services.query import BookPreferences


@pytest.fixture
def preferences() -> BookPreferences:
    return BookPreferences(query_text="books about space", age=10, genre="science")


@pytest.fixture
def mock_book():
    # Minimal Book object with required attributes
    return Book(
        id=123,
        title="Space Adventures",
        author="Jane Doe",
        from_age=10,
        to_age=12,
        purpose="entertainment",
        genre="science",
        description="A thrilling journey through the cosmos.",
        price=12.99,
        tags="space, adventure",
        quantity=1,
    )


@pytest.mark.parametrize(
    "book_id, prefs, expected",
    [
        (
            123,
            BookPreferences(query_text="books about space", age=10, genre="science"),
            "This book is perfect for your interests in space exploration.",
        ),
        (456, BookPreferences(age=12, genre="fantasy"), "This fantasy book is appropriate for a 12-year-old."),
    ],
)
def test_generate_explanations_success(mocker, book_id: int, prefs: BookPreferences, expected: str):
    """Test generating an explanation for a book recommendation (with and without template)."""
    mock_openai = mocker.patch("ai_book_seeker.services.explainer.client")
    mock_load_text_file = mocker.patch(
        "ai_book_seeker.services.explainer.get_explainer_prompt",
        return_value="Explain why book {title} by {author} is a good fit for {preferences}",
    )
    mock_chat_completion = mocker.MagicMock()
    mock_openai.chat.completions.create.return_value = mock_chat_completion
    mock_choice = mocker.MagicMock()
    mock_choice.message.content = f"[BOOK_ID:{book_id}]{expected}[/BOOK_ID]"
    mock_chat_completion.choices = [mock_choice]
    # Create a Book object with the correct id
    book = Book(
        id=book_id,
        title="Test Book",
        author="Test Author",
        from_age=10,
        to_age=12,
        purpose="entertainment",
        genre="science",
        description="A test book.",
        price=10.0,
        tags="test",
        quantity=1,
    )
    explanations = generate_explanations([book], prefs)
    mock_openai.chat.completions.create.assert_called_once()
    assert explanations[book_id] == expected
    mock_load_text_file.assert_called()


def test_generate_explanations_error_handling(mocker, mock_book, preferences: BookPreferences):
    """Test error handling in the generate_explanations function."""
    mock_openai = mocker.patch("ai_book_seeker.services.explainer.client")
    mock_openai.chat.completions.create.side_effect = Exception("API error")
    explanations = generate_explanations([mock_book], preferences)
    assert explanations == {123: "Fallback explanation."}


def test_generate_explanations_template_load_failure(mocker, mock_book, preferences: BookPreferences):
    """Test error handling when template loading fails."""
    mock_openai = mocker.patch("ai_book_seeker.services.explainer.client")
    mocker.patch(
        "ai_book_seeker.services.explainer.get_explainer_prompt", side_effect=FileNotFoundError("template missing")
    )
    mock_chat_completion = mocker.MagicMock()
    mock_openai.chat.completions.create.return_value = mock_chat_completion
    mock_choice = mocker.MagicMock()
    mock_choice.message.content = "[BOOK_ID:123]Fallback explanation.[/BOOK_ID]"
    mock_chat_completion.choices = [mock_choice]
    explanations = generate_explanations([mock_book], preferences)
    assert explanations[123] == "Fallback explanation."


def test_generate_explanations_empty_preferences(mocker, mock_book):
    """Test explanation generation with empty preferences (edge case)."""
    mock_openai = mocker.patch("ai_book_seeker.services.explainer.client")
    mock_chat_completion = mocker.MagicMock()
    mock_openai.chat.completions.create.return_value = mock_chat_completion
    mock_choice = mocker.MagicMock()
    mock_choice.message.content = "[BOOK_ID:123]General recommendation.[/BOOK_ID]"
    mock_chat_completion.choices = [mock_choice]
    empty_prefs = BookPreferences()
    explanations = generate_explanations([mock_book], empty_prefs)
    assert explanations[123] == "General recommendation."
