# AI Book Seeker

An AI-powered book recommendation system that helps users find books based on their preferences and interests.

![AI Book Seeker Interface](/images/UI-1.png)

## 🎯 Problem & Solution

### Problem:

- Parents struggle to find age-appropriate books for children
- Hard to discover titles without knowing them in advance
- Difficult to match books to specific interests, reading levels, and budgets
- Manual metadata extraction from PDF books is time-consuming and error-prone

### Solution:

- Natural language interface understands conversational requests
- Automatically extracts key parameters (age, purpose, budget) from user input
- Provides personalized recommendations with tailored explanations
- Maintains context across conversation for follow-up questions
- AI-powered metadata extraction from PDF books with high accuracy

**Example Interaction:**

```
User: "I need books for my 6-year-old who is learning to read. My budget is around $50."

AI: "I found these books that match your criteria:

- 'Bob Books, Set 1: Beginning Readers' by Bobby Lynn Maslen: Simple phonics-based stories perfect for beginning readers age 4-6 with gradually increasing complexity to build confidence.

- 'The Reading House Set 1: Letter Recognition' by Marla Conn: Colorful workbooks designed specifically for 5-6 year olds beginning their reading journey with engaging illustrations.

- 'Elephant & Piggie: There Is a Bird on Your Head!' by Mo Willems: Award-winning easy reader with simple vocabulary, expressive characters and humorous storyline that beginning readers love.

- 'Frog and Toad Are Friends' by Arnold Lobel: Classic friendship stories with short chapters and charming illustrations, ideal for children transitioning to independent reading."
```

## 📱 UI Demo

Here's a visual overview of the AI Book Seeker interface:

### Conversation Flow
![Conversation Flow](/images/UI-2.png)

### Book Recommendations
![Book Recommendations](/images/UI-3.png)

### Refinement and Follow-up Questions
![Refinement and Follow-up Questions](/images/UI-4.png)

### Detailed Book Information
![Detailed Book Information](/images/UI-5.png)

## 🧱 Tech Stack

| Component | Technology                      |
| --------- | ------------------------------- |
| Frontend  | Next.js + TypeScript            |
| Backend   | FastAPI (Python)                |
| AI        | OpenAI GPT-4 with tool-calling  |
| Data      | MySQL + ChromaDB (vector store) |
| PDF metadata extraction | CrewAI + PyPDF2 + OpenAI model |

## 🚀 Installation & Setup

### Backend Setup

1. Create a virtual environment:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install the package in development mode:
   ```bash
   pip install -e ".[dev]"
   ```

3. Set up environment variables:
   Create a `.env` file in the backend directory with:
   ```
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_MODEL=gpt-4
   DATABASE_URL=mysql://user:password@localhost/books
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_DB=0
   REDIS_PASSWORD=
   VECTOR_DB_PATH=./chromadb_data
   ```

4. Run database migrations:
   ```bash
   cd backend
   alembic upgrade head
   ```

5. Start the API server:
   ```bash
   python -m ai_book_seeker.main
   ```

### Frontend Setup

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

## 🤖 Key AI Features

| Feature                        | Business Value                                                                  | Implementation                                                       |
| ------------------------------ | ------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| Natural Language Understanding | Processes user requests in everyday language without requiring specific formats | System prompt with guidance for parameter extraction                 |
| Query Flexibility              | Handles unexpected or novel request types beyond training examples              | Zero-shot capability in system prompts and general query handling    |
| Consistent Output Formatting   | Ensures recommendations follow standardized, user-friendly formats              | One-shot learning with example templates in explainer.py             |
| Intelligent Function Selection | Automatically selects appropriate search functions based on user needs          | Tool calling via OpenAI function API with custom tools               |
| Semantic Search                | Finds relevant books beyond exact keyword matching, improving results           | RAG (Retrieval Augmented Generation) with ChromaDB vector embeddings |
| Conversational Memory          | Remembers previous interactions for natural, ongoing conversations              | Context-aware memory system with Redis and automatic summarization   |
| PDF Metadata Extraction        | Automatically extracts structured metadata from PDF books with high accuracy    | AI agent crew with specialized roles for content analysis            |

## 🔄 System Flow

```mermaid
flowchart TD
    User(User) -->|Message| NextJS[Frontend\nNext.js + TypeScript]
    NextJS -->|HTTP Request| FastAPI[Backend\nFastAPI]

    subgraph Backend
        FastAPI -->|Process Request| ChatParser[Chat Parser]
        ChatParser -->|Extract Parameters| SystemPrompt[System Prompt]
        SystemPrompt -->|Guide Conversation| GPT4[OpenAI GPT-4]
        GPT4 -->|Tool Selection| ToolCalling[Tool Calling]

        ToolCalling -->|Search Request| BookSearch[Book Search]

        BookSearch -->|SQL Query| MySQL[(MySQL Database)]
        BookSearch -->|Vector Search| ChromaDB[(ChromaDB Vector Store)]

        BookSearch -->|Results| Explainer[Book Explainer]
        Explainer -->|Personalized Explanations| ResponseGen[Response Generation]

        ChatParser -->|Store Context| SessionMemory[Session Memory]
        SessionMemory -->|Retrieve Context| ChatParser
        SessionMemory <-->|Store/Retrieve| Redis[(Redis)]
    end

    ResponseGen -->|API Response| FastAPI
    FastAPI -->|HTTP Response| NextJS
    NextJS -->|Display Results| User
```

## 📚 Book Metadata Extraction Flow

```mermaid
flowchart TD
    PDF[PDF Book File] -->|Input| Reader[PDF Reader Agent]
    Reader -->|Extracted Text| Structure[Structure Analyzer Agent]
    Structure -->|Structure Type| Summarizer[Metadata Summarizer Agent]
    Summarizer -->|Raw Metadata| Validator[Quality Controller Agent]
    Validator -->|Validated Metadata| DB[(MySQL Database)]

    subgraph PDF Reader Agent
        Reader -->|Try PyPDF2| PyPDF2[PyPDF2]
        PyPDF2 -->|Success| Text[Clean Text]
        PyPDF2 -->|Failure| OCR[Tesseract OCR]
        OCR -->|Fallback| Text
    end

    subgraph Structure Analyzer Agent
        Structure -->|Analyze| Chapters[Chapters]
        Structure -->|Analyze| Sections[Sections]
        Structure -->|Analyze| Flat[Flat Text]
    end

    subgraph Metadata Summarizer Agent
        Summarizer -->|Extract| Title[Title]
        Summarizer -->|Extract| Author[Author]
        Summarizer -->|Extract| Description[Description]
        Summarizer -->|Extract| AgeRange[Age Range]
        Summarizer -->|Extract| Purpose[Purpose]
        Summarizer -->|Extract| Genre[Genre]
        Summarizer -->|Extract| Tags[Tags]
    end

    subgraph Quality Controller Agent
        Validator -->|Validate| Fields[Required Fields]
        Validator -->|Validate| Types[Data Types]
        Validator -->|Validate| Normalize[Normalize Values]
    end
```

## 📊 Data Structure

**MySQL Schema:** Books table with title, author, description, age_range, purpose, price, etc.

**Vector Embeddings:** Title + description + tags for semantic search

## 🔜 Roadmap

### ✅ MVP (Current)

- Natural language chat
- MySQL + ChromaDB search
- Tool calling
- Long chat memory
- Human-style explanations

### 💜 Phase 2

- External APIs (Amazon, Google Books)
- Voice input (Whisper)
- User accounts and history
- Advanced personalized suggestions with Chain-of-Thought
  - Multi-factor analysis (reading history, developmental needs)
  - Step-by-step reasoning for recommendations

## 📁 Project Structure

The project follows a modern Python package structure with clear separation of concerns:

```
.
├── backend/               # Backend Python code
│   ├── src/              # Source code
│   │   └── ai_book_seeker/  # Main package
│   │       ├── api/         # API endpoints and routes
│   │       │   ├── __init__.py
│   │       │   └── routes.py
│   │       ├── core/        # Core functionality
│   │       │   ├── __init__.py
│   │       │   ├── config.py
│   │       │   └── logging.py
│   │       ├── db/          # Database models and connections
│   │       │   ├── __init__.py
│   │       │   ├── connection.py
│   │       │   ├── database.py
│   │       │   └── models.py
│   │       ├── metadata_extraction/ # Book metadata extraction
│   │       ├── prompts/     # Prompt templates
│   │       ├── services/    # Business logic
│   │       │   ├── __init__.py
│   │       │   ├── chat_parser.py
│   │       │   ├── explainer.py
│   │       │   ├── memory.py
│   │       │   ├── query.py
│   │       │   ├── tools.py
│   │       │   └── vectordb.py
│   │       ├── utils/       # Utility functions
│   │       ├── __init__.py  # Package initialization
│   │       └── main.py      # Application entry point
│   ├── docs/             # Documentation
│   │   ├── features/      # Feature specifications
│   │   └── book_metadata_extraction.md  # Technical documentation
│   ├── tests/            # Test suite
│   │   ├── integration/  # Integration tests
│   │   └── unit/         # Unit tests
│   ├── setup.py          # Package installation
│   ├── pyproject.toml    # Project configuration
│   ├── requirements.txt  # Production dependencies
│   └── requirements-dev.txt  # Development dependencies
├── frontend/            # Frontend Next.js code
│   ├── src/            # Source code
│   ├── public/         # Static assets
│   └── package.json    # Dependencies
└── README.md           # Project overview
```


## 📋 Additional Info

- **Session Persistence:** Temporary in Redis (2-hour TTL)
- **Prompt Versioning:** Environment-variable controlled
- **License:** MIT
- **Language:** English only (currently)

## 👥 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to your branch (`git push origin feature/your-feature`)
5. Open a Pull Request

Please ensure your code follows the existing style and passes all tests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
