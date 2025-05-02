"""
Validation tools for metadata extraction.
"""

from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session

from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.db.models import Book
from ai_book_seeker.metadata_extraction.schema import MetadataOutput

# Initialize logger
logger = get_logger(__name__)


def validate_metadata(raw: Dict[str, Any]) -> MetadataOutput:
    """
    Validate and normalize metadata by directly
    using the Pydantic schema.
    """
    try:
        return MetadataOutput.model_validate(raw)
    except Exception as e:
        logger.error(f"Metadata validation failed: {e}")
        raise


def insert_book_metadata(db: Session, metadata: Union[Dict[str, Any], MetadataOutput]) -> Optional[int]:
    """
    Insert normalized metadata into the database.

    Args:
        db: SQLAlchemy database session
        metadata: Metadata to insert, either as a dict or MetadataOutput object

    Returns:
        Optional[int]: The ID of the inserted book, or None if insertion failed
    """
    if isinstance(metadata, dict):
        book_data = metadata
    else:
        # Convert NormalizedMetadata to dict
        book_data = metadata.normalized_metadata.model_dump()

    # Get valid fields dynamically from the Book model
    valid_fields = {c.name for c in Book.__table__.columns}

    filtered_data = {k: v for k, v in book_data.items() if k in valid_fields}

    # Handle tags separately
    if "tags" in filtered_data:
        filtered_data["tags"] = ",".join(filtered_data["tags"])

    book = Book(**filtered_data)

    # Handle price explicitly
    if getattr(book, "price", None) is None:
        book.price = 0.0

    try:
        db.add(book)
        db.commit()
        db.refresh(book)
        logger.info(f"Inserted book metadata successfully with id: {book.id}")
        return book.id
    except Exception as e:
        logger.error(f"Failed to insert metadata: {e}")
        try:
            db.rollback()
        except Exception as rollback_error:
            logger.error(f"Failed to rollback transaction: {rollback_error}")
        raise  # Re-raise the exception to be handled by the caller
