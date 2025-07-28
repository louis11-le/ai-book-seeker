"""
Dependency injection utilities for the AI Book Seeker application.

This module provides FastAPI dependency functions that can be imported
without creating circular imports.
"""

from fastapi import Request

from .config import AppSettings


def get_app_settings(request: Request) -> AppSettings:
    """
    FastAPI dependency to get application settings from request state.

    This function retrieves the centralized AppSettings instance from
    the FastAPI application state, ensuring a single source of truth
    for all configuration.

    Args:
        request: FastAPI request object containing app state

    Returns:
        AppSettings: Centralized application settings

    Raises:
        RuntimeError: If settings are not available in app state
    """
    if not hasattr(request.app.state, "config"):
        raise RuntimeError("Application settings not available in app state")
    return request.app.state.config
