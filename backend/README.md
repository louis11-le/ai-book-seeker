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
│       ├── prompts/                   # General prompt templates (explainer, searcher, system, voice_assistant/elevenlabs)
│       ├── services/                  # Orchestrator, tools, memory, explainer, etc.
│       ├── utils/                     # Utility functions
│       ├── workflows/                 # LangGraph workflow orchestration
│       │   ├── agents/                # Agent implementations (general, sales, voice)
│       │   ├── nodes/                 # Workflow nodes (router, coordinator, tools)
│       │   ├── prompts/               # Workflow-specific prompt templates
│       │   │   └── agents/            # Agent prompt templates (BaseAnalysisPromptTemplate)
│       │   ├── schemas/               # Workflow state and data models
│       │   ├── utils/                 # Workflow utilities (node_utils, message_factory, error_handling)
│       │   └── orchestrator.py        # Main workflow orchestration
│       └── main.py                    # Application entry point
├── docs/                              # Documentation (feature specs, technical docs)
├── tests/                             # Unit and integration tests
├── pyproject.toml                     # Project configuration
└── README.md                          # Backend overview
```

## Redis Usage: Workflow Memory vs. App Data

- **Workflow memory and checkpointing for LangGraph workflows** is handled exclusively by the official [`langgraph-redis`](https://github.com/redis-developer/langgraph-redis) package. This ensures compatibility, maintainability, and best practices as required by project architecture and context7 standards.
- **All other Redis usage** (sessions, cache, user/app data, etc.) should use the canonical client in `src/ai_book_seeker/services/redis_client.py`.
- Do **not** use or implement custom RedisSaver/checkpointer logic for workflow memory—always use the official package for LangGraph workflows.

For more details, see the docstrings in `orchestrator.py` and `services/redis_client.py`.

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
CHROMADB_BOOK_PERSIST_DIRECTORY=./chromadb_books
CHROMADB_BOOK_COLLECTION_NAME=books_collection
CHROMADB_FAQ_PERSIST_DIRECTORY=./chromadb_faq
CHROMADB_FAQ_COLLECTION_NAME=faq_collection
ELEVENLABS_API_KEY=your_elevenlabs_api_key
X_API_KEY=your_backend_webhook_secret
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

## Logging

- All API requests and responses are logged using structured logging for traceability and debugging.
- Environment variables and secrets should never be committed to version control.

## Modularity & Feature Addition

- The backend is organized by feature (see `features/`), making it easy to add new tools or endpoints.
- To add a new feature/tool:
  1. Create a new folder in `features/` with `handler.py`, `schema.py`, and `tool.py`.
  2. Register the tool in `services/tools.py`.
  3. Add routes and schemas as needed in `api/routes/` and `api/schemas/`.
  4. Add tests in `tests/unit/features/` or `tests/integration/`.
  5. Update workflow nodes and edges in `workflows/` if needed for LangGraph integration.

## Workflow Architecture & Optimizations

The system uses a **LangGraph-based multi-agent workflow** with the following key features:

### **Pure Conditional Edge System**
- **Static edges** only for deterministic routing (entry/exit points, result collection)
- **Conditional edges** for all dynamic routing decisions (agent selection, tool routing)
- **No edge conflicts** - clean separation of concerns
- **Explicit error handling** through conditional routing

### **Multi-Agent Parallel Execution**
- **Router Node**: Analyzes queries and determines routing strategy
- **Parameter Extraction**: Extracts structured parameters using LLM
- **Agent Coordinator**: Manages multi-agent parallel execution
- **Specialized Agents**: General and Voice agents with specific tool access
- **Tool Execution**: Parallel tool execution with proper state merging

### **State Management**
- **Concurrent Updates**: Support for multi-tool parallel execution
- **State Merging**: Intelligent merging of agent results and shared data
- **Memory Management**: Redis-based session memory with automatic cleanup
- **Performance Optimization**: Caching and memory optimization layers

### **Code Optimizations**
- **Centralized error handling** via `_safe_routing_targets()` helper function
- **Standardized edge registration** via `_create_conditional_edge_with_error_fallback()` helper
- **Dynamic agent-tool mapping** for flexible edge generation
- **Consistent patterns** across all conditional edge registrations
- **Streamlined utilities** via `node_utils.py` for state validation and Command creation
- **Modular message factory** for standardized message creation patterns

### **Agent Architecture & Prompt Templates**
- **Template Method Pattern**: All agents extend `BaseAgent` with abstract methods
- **Modular Prompt System**: `BaseAnalysisPromptTemplate` (workflows/prompts/agents/) provides composable guidance
- **Domain-Specific Guidance**: FAQ, sales, voice, and book recommendation guidance
- **Validation Integration**: Built-in confidence range enforcement
- **Composable Design**: Agents combine multiple guidance sources for specialized behavior

### **Key Benefits**
- **Improved maintainability** through centralized error handling and prompt templates
- **Better debugging** with context-aware error messages
- **Consistent patterns** for all workflow components
- **Professional-grade documentation** and type safety throughout
- **Parallel Execution**: Multi-agent and multi-tool parallelism
- **Streaming Responses**: Real-time workflow state updates
- **Error Recovery**: Graceful error handling and fallback mechanisms
