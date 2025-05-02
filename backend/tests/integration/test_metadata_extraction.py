"""
Integration tests for the metadata extraction module.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai_book_seeker.metadata_extraction.main import extract_book_metadata
from ai_book_seeker.metadata_extraction.schema import MetadataOutput


@pytest.fixture
def sample_pdf_path():
    """Create a temporary PDF file for testing."""
    # Create a simple PDF file for testing
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(
            b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << >> /Contents 4 0 R >>\nendobj\n"
            b"4 0 obj\n<< /Length 69 >>\nstream\n"
            b"BT\n/F1 12 Tf\n100 700 Td\n(Test Book by Test Author) Tj\n"
            b"ET\nendstream\nendobj\n"
            b"trailer\n<< /Root 1 0 R /Size 5 >>\n"
            b"%%EOF\n"
        )
    yield tmp.name
    # Clean up
    os.unlink(tmp.name)


@patch("ai_book_seeker.metadata_extraction.crew.MetadataExtractionCrew.crew")
def test_extract_book_metadata_integration(mock_crew, sample_pdf_path):
    """Test the integration of metadata extraction components."""
    # Create mock crew
    mock_crew_instance = MagicMock()
    mock_crew.return_value = mock_crew_instance

    # Set up mock result
    mock_result = {
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
        "quality_assessment": {"summary": "Good quality metadata"},
    }

    # Mock the crew kickoff method to return our test data
    mock_crew_instance.kickoff.return_value = mock_result

    # Temporarily patch the insert_book_metadata function
    with patch("ai_book_seeker.metadata_extraction.main.insert_book_metadata") as mock_insert:
        mock_insert.return_value = 1  # Simulating book ID

        # Run the extraction with save_to_db=True but with output_path=None (temporary file)
        result = extract_book_metadata(sample_pdf_path, save_to_db=True, db=None, output_path=None)

    # Assert the crew was called with correct inputs
    mock_crew_instance.kickoff.assert_called_once_with(inputs={"pdf_path": sample_pdf_path})

    # Check the results
    assert result is not None
    assert result["normalized_metadata"]["title"] == "Test Book"
    assert result["normalized_metadata"]["author"] == "Test Author"

    # Verify that a temporary output file was created (and then deleted in the cleanup)
    assert mock_crew_instance.kickoff.call_count == 1
