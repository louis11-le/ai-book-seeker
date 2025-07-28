"""
Agent implementations for workflow orchestration.

This package provides explicit agent classes for different query types:
- GeneralAgent: Handles general queries with FAQ and book recommendation tools
- GeneralVoiceAgent: Handles voice interface queries with book recommendation tools
- SalesAgent: Handles sales-related queries with book details tools
- BaseAgent: Base class providing common agent functionality
"""

from .base import BaseAgent
from .general import GeneralAgent
from .general_voice import GeneralVoiceAgent
from .sales import SalesAgent

__all__ = [
    "BaseAgent",
    "GeneralAgent",
    "GeneralVoiceAgent",
    "SalesAgent",
]
