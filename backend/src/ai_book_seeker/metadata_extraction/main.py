"""
Book Metadata Extraction

This module serves as the entry point for the book metadata extraction feature.
It provides functions to extract metadata from PDF book files using a crew of
specialized AI agents.
"""

import json
import os
import traceback
from pathlib import Path
from typing import Dict, Optional, Union

from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.db.database import get_db_session
from ai_book_seeker.metadata_extraction.crew import MetadataExtractionCrew
from ai_book_seeker.metadata_extraction.schema import MetadataOutput
from ai_book_seeker.metadata_extraction.tools.validation_tools import insert_book_metadata

# Set up logging
logger = get_logger(__name__)


def extract_book_metadata(
    pdf_path: str, save_to_db: bool = True, output_path: Optional[str] = None
) -> Optional[Dict[str, Union[str, int, list]]]:
    """
    Extract metadata from a PDF book file.

    Args:
        pdf_path: Path to the PDF file
        save_to_db: Whether to save the metadata to the database
        output_path: Path to save the output file (optional)

    Returns:
        A dict of validated metadata or None on failure.
    """
    logger.info(f"Extracting metadata from {pdf_path}")
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    try:
        # Run the crew
        crew_instance = MetadataExtractionCrew().crew()
        result = crew_instance.kickoff(inputs={"pdf_path": pdf_path})

        # Parse raw output
        metadata = result
        if hasattr(result, "raw"):
            metadata = result.raw

        # Convert to dictionary if string
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except json.JSONDecodeError:
                metadata = {"raw_text": metadata}

        logger.info(f"Type of metadata: {type(metadata)}")
        logger.info(f"Parsed metadata: {json.dumps(metadata, indent=2)}")

        validated_model = MetadataOutput.model_validate(metadata)
        metadata_dict = validated_model.model_dump()

        # Save output to file
        if output_path is None:
            # Create outputs directory if it doesn't exist
            outputs_dir = Path(__file__).parent / "outputs"
            outputs_dir.mkdir(exist_ok=True)

            # Get PDF filename without extension and create output filename
            pdf_filename = Path(pdf_path).stem
            output_path = outputs_dir / f"{pdf_filename}.txt"

        # Ensure the output directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save metadata to file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(metadata_dict, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved metadata to {output_path}")

        # Insert into DB
        if save_to_db:
            with get_db_session() as session:
                book_id = insert_book_metadata(session, validated_model)
                metadata_dict["id"] = book_id

        return metadata_dict

    except Exception as e:
        traceback.print_exc()
        logger.error(f"Error in metadata extraction: {e}")
        return None
