# AI Book Seeker Backend

An AI-powered book recommendation system that suggests books based on user preferences.

## Project Structure

```
backend/
├── src/                       # Source code
│   └── ai_book_seeker/        # Main package
│       ├── api/               # API endpoints and routes
│       │   ├── __init__.py
│       │   └── routes.py      # FastAPI route definitions
│       ├── core/              # Core functionality
│       │   ├── __init__.py
│       │   ├── config.py      # Configuration management
│       │   └── logging.py     # Logging setup
│       ├── db/                # Database models and connections
│       │   ├── __init__.py
│       │   ├── connection.py  # Database connection setup
│       │   ├── database.py    # Database session management
│       │   └── models.py      # SQLAlchemy models
│       ├── metadata_extraction/ # Book metadata extraction
│       ├── prompts/           # Prompt templates
│       ├── services/          # Business logic
│       │   ├── __init__.py
│       │   ├── chat_parser.py # Chat request processing
│       │   ├── explainer.py   # Book recommendation explanations
│       │   ├── memory.py      # Session memory management
│       │   ├── query.py       # Book search functionality
│       │   ├── tools.py       # Tool definitions
│       │   └── vectordb.py    # Vector database operations
│       ├── utils/             # Utility functions
│       ├── __init__.py        # Package initialization
│       └── main.py            # Application entry point
├── docs/                      # Documentation
│   ├── features/             # Feature specifications
│   └── book_metadata_extraction.md  # Technical documentation
├── tests/                     # Test suite
│   ├── integration/           # Integration tests
│   └── unit/                  # Unit tests
├── setup.py                   # Package installation
├── pyproject.toml             # Project configuration
├── requirements.txt           # Production dependencies
└── requirements-dev.txt       # Development dependencies
```

## Installation

1. Clone the repository
2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
# For development
pip install -e ".[dev]"

# For production
pip install -e .
```

4. Set up your `.env` file:
```
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4
DATABASE_URL=mysql://user:password@localhost/books
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
VECTOR_DB_PATH=./chromadb_data
```

## Running the API

```bash
# From the backend directory
python -m ai_book_seeker.main
```

## Development

- Format code with Black: `black .`
- Sort imports with isort: `isort .`
- Run linter: `flake8 .`
- Run type checking: `mypy src/`
