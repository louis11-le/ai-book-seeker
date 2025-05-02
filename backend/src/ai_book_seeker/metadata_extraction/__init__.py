"""
Book Metadata Extraction Module

This module implements the extraction of metadata from PDF book files
using a crew of specialized agents.
"""

from .api import router as metadata_router
from .main import extract_book_metadata

__all__ = ["extract_book_metadata", "metadata_router"]
