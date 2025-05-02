"""
Unit tests for the explainer service module.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai_book_seeker.services.explainer import explain_recommendation
from ai_book_seeker.services.query import BookPreferences


@patch("ai_book_seeker.services.explainer.openai")
def test_explain_recommendation(mock_openai):
    """Test generating an explanation for a book recommendation."""
    # Mock the OpenAI API call
    mock_chat_completion = MagicMock()
    mock_openai.ChatCompletion.create.return_value = mock_chat_completion
    mock_chat_completion.choices = [MagicMock()]
    mock_chat_completion.choices[0].message.content = "This book is perfect for your interests in space exploration."

    # Create test preferences
    preferences = BookPreferences(query_text="books about space", age="10-12", genre="science")

    # Call the function
    explanation = explain_recommendation("123", preferences)

    # Check that the OpenAI API was called
    mock_openai.ChatCompletion.create.assert_called_once()

    # Check that we got the expected explanation
    assert explanation == "This book is perfect for your interests in space exploration."


@patch("ai_book_seeker.services.explainer.openai")
@patch("ai_book_seeker.services.explainer.load_text_file")
def test_explain_recommendation_with_template(mock_load_text_file, mock_openai):
    """Test generating an explanation with a template."""
    # Mock loading the template
    mock_load_text_file.return_value = "Explain why book {title} by {author} is a good fit for {preferences}"

    # Mock the OpenAI response
    mock_chat_completion = MagicMock()
    mock_openai.ChatCompletion.create.return_value = mock_chat_completion
    mock_chat_completion.choices = [MagicMock()]
    mock_chat_completion.choices[0].message.content = "This fantasy book is appropriate for a 12-year-old."

    # Create test preferences
    preferences = BookPreferences(age="12", genre="fantasy")

    # Call the function
    explanation = explain_recommendation("456", preferences)

    # Check that the OpenAI API was called
    mock_openai.ChatCompletion.create.assert_called_once()

    # Check that we got the expected explanation
    assert explanation == "This fantasy book is appropriate for a 12-year-old."

    # Check that the template was loaded
    mock_load_text_file.assert_called_once()


@patch("ai_book_seeker.services.explainer.openai")
def test_explain_recommendation_error_handling(mock_openai):
    """Test error handling in the explain_recommendation function."""
    # Mock an error from the OpenAI API
    mock_openai.ChatCompletion.create.side_effect = Exception("API error")

    # Create test preferences
    preferences = BookPreferences(age="teen", purpose="learning")

    # Call the function
    explanation = explain_recommendation("789", preferences)

    # Check that we got an error message
    assert "Error" in explanation
    assert "API error" in explanation
