"""
Book Metadata Extraction

This module serves as the entry point for the book metadata extraction feature.
It provides functions to extract metadata from PDF book files using a crew of
specialized AI agents.

All configuration (output directory, file naming, feature flags) is accessed via the centralized AppSettings config object.
Do not use direct environment variable access or hardcoded values; use only AppSettings.
"""

import json
import os
import traceback
from pathlib import Path
from typing import Dict, Optional, Union

from ai_book_seeker.core.config import AppSettings
from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.db.database import get_db_session
from ai_book_seeker.metadata_extraction.crew import create_metadata_extraction_crew
from ai_book_seeker.metadata_extraction.schema import MetadataOutput
from ai_book_seeker.metadata_extraction.tools.validation_tools import insert_book_metadata

# Set up logging
logger = get_logger(__name__)


def extract_book_metadata(
    pdf_path: str, settings: AppSettings, save_to_db: bool = True, output_path: Optional[str] = None
) -> Optional[Dict[str, Union[str, int, list]]]:
    """
    Extract metadata from a PDF book file.

    Args:
        pdf_path: Path to the PDF file
        settings: Application settings containing configuration
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
        # Run the crew using factory function
        crew_instance = create_metadata_extraction_crew(settings).crew()
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
        output_path_obj: Path
        if output_path is None:
            # Use output directory from config
            output_dir = Path(settings.metadata_extraction.output_dir)
            output_dir.mkdir(exist_ok=True)
            pdf_filename = Path(pdf_path).stem
            # Simple file naming pattern
            output_filename = f"{pdf_filename}_metadata.json"
            output_path_obj = output_dir / output_filename
        else:
            output_path_obj = Path(output_path)
            output_dir = output_path_obj.parent
            output_dir.mkdir(parents=True, exist_ok=True)

        # Save metadata to file
        with open(str(output_path_obj), "w", encoding="utf-8") as f:
            json.dump(metadata_dict, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved metadata to {output_path_obj}")

        # Insert into DB
        if save_to_db:
            with get_db_session(settings) as session:
                book_id = insert_book_metadata(session, validated_model)
                metadata_dict["id"] = book_id

        return metadata_dict

    except Exception as e:
        traceback.print_exc()
        logger.error(f"Error in metadata extraction: {e}", exc_info=True)
        return None
