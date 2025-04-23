# AI Book Seeker Backend

FastAPI backend for the AI Book Seeker, integrating NLP and vector search for intelligent book recommendations.

## 🧱 Tech Stack

- **FastAPI**: Web framework
- **SQLAlchemy**: Database ORM
- **OpenAI**: GPT-4 integration, embeddings
- **ChromaDB**: Vector database for semantic search
- **Redis**: Session management

## 🔑 Key Components

### 🔍 Vector Search (`vectordb.py`)
- Generates embeddings from text using OpenAI
- Enables semantic search beyond exact keyword matching
- Integrates with SQL for hybrid search capabilities

### 📚 Book Search (`query.py`)
- Combines SQL filtering with vector search
- Handles search by age, purpose, genre, budget
- Falls back to semantic search when criteria are vague

### 💬 Conversation (`chat_parser.py`)
- Processes natural language with GPT-4
- Uses few-shot learning for intent detection
- Implements function calling for tool integration
- Maintains conversation context via Redis

### 🧠 Explanations (`explainer.py`)
- Generates personalized recommendation justifications
- Uses structured format to map explanations to books
- Creates human-like reasoning for each recommendation

## 🛠️ Quick Setup

```bash
# Create environment
conda create -n ai-book-seeker python=3.12
conda activate ai-book-seeker
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🗄️ Database Setup

```bash
# Initialize MySQL database
mysql -u root -p
CREATE DATABASE ai_book_seeker;
CREATE USER 'ai_book_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON ai_book_seeker.* TO 'ai_book_user'@'localhost';
FLUSH PRIVILEGES;

# Run database migrations (from backend directory)
python -m scripts.db_init
```

## 🔐 Environment Variables

Key variables in `.env` file:

```
# OpenAI credentials
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-3.5-turbo  # or gpt-4 for better results

# Database settings
MYSQL_USER=ai_book_user
MYSQL_PASSWORD=your_password
MYSQL_HOST=localhost
MYSQL_DATABASE=ai_book_seeker

# Redis settings (for session management)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_EXPIRE_SECONDS=7200  # 2 hours
```

## 🌐 API Endpoints

- `GET /`: Health check
- `POST /api/chat`: Chat endpoint
- `DELETE /api/session/{session_id}`: Delete session

## 📁 Directory Structure

```
backend/
├── main.py          # Application entry
├── chat_parser.py   # Query processing
├── query.py         # Database searches
├── tools.py         # Function definitions
├── vectordb.py      # Vector embeddings
├── explainer.py     # Book explanations
├── memory.py        # Session management
├── db/              # Database components
└── tests/           # Unit & integration tests
```

## 🧪 Code Quality

Run these from the backend directory:
- Format: `black .`
- Sort imports: `isort .`
- Lint: `flake8 .` and `pylint *.py`
- Type check: `mypy .`
