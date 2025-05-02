"""
Command-line scripts for AI Book Seeker.

This package contains utility scripts for various tasks such as:
- Creating embeddings for book content
- Extracting metadata from PDF files
- Other maintenance and utility tasks
"""

from .create_embeddings import main as create_embeddings
from .extract_book_metadata import main as extract_book_metadata

__all__ = ["create_embeddings", "extract_book_metadata"]
