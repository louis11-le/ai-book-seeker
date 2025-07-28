"""
Unit Tests for the Prompt Versioning System

Updated to work with the new PromptManager system.
"""

import os
import unittest
from pathlib import Path
from unittest import mock

from ai_book_seeker.core.config import AppSettings
from ai_book_seeker.prompts import create_prompt_manager


class TestPromptVersioning(unittest.TestCase):
    """Test cases for the prompt versioning system"""

    def setUp(self):
        """Set up test environment"""
        # Create test settings
        self.settings = AppSettings()

        # Path to the prompts directory
        self.base_dir = Path(__file__).parent.parent / "src" / "ai_book_seeker" / "prompts"

    def test_prompt_manager_creation(self):
        """Test creating a PromptManager instance"""
        prompt_manager = create_prompt_manager(self.settings)
        self.assertIsNotNone(prompt_manager)
        self.assertEqual(prompt_manager.searcher_version, "v1")
        self.assertEqual(prompt_manager.explainer_version, "v1")
        self.assertEqual(prompt_manager.system_prompt_version, "v1")

    def test_get_prompt_path(self):
        """Test getting the path to a specific prompt file"""
        prompt_manager = create_prompt_manager(self.settings)

        # Test searcher prompt path
        searcher_path = prompt_manager.get_prompt_path("searcher", "v1")
        expected_path = self.base_dir / "searcher" / "search_books_v1.txt"
        self.assertEqual(searcher_path, expected_path)

        # Test explainer prompt path
        explainer_path = prompt_manager.get_prompt_path("explainer", "v2")
        expected_path = self.base_dir / "explainer" / "explain_recommendation_v2.txt"
        self.assertEqual(explainer_path, expected_path)

        # Test system prompt path
        system_path = prompt_manager.get_prompt_path("system", "v1")
        expected_path = self.base_dir / "system" / "system_prompt_v1.txt"
        self.assertEqual(system_path, expected_path)

        # Test invalid prompt type
        with self.assertRaises(ValueError):
            prompt_manager.get_prompt_path("invalid_type", "v1")

    def test_load_prompt(self):
        """Test loading prompts from files"""
        prompt_manager = create_prompt_manager(self.settings)

        # Test loading searcher prompt
        with mock.patch.object(prompt_manager, "get_prompt_path") as mock_path:
            mock_path.return_value = self.base_dir / "searcher" / "search_books_v1.txt"
            with mock.patch("builtins.open", mock.mock_open(read_data="Searcher Prompt v1")) as mock_file:
                prompt = prompt_manager.load_prompt("searcher", "v1")
                self.assertEqual(prompt, "Searcher Prompt v1")
                mock_file.assert_called_once_with(mock_path.return_value, "r")

        # Test loading explainer prompt
        with mock.patch.object(prompt_manager, "get_prompt_path") as mock_path:
            mock_path.return_value = self.base_dir / "explainer" / "explain_recommendation_v1.txt"
            with mock.patch("builtins.open", mock.mock_open(read_data="Explainer Prompt v1")) as mock_file:
                prompt = prompt_manager.load_prompt("explainer", "v1")
                self.assertEqual(prompt, "Explainer Prompt v1")
                mock_file.assert_called_once_with(mock_path.return_value, "r")

        # Test file not found
        with mock.patch.object(prompt_manager, "get_prompt_path") as mock_path:
            mock_path.return_value = self.base_dir / "nonexistent.txt"
            with mock.patch("builtins.open", mock.mock_open()) as mock_file:
                mock_file.side_effect = FileNotFoundError
                with self.assertRaises(FileNotFoundError):
                    prompt_manager.load_prompt("searcher", "nonexistent")

    def test_get_searcher_prompt(self):
        """Test getting the current searcher prompt"""
        prompt_manager = create_prompt_manager(self.settings)

        with mock.patch.object(prompt_manager, "load_prompt") as mock_load:
            mock_load.return_value = "Current Searcher Prompt"
            prompt = prompt_manager.get_searcher_prompt()
            self.assertEqual(prompt, "Current Searcher Prompt")
            mock_load.assert_called_once_with("searcher", "v1")

    def test_get_explainer_prompt(self):
        """Test getting the current explainer prompt"""
        prompt_manager = create_prompt_manager(self.settings)

        with mock.patch.object(prompt_manager, "load_prompt") as mock_load:
            mock_load.return_value = "Current Explainer Prompt"
            prompt = prompt_manager.get_explainer_prompt()
            self.assertEqual(prompt, "Current Explainer Prompt")
            mock_load.assert_called_once_with("explainer", "v1")

    def test_get_system_prompt(self):
        """Test getting the current system prompt"""
        prompt_manager = create_prompt_manager(self.settings)

        with mock.patch.object(prompt_manager, "load_prompt") as mock_load:
            mock_load.return_value = "Current System Prompt"
            prompt = prompt_manager.get_system_prompt()
            self.assertEqual(prompt, "Current System Prompt")
            mock_load.assert_called_once_with("system", "v1")

    def test_environment_variable_override(self):
        """Test that environment variables override the default versions"""
        # Set environment variables - only use versions that exist
        os.environ["PROMPT_EXPLAINER_VERSION"] = "v2"  # This version exists

        try:
            # Create new settings with environment variables
            settings = AppSettings()
            prompt_manager = create_prompt_manager(settings)

            # Test that explainer version is updated (others remain default)
            self.assertEqual(prompt_manager.searcher_version, "v1")  # v2 doesn't exist for searcher
            self.assertEqual(prompt_manager.explainer_version, "v2")  # v2 exists for explainer
            self.assertEqual(prompt_manager.system_prompt_version, "v1")  # v2 doesn't exist for system

            # Test prompt loading with new version
            with mock.patch.object(prompt_manager, "load_prompt") as mock_load:
                mock_load.return_value = "Explainer Prompt v2"
                prompt = prompt_manager.get_explainer_prompt()
                self.assertEqual(prompt, "Explainer Prompt v2")
                mock_load.assert_called_once_with("explainer", "v2")

        finally:
            # Clean up environment variables
            if "PROMPT_EXPLAINER_VERSION" in os.environ:
                del os.environ["PROMPT_EXPLAINER_VERSION"]

    def test_prompt_settings_fallback(self):
        """Test that PromptSettings fallback works when prompt field is missing"""
        # Create settings without prompt field
        settings = AppSettings()

        # Mock the prompt field to be None
        with mock.patch.object(settings, "prompt", None):
            prompt_manager = create_prompt_manager(settings)

            # Should fallback to default versions
            self.assertEqual(prompt_manager.searcher_version, "v1")
            self.assertEqual(prompt_manager.explainer_version, "v1")
            self.assertEqual(prompt_manager.system_prompt_version, "v1")

    def test_prompt_caching(self):
        """Test that prompts are cached correctly"""
        from ai_book_seeker.prompts import _prompt_cache

        # Clear the cache before testing
        _prompt_cache.clear()

        prompt_manager = create_prompt_manager(self.settings)

        # Mock file reading
        with mock.patch("builtins.open", mock.mock_open(read_data="Test Prompt")):
            # Load the same prompt twice
            prompt1 = prompt_manager.load_prompt("searcher", "v1")
            prompt2 = prompt_manager.load_prompt("searcher", "v1")

            # Both should be the same
            self.assertEqual(prompt1, prompt2)
            self.assertEqual(prompt1, "Test Prompt")

    def test_prompt_settings_validation(self):
        """Test PromptSettings validation functionality"""
        from ai_book_seeker.core.config import PromptSettings

        # Test valid settings
        valid_settings = PromptSettings()
        self.assertEqual(valid_settings.system_prompt_version, "v1")
        self.assertEqual(valid_settings.explainer_version, "v1")
        self.assertEqual(valid_settings.searcher_version, "v1")

        # Test available versions
        available_versions = valid_settings.get_available_versions()
        self.assertIn("system", available_versions)
        self.assertIn("explainer", available_versions)
        self.assertIn("searcher", available_versions)
        self.assertIn("v1", available_versions["system"])
        self.assertIn("v1", available_versions["explainer"])
        self.assertIn("v2", available_versions["explainer"])
        self.assertIn("v1", available_versions["searcher"])

        # Test validation results
        validation_results = valid_settings.validate_all_versions()
        self.assertTrue(validation_results["system"])
        self.assertTrue(validation_results["explainer"])
        self.assertTrue(validation_results["searcher"])

        # Test invalid version format
        with self.assertRaises(ValueError):
            PromptSettings(system_prompt_version="invalid")

        # Test non-existent version
        with self.assertRaises(ValueError):
            PromptSettings(system_prompt_version="v999")

        # Test valid custom version
        custom_settings = PromptSettings(explainer_version="v2")
        self.assertEqual(custom_settings.explainer_version, "v2")


if __name__ == "__main__":
    unittest.main()
