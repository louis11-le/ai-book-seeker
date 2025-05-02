"""
Unit tests for metadata validation tools.
"""

import pytest
from pydantic import ValidationError

from ai_book_seeker.metadata_extraction.schema import MetadataOutput
from ai_book_seeker.metadata_extraction.tools.validation_tools import validate_metadata


def test_validate_metadata_success():
    """Test successful validation of metadata."""
    # Create a valid metadata dictionary
    metadata = {
        "normalized_metadata": {
            "title": "Test Book",
            "author": "Test Author",
            "description": "A test book description",
            "age_range": "8-12",
            "purpose": "learning",
            "genre": "fiction",
            "tags": ["test", "sample"],
            "publication_details": {
                "publisher": "Test Publisher",
                "publication_date": "2023-01-01",
                "isbn": "1234567890",
            },
            "language": "English",
            "target_audience": {"age_range": "8-12", "from_age": 8, "to_age": 12},
        },
        "validation_status": {
            "is_valid": True,
            "missing_fields": [],
            "valid_fields": ["title", "author", "description"],
        },
        "error_reports": {"errors": {}, "warnings": {}},
        "confidence_scores": {"overall": 0.95, "fields": {"title": 0.99, "author": 0.98}},
        "quality_assessment": {"summary": "Good quality metadata with high confidence"},
    }

    # Validate the metadata
    result = validate_metadata(metadata)

    # Check that the validation succeeded
    assert result is not None
    assert isinstance(result, MetadataOutput)
    assert result.normalized_metadata.title == "Test Book"
    assert result.normalized_metadata.author == "Test Author"
    assert result.validation_status.is_valid == True
    assert result.confidence_scores.overall == 0.95


def test_validate_metadata_missing_required_field():
    """Test validation with missing required field."""
    # Create a metadata dictionary with a missing required field
    metadata = {
        "normalized_metadata": {
            # Missing title field
            "author": "Test Author",
            "description": "A test book description",
            "age_range": "8-12",
            "purpose": "learning",
            "genre": "fiction",
            "tags": ["test", "sample"],
            "publication_details": {"publisher": "Test Publisher"},
            "language": "English",
            "target_audience": {"age_range": "8-12"},
        },
        "validation_status": {
            "is_valid": False,
            "missing_fields": ["title"],
            "valid_fields": ["author", "description"],
        },
        "error_reports": {"errors": {"title": "Missing required field"}, "warnings": {}},
        "confidence_scores": {"overall": 0.8, "fields": {}},
        "quality_assessment": {"summary": "Missing required field: title"},
    }

    # Validation should raise a ValidationError
    with pytest.raises(ValidationError):
        validate_metadata(metadata)
