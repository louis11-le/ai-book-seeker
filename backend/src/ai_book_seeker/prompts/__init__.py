"""
Prompt Management Module for AI Book Seeker

This module manages versioned prompts for the application. It provides
functionality for loading prompt templates based on AppSettings.

All prompt configuration (versions, paths, etc.) is accessed via the centralized AppSettings config object.
Do not use direct environment variable access or hardcoded values; use only AppSettings.
"""

from pathlib import Path
from typing import Dict, Optional

from ai_book_seeker.core.config import AppSettings

# Prompt cache to avoid reading files multiple times
_prompt_cache: Dict[str, str] = {}


def create_prompt_manager(settings: AppSettings) -> "PromptManager":
    """
    Factory function to create a PromptManager instance with the provided settings.

    Args:
        settings: Application settings containing prompt configuration

    Returns:
        PromptManager: Configured prompt manager instance
    """
    return PromptManager(settings)


class PromptManager:
    """Manages versioned prompts for the application."""

    def __init__(self, settings: AppSettings):
        """
        Initialize PromptManager with settings.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self._get_prompt_version = self._create_version_getter()

        # Get prompt versions from AppSettings (type-safe, with fallback)
        self.searcher_version = self._get_prompt_version("searcher_version", "v1")
        self.explainer_version = self._get_prompt_version("explainer_version", "v1")
        self.system_prompt_version = self._get_prompt_version("system_prompt_version", "v1")

    def _create_version_getter(self):
        """Helper to get a prompt version from settings with a fallback."""

        def get_version(attr: str, default: str = "v1") -> str:
            try:
                return getattr(self.settings.prompt_settings, attr)
            except (AttributeError, TypeError):
                return default

        return get_version

    def get_prompt_path(self, prompt_type: str, version: str) -> Path:
        """
        Get the path to a specific prompt file.
        """
        base_dir = Path(__file__).parent
        if prompt_type == "searcher":
            return base_dir / "searcher" / f"search_books_{version}.txt"
        elif prompt_type == "explainer":
            return base_dir / "explainer" / f"explain_recommendation_{version}.txt"
        elif prompt_type == "system":
            return base_dir / "system" / f"system_prompt_{version}.txt"
        else:
            raise ValueError(f"Unknown prompt type: {prompt_type}")

    def load_prompt(self, prompt_type: str, version: Optional[str] = None) -> str:
        """
        Load a prompt from a file.
        """
        # Determine the version to use
        if version is None:
            if prompt_type == "searcher":
                version = self.searcher_version
            elif prompt_type == "explainer":
                version = self.explainer_version
            elif prompt_type == "system":
                version = self.system_prompt_version
            else:
                raise ValueError(f"Unknown prompt type: {prompt_type}")

        # Ensure version is a string (fallback to 'v1' if still None)
        if version is None:
            version = "v1"

        # Create a cache key for this prompt
        cache_key = f"{prompt_type}_{version}"
        # Check if the prompt is already in cache
        if cache_key in _prompt_cache:
            return _prompt_cache[cache_key]
        # Get the path to the prompt file
        prompt_path = self.get_prompt_path(prompt_type, version)
        # Read the prompt file
        try:
            with open(prompt_path, "r") as f:
                prompt = f.read()
            _prompt_cache[cache_key] = prompt
            return prompt
        except FileNotFoundError:
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    def get_searcher_prompt(self) -> str:
        """
        Get the current searcher prompt.
        """
        return self.load_prompt("searcher", self.searcher_version)

    def get_explainer_prompt(self) -> str:
        """
        Get the current explainer prompt.
        """
        return self.load_prompt("explainer", self.explainer_version)

    def get_system_prompt(self) -> str:
        """
        Get the current system prompt.
        """
        return self.load_prompt("system", self.system_prompt_version)
