# Book Metadata Extraction

## Overview

The Book Metadata Extraction feature extracts and structures metadata from PDF book files, then inserts it into the MySQL database. This feature uses a crew of specialized agents powered by LLMs to analyze PDF content and extract relevant information.

## Architecture

The system is organized into 4 sequential agents:

1. **PDF Reader Agent**: Extracts clean text from PDF files
2. **Book Structure Analyzer Agent**: Detects organization style (Chapters, Sections, Flat)
3. **Metadata Summarizer Agent**: Extracts core book metadata
4. **Metadata Quality Controller Agent**: Validates and normalizes extracted metadata

## Extracted Metadata

The feature extracts the following metadata fields:

| Field | Type | Description |
|:------|:-----|:------------|
| `title` | String | Book title |
| `author` | String | Book author |
| `description` | String | 2-4 line summary of the book |
| `from_age` | Integer | Minimum recommended age (null if not applicable) |
| `to_age` | Integer | Maximum recommended age (null if not applicable) |
| `purpose` | String | Purpose of the book (e.g., "Entertainment", "Educational") |
| `genre` | String | Book genre (e.g., "Fantasy", "Biography") |
| `tags` | List | List of keywords or themes |

## Usage

### API Endpoint

```
POST /api/metadata/extract
```

**Request**:
- Form data with a file field named "file" containing the PDF

**Response**:
- 201 Created with the extracted metadata JSON

**Example**:

```bash
curl -X POST "http://localhost:8000/api/metadata/extract" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/to/your/book.pdf"
```

### CLI Tool

You can also use the provided command-line tool:

```bash
python backend/scripts/extract_book_metadata.py path/to/your/book.pdf [--no-db] [--output output.json]
```

**Options**:
- `--no-db`: Don't save the metadata to the database
- `--output`: Path to save the extracted metadata as JSON

## Development and Customization

### Required Dependencies

- PyPDF2
- Tesseract OCR
- CrewAI
- pdf2image
- FastAPI

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key for LLM access
- `MYSQL_CONNECTION_STRING`: Database connection string

### Extending the Feature

To modify the extracted metadata fields:

1. Update the `Book` model in `backend/db/models.py`
2. Update the metadata extraction context in `backend/metadata_extraction/tasks.py`
3. Update the validation logic in `backend/metadata_extraction/db_utils.py`
