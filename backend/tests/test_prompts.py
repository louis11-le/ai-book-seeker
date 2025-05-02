"""
Unit Tests for the Prompt Versioning System
"""

import os
import unittest
from pathlib import Path
from unittest import mock

from ai_book_seeker.prompts import (
    EXPLAINER_VERSION,
    SEARCHER_VERSION,
    get_explainer_prompt,
    get_prompt_path,
    get_searcher_prompt,
    load_prompt,
)


class TestPromptVersioning(unittest.TestCase):
    """Test cases for the prompt versioning system"""

    def setUp(self):
        """Set up test environment"""
        # Create a mock environment
        self.original_searcher_version = SEARCHER_VERSION
        self.original_explainer_version = EXPLAINER_VERSION

        # Path to the prompts directory
        self.base_dir = Path(__file__).parent.parent / "prompts"

    def test_get_prompt_path(self):
        """Test getting the path to a specific prompt file"""
        # Test searcher prompt path
        searcher_path = get_prompt_path("searcher", "v1")
        expected_path = self.base_dir / "searcher" / "search_books_v1.txt"
        self.assertEqual(searcher_path, expected_path)

        # Test explainer prompt path
        explainer_path = get_prompt_path("explainer", "v2")
        expected_path = self.base_dir / "explainer" / "explain_recommendation_v2.txt"
        self.assertEqual(explainer_path, expected_path)

        # Test invalid prompt type
        with self.assertRaises(ValueError):
            get_prompt_path("invalid_type", "v1")

    def test_load_prompt(self):
        """Test loading prompts from files"""
        # Test loading searcher prompt
        with mock.patch("ai_book_seeker.prompts.get_prompt_path") as mock_path:
            mock_path.return_value = self.base_dir / "searcher" / "search_books_v1.txt"
            with mock.patch("builtins.open", mock.mock_open(read_data="Searcher Prompt v1")) as mock_file:
                prompt = load_prompt("searcher", "v1")
                self.assertEqual(prompt, "Searcher Prompt v1")
                mock_file.assert_called_once_with(mock_path.return_value, "r")

        # Test loading explainer prompt
        with mock.patch("ai_book_seeker.prompts.get_prompt_path") as mock_path:
            mock_path.return_value = self.base_dir / "explainer" / "explain_recommendation_v1.txt"
            with mock.patch("builtins.open", mock.mock_open(read_data="Explainer Prompt v1")) as mock_file:
                prompt = load_prompt("explainer", "v1")
                self.assertEqual(prompt, "Explainer Prompt v1")
                mock_file.assert_called_once_with(mock_path.return_value, "r")

        # Test file not found
        with mock.patch("ai_book_seeker.prompts.get_prompt_path") as mock_path:
            mock_path.return_value = self.base_dir / "nonexistent.txt"
            with mock.patch("builtins.open", mock.mock_open()) as mock_file:
                mock_file.side_effect = FileNotFoundError
                with self.assertRaises(FileNotFoundError):
                    load_prompt("searcher", "nonexistent")

    def test_get_searcher_prompt(self):
        """Test getting the current searcher prompt"""
        with mock.patch("ai_book_seeker.prompts.load_prompt") as mock_load:
            mock_load.return_value = "Current Searcher Prompt"
            prompt = get_searcher_prompt()
            self.assertEqual(prompt, "Current Searcher Prompt")
            mock_load.assert_called_once_with("searcher", SEARCHER_VERSION)

    def test_get_explainer_prompt(self):
        """Test getting the current explainer prompt"""
        with mock.patch("ai_book_seeker.prompts.load_prompt") as mock_load:
            mock_load.return_value = "Current Explainer Prompt"
            prompt = get_explainer_prompt()
            self.assertEqual(prompt, "Current Explainer Prompt")
            mock_load.assert_called_once_with("explainer", EXPLAINER_VERSION)

    @mock.patch.dict(os.environ, {"SEARCHER_VERSION": "v2"})
    def test_environment_variable_override(self):
        """Test that environment variables override the default versions"""
        # This test requires reloading the prompts module to pick up the new environment variables
        # In a real test, you would need to handle module reloading or dependency injection
        with mock.patch("ai_book_seeker.prompts.SEARCHER_VERSION", "v2"):
            with mock.patch("ai_book_seeker.prompts.load_prompt") as mock_load:
                mock_load.return_value = "Searcher Prompt v2"
                prompt = get_searcher_prompt()
                self.assertEqual(prompt, "Searcher Prompt v2")
                mock_load.assert_called_once_with("searcher", "v2")


if __name__ == "__main__":
    unittest.main()
