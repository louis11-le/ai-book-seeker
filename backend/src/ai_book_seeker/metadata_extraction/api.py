"""
API Endpoints for Book Metadata Extraction

This module provides FastAPI endpoints for extracting metadata from PDF book files.
"""

import os
import tempfile
from typing import Dict

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.metadata_extraction.main import extract_book_metadata

# Set up logging
logger = get_logger("metadata_extraction_api")

# Create router
router = APIRouter(prefix="/metadata", tags=["metadata"])


@router.post("/extract", status_code=status.HTTP_201_CREATED)
async def extract_metadata(
    file: UploadFile = File(...),
) -> Dict:
    """
    Extract metadata from a PDF book file and save it to the database.

    Args:
        file: Uploaded PDF file

    Returns:
        Dictionary containing the extracted metadata

    Raises:
        HTTPException: If the uploaded file is not a PDF or metadata extraction fails
    """
    # Check if the file is a PDF
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a PDF",
        )

    # Create a temporary file
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            # Write the uploaded file to the temporary file
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        # Extract metadata
        metadata = extract_book_metadata(temp_path, save_to_db=True)

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
        logger.error(f"Error processing PDF file: {str(e)}")
        # Ensure temporary file is cleaned up
        if "temp_path" in locals():
            try:
                os.unlink(temp_path)
            except OSError as cleanup_error:
                logger.error(f"Failed to remove temporary file: {str(cleanup_error)}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing PDF file: {str(e)}",
        )
