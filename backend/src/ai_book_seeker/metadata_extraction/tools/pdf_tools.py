"""
PDF processing tools for the metadata extraction module.
"""

from typing import List, Optional, Tuple

import PyPDF2
import pytesseract
from crewai.tools import BaseTool
from pdf2image import convert_from_path

from ai_book_seeker.core.logging import get_logger

# Initialize logger
logger = get_logger(__name__)


def extract_text_with_pypdf(pdf_path: str, max_pages: int = 10) -> List[str]:
    """
    Extract text from a PDF file using PyPDF2.

    Args:
        pdf_path: Path to the PDF file
        max_pages: Maximum number of pages to extract

    Returns:
        List of strings containing extracted text from each page
    """
    logger.info(f"Extracting text from {pdf_path} using PyPDF2")
    text_by_page = []

    try:
        with open(pdf_path, "rb") as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            num_pages = min(len(pdf_reader.pages), max_pages)

            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                text_by_page.append(text if text else "")

        return text_by_page
    except Exception as e:
        logger.error(f"Error extracting text with PyPDF2: {str(e)}", exc_info=True)
        return [""] * min(max_pages, 10)  # Return empty strings on error


def extract_text_with_ocr(pdf_path: str, max_pages: int = 10) -> List[str]:
    """
    Extract text from a PDF file using OCR.

    Args:
        pdf_path: Path to the PDF file
        max_pages: Maximum number of pages to extract

    Returns:
        List of strings containing OCR'd text from each page
    """
    logger.info(f"Extracting text from {pdf_path} using OCR")
    text_by_page = []

    try:
        # Convert PDF to images
        pages = convert_from_path(pdf_path, first_page=1, last_page=max_pages)

        # Process each page image with OCR
        for i, page in enumerate(pages):
            if i >= max_pages:
                break

            # Extract text using OCR
            text = pytesseract.image_to_string(page)
            text_by_page.append(text if text else "")

        return text_by_page
    except Exception as e:
        logger.error(f"Error extracting text with OCR: {str(e)}", exc_info=True)
        return [""] * min(max_pages, 10)  # Return empty strings on error


def extract_text_from_pdf(pdf_path: str, page_range: Optional[Tuple[int, int]] = None) -> str:
    """
    Extract text from a PDF file, trying PyPDF2 first and falling back to OCR if needed.

    Args:
        pdf_path: Path to the PDF file
        page_range: Optional tuple of (start_page, end_page)

    Returns:
        Combined string of extracted text
    """
    logger.info(f"Extracting text from {pdf_path} using PyPDF2 and OCR")

    # Calculate max_pages from page_range
    max_pages = 10  # Default
    if page_range:
        max_pages = page_range[1] - page_range[0]

    # Extract text using PyPDF2
    pypdf_text_by_page = extract_text_with_pypdf(pdf_path, max_pages)

    # For each page, if PyPDF2 extraction yielded little or no text, try OCR
    combined_text_by_page = []
    ocr_text_by_page = None

    for i, page_text in enumerate(pypdf_text_by_page):
        # Check if page has sufficient text
        if len(page_text.strip()) < 100:  # Arbitrary threshold
            if ocr_text_by_page is None:
                # Only do OCR once, if needed
                ocr_text_by_page = extract_text_with_ocr(pdf_path, max_pages)

            # Use OCR text if it extracted more than PyPDF2
            if i < len(ocr_text_by_page) and len(ocr_text_by_page[i].strip()) > len(page_text.strip()):
                combined_text_by_page.append(ocr_text_by_page[i])
                continue

        combined_text_by_page.append(page_text)

    # Join all pages with page breaks
    combined_text = "\n\n----- PAGE BREAK -----\n\n".join(combined_text_by_page)

    logger.info(f"Extracted {len(combined_text_by_page)} pages with {len(combined_text)} characters")
    return combined_text


class PDFExtractionTool(BaseTool):
    """Tool for extracting text from PDF files."""

    name: str = "extract_text_from_pdf"
    description: str = "Extract text from a PDF file, trying PyPDF2 first and falling back to OCR if needed."

    def _run(self, pdf_path: str, page_range: Optional[Tuple[int, int]] = None) -> str:
        """
        Run the PDF extraction tool.

        Args:
            pdf_path: Path to the PDF file
            page_range: Optional tuple of (start_page, end_page)

        Returns:
            The extracted text
        """
        return extract_text_from_pdf(pdf_path, page_range)
