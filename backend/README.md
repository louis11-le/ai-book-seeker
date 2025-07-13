# AI Book Seeker Backend

An AI-powered book recommendation system that suggests books based on user preferences.

## Project Structure

```
backend/
├── src/
│   └── ai_book_seeker/
│       ├── api/
│       │   ├── routes/                # Feature-based route files (chat, session, voice_assistant)
│       │   ├── schemas/               # Pydantic schemas for API
│       ├── core/                      # Core config and logging
│       ├── db/                        # Database models, connection, migrations
│       ├── features/                  # Modular features (get_book_recommendation, search_faq, purchase_book)
│       ├── metadata_extraction/       # Book metadata extraction pipeline
│       ├── prompts/                   # Prompt templates (including voice_assistant/elevenlabs)
│       ├── services/                  # Orchestrator, tools, memory, explainer, etc.
│       ├── utils/                     # Utility functions
│       └── main.py                    # Application entry point
├── docs/                              # Documentation (feature specs, technical docs)
├── tests/                             # Unit and integration tests
├── pyproject.toml                     # Project configuration
└── README.md                          # Backend overview
```

## Installation

1. Clone the repository
2. Install dependencies and create a virtual environment automatically:

```bash
cd backend
uv lock
uv sync --dev
```

3. Set up your `.env` file (example):

```
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o
DATABASE_URL=mysql://user:password@localhost/books
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
VECTOR_DB_PATH=./chromadb_data
ELEVENLABS_API_KEY=your_elevenlabs_api_key
X_API_KEY=your_backend_webhook_secret
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langchain_api_key
LANGCHAIN_PROJECT=ai-book-seeker
```

## Running the API

```bash
uv run uvicorn ai_book_seeker.main:app --reload --host 0.0.0.0 --port 8000
```

## Running Tests

```bash
uv run pytest tests/ -v
```

## Development

- Format code with Black: `uv run black .`
- Sort imports with isort: `uv run isort .`
- Run linter: `uv run flake8 .`
- Run type checking: `uv run mypy src/`

## Security & Logging

- The `/voice` endpoint and other webhooks require an `x_api_key` header for secure server-to-server calls (never exposed to frontend).
- All API requests and responses are logged using structured logging for traceability and debugging.
- Environment variables and secrets should never be committed to version control.

## Modularity & Feature Addition

- The backend is organized by feature (see `features/`), making it easy to add new tools or endpoints.
- To add a new feature/tool:
  1. Create a new folder in `features/` with `handler.py`, `schema.py`, and `tool.py`.
  2. Register the tool in `services/tools.py`.
  3. Add routes and schemas as needed in `api/routes/` and `api/schemas/`.
  4. Add tests in `tests/unit/features/` or `tests/integration/`.

## LangSmith Integration

This project supports [LangSmith](https://docs.smith.langchain.com/) for tracing and debugging LangChain workflows.

### Setup

1. Install dependencies (already included):
   ```sh
   uv add langsmith
   ```
2. Obtain a LangSmith API key from your LangSmith account.
3. Add the following environment variables to your `.env` file or deployment environment:
   ```env
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_API_KEY=your-langsmith-api-key
   # Optional: organize traces by project
   LANGCHAIN_PROJECT=ai-book-seeker
   ```
4. Environment variables are loaded automatically via `dotenv` in `core/config.py`.

### Usage

- Tracing is enabled automatically for all LangChain workflows when the above variables are set.
- Visit your [LangSmith dashboard](https://smith.langchain.com/) to view traces and debug LLM chains, agents, and tool calls.

### Privacy & Best Practices

- Only enable tracing in development or staging unless you have reviewed data privacy requirements for production.
- For more details, see the [LangSmith documentation](https://docs.smith.langchain.com/).
