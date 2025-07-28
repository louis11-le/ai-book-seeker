"""
API Endpoints for Book Metadata Extraction

This module provides FastAPI endpoints for extracting metadata from PDF book files.

All configuration (e.g., temp file directory, feature flags) should be accessed via the centralized AppSettings config object.
Do not use direct environment variable access or hardcoded values; use only AppSettings.
"""

import os
import tempfile
from typing import Dict

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from ai_book_seeker.core.config import AppSettings
from ai_book_seeker.core.dependencies import get_app_settings
from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.metadata_extraction.main import extract_book_metadata

# Set up logging
logger = get_logger("metadata_extraction_api")

# Create router
router = APIRouter(prefix="/metadata", tags=["metadata"])


@router.post("/extract", status_code=status.HTTP_201_CREATED)
async def extract_metadata(
    file: UploadFile = File(...),
    settings: AppSettings = Depends(get_app_settings),
) -> Dict:
    """
    Extract metadata from a PDF book file and save it to the database.

    Args:
        file: Uploaded PDF file
        settings: Application settings containing configuration

    Returns:
        Dictionary containing the extracted metadata

    Raises:
        HTTPException: If the uploaded file is not a PDF or metadata extraction fails

    All configuration (e.g., temp file directory) should be accessed via AppSettings.
    """
    # Check if the file is a PDF
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a PDF",
        )

    # Create a temporary file (directory can be made configurable via AppSettings if needed)
    try:
        temp_dir = getattr(settings.metadata_extraction, "temp_dir", None)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", dir=temp_dir) as temp_file:
            # Write the uploaded file to the temporary file
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        # Extract metadata
        metadata = extract_book_metadata(temp_path, settings, save_to_db=True)

        # Remove the temporary file
        os.unlink(temp_path)

        # Check if metadata extraction succeeded
        if metadata is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to extract metadata from the PDF",
            )

        return metadata
    except Exception as e:
        logger.error(f"Error processing PDF file: {str(e)}", exc_info=True)
        # Ensure temporary file is cleaned up
        if "temp_path" in locals():
            try:
                os.unlink(temp_path)
            except OSError as cleanup_error:
                logger.error(f"Failed to remove temporary file: {str(cleanup_error)}", exc_info=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing PDF file: {str(e)}",
        )
