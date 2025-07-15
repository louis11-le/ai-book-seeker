# Book Metadata Extraction

## 📚 Feature Goal

Extract and structure metadata from PDF book files and insert it into an existing MySQL database.

The system will:

1. Read the PDF file (including OCR fallback if needed).
2. Analyze the book structure (detect chapters, sections, or flat text).
3. Summarize key metadata fields.
4. Validate and clean the metadata before database insertion.

---

## Overview

The Book Metadata Extraction feature extracts and structures metadata from PDF book files, then inserts it into the MySQL database. This feature uses a crew of specialized agents powered by LLMs to analyze PDF content and extract relevant information.

---

## 🧩 Agent Setup Overview

The system is organized into 4 agents:

| #   | Agent Name                            | Purpose                                              |
| :-- | :------------------------------------ | :--------------------------------------------------- |
| 1   | **PDF Reader Agent**                  | Extract clean text from PDF                          |
| 2   | **Book Structure Analyzer Agent**     | Detect organization style (Chapters, Sections, Flat) |
| 3   | **Metadata Summarizer Agent**         | Extract core book metadata                           |
| 4   | **Metadata Quality Controller Agent** | Validate and normalize extracted metadata            |

✅ Agents work sequentially.
✅ Each agent has a clear, focused responsibility.

---

## Architecture

The system is organized into 4 sequential agents:

1. **PDF Reader Agent**: Extracts clean text from PDF files
2. **Book Structure Analyzer Agent**: Detects organization style (Chapters, Sections, Flat)
3. **Metadata Summarizer Agent**: Extracts core book metadata
4. **Metadata Quality Controller Agent**: Validates and normalizes extracted metadata

---

## 🛠 Technical Stack

| Technology          | Details                                               |
| :------------------ | :---------------------------------------------------- |
| Orchestration       | CrewAI                                                |
| LLM Provider        | OpenAI (GPT-4-turbo preferred)                        |
| PDF Text Extraction | PyPDF2 + Tesseract OCR                                |
| Database            | MySQL (feel free to update existing table and create) |

---

## Extracted Metadata

The feature extracts the following metadata fields:

| Field         | Type    | Description                                                                                                                                                                                           |
| :------------ | :------ | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `title`       | String  | Book title                                                                                                                                                                                            |
| `author`      | String  | Book author                                                                                                                                                                                           |
| `description` | String  | 2-4 line summary of the book                                                                                                                                                                          |
| `from_age`    | Integer | Minimum recommended age (null if not applicable)                                                                                                                                                      |
| `to_age`      | Integer | Maximum recommended age (null if not applicable)                                                                                                                                                      |
| `purpose`     | String  | Purpose of the book (e.g., "Entertainment", "Educational"). Only fill if explicitly mentioned in the book's content (e.g., introduction, preface, or marketing text); otherwise, leave blank or null. |
| `genre`       | String  | Book genre (e.g., "Fantasy", "Biography")                                                                                                                                                             |
| `tags`        | List    | List of keywords or themes                                                                                                                                                                            |

---

## Detailed Implementation Steps

### Step 1: Text Extraction (Reader Agent)

- Read first 10 pages of the PDF using PyPDF2.
- If text is missing or very short on a page, fallback to OCR (Tesseract).
- Combine all extracted text into one clean string.

✅ Output: Combined readable book text.

---

### Step 2: Book Structure Analysis (Structure Analyzer Agent)

- Analyze the extracted text.
- Determine if the book is organized with:
  - **Chapters**
  - **Sections**
  - **Flat text** (continuous text without divisions)

✅ Output: `"structure_type"` value ("Chapters", "Sections", or "Flat").

---

### Step 3: Metadata Summarization (Metadata Summarizer Agent)

- Summarize the extracted text and structure.
- Extract the following fields:

| Field         | Notes                                                        |
| :------------ | :----------------------------------------------------------- |
| `title`       | String, leave blank or "Unknown" if missing                  |
| `author`      | String, blank or "Unknown" if missing                        |
| `description` | 2–4 line short summary, blank if missing                     |
| `from_age`    | Integer if possible, else null                               |
| `to_age`      | Integer if possible, else null                               |
| `purpose`     | e.g., "Entertainment", "Educational", "Academic", else blank |
| `genre`       | e.g., "Fantasy", "Biography", else blank                     |
| `tags`        | List of keywords or themes, else blank                       |

✅ If metadata is missing ➔ leave blank, empty, null, or "Unknown".
✅ **No guessing or assuming** content if unclear.

✅ Output: Valid structured JSON.

---

### Step 4: Metadata Validation (Quality Controller Agent)

- Review the structured metadata.
- Validate:
  - Every expected field exists.
  - Missing values are safely marked (`""`, `"Unknown"`, or `null`).
  - No invalid types (e.g., integers must be integers).

✅ No guessing missing information.
✅ Only safe normalization and cleaning.

✅ Output: Clean validated JSON object ready for DB insertion.

---

## 🛡 Data Insertion into MySQL

- After validation, cast types properly (e.g., from_age ➔ integer).
- Insert the final clean metadata into the existing MySQL table.

✅ No broken records should be inserted.

---

## ⚙️ CrewAI Process Setup

- Use `Process.sequential` mode.
- Data flows like this:
  PDF ➔ Reader Agent ➔ Structure Analyzer Agent ➔ Metadata Summarizer Agent ➔ Quality Controller Agent ➔ MySQL Insert

✅ Output of each agent is input for the next.

---

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

---

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

---

## 🚀 Extra Notes

- API keys and database credentials must come from environment variables.
- Every agent must log its final output for debugging.
- Clear errors must be raised if PDF reading, OCR, summarization, or validation fails.

---

# 🎯 TL;DR

| Step | Task                             |
| :--- | :------------------------------- |
| 1    | Extract text from PDF            |
| 2    | Analyze book structure           |
| 3    | Summarize core metadata          |
| 4    | Validate metadata fields         |
| 5    | Insert clean metadata into MySQL |

✅ Fully business-driven.
✅ Scalable for production systems.

---
