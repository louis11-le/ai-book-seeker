# AI Book Seeker

## Problem & Solution

### Problem:

- Parents and educators struggle to find age-appropriate, interest-matched books for children and students.
- Discovering new titles is difficult without prior knowledge or recommendations.
- Matching books to specific interests, reading levels, and budgets is time-consuming.
- Manual metadata extraction from PDF books is error-prone and labor-intensive.
- Users want to interact naturally, including by voice, and get instant, explainable answers to book-related questions.

### Solution:

- Natural language **chat and voice assistant** (via ElevenLabs) for intuitive, multi-modal book discovery.
- Instantly answers common questions using a vector-based FAQ index (backend for chat, ElevenLabs for voice).
- AI-powered, context-aware book recommendations with clear, human-style explanations.
- Automated, accurate extraction of book details from PDF files using an AI agent crew.
- Modular, feature-based backend for rapid development and real-world integrations (OpenAI, ElevenLabs, ChromaDB, etc.).

**Example Interaction:**

```
User: "I need books for my 6-year-old who is learning to read. My budget is around $50."

AI: "I found these books that match your criteria:
- 'Bob Books, Set 1: Beginning Readers' by Bobby Lynn Maslen: Simple phonics-based stories perfect for beginning readers age 4-6 with gradually increasing complexity to build confidence.
- 'The Reading House Set 1: Letter Recognition' by Marla Conn: Colorful workbooks designed specifically for 5-6 year olds beginning their reading journey with engaging illustrations.
- 'Elephant & Piggie: There Is a Bird on Your Head!' by Mo Willems: Award-winning easy reader with simple vocabulary, expressive characters and humorous storyline that beginning readers love.
- 'Frog and Toad Are Friends' by Arnold Lobel: Classic friendship stories with short chapters and charming illustrations, ideal for children transitioning to independent reading."
```

---

## Project Overview

AI Book Seeker is a next-generation, AI-powered platform for book discovery. Designed for parents, educators, and curious readers, it combines chat and voice interfaces, advanced semantic search, and explainable recommendations. The system is built with a modular, production-ready architecture for rapid feature development and real-world integrations.

---

## UI Demo

Here's a visual overview of the AI Book Seeker interface:

### Conversation Flow (Chat & Voice)

- Interact via chat or voice (powered by ElevenLabs) for seamless book discovery and FAQ support.

![Conversation Flow](/images/UI-1.png)

### Book Recommendations

- Personalized, explainable book suggestions based on user preferences and context.

![Book Recommendations](/images/UI-2.png)

<!-- Inline Demo Video -->
<video controls width="600">
  <source src="images/conversational-ai.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>

## ▶️ Watch the Demo Video

[▶️ Watch the demo video](images/conversational-ai.mp4)

---

## Tech Stack

| Component               | Technology                                   |
| ----------------------- | -------------------------------------------- |
| Frontend                | Next.js + TypeScript                         |
| Backend                 | FastAPI (Python)                             |
| AI Orchestration        | LangChain (tool orchestration)               |
| LLM                     | OpenAI GPT-4o (tool-calling, embeddings)     |
| Voice Assistant         | ElevenLabs (voice input/output)              |
| Data                    | MySQL (structured) + ChromaDB (vector store) |
| PDF Metadata Extraction | CrewAI + PyPDF2 + OpenAI model               |
| Schemas                 | Pydantic (strict validation)                 |
| Security                | x_api_key (webhook), .env secrets            |
| Testing                 | Pytest (backend)                             |

---

## Installation & Setup

### Backend Setup

1. Install dependencies and create a virtual environment automatically:
   ```bash
   cd backend
   uv lock
   uv sync --dev
   ```
2. Set up environment variables:
   Create a `.env` file in the backend directory with:
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
   LANGCHAIN_TRACING_V2=true  # Enable LangChain advanced tracing (set to true or false)
   LANGCHAIN_API_KEY=your_langchain_api_key  # For LangChain cloud tracing (if used)
   LANGCHAIN_PROJECT=your_langchain_project  # Project name for LangChain tracing
   ```
3. Run database migrations:
   ```bash
   cd backend
   uv run alembic upgrade head
   ```
4. Start the API server:
   ```bash
   uv run uvicorn ai_book_seeker.main:app --reload --host 0.0.0.0 --port 8000
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

---

## Key AI Features

| Feature                        | Business Value                                                                           | Implementation                                                       |
| ------------------------------ | ---------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| Natural Language Understanding | Processes user requests in everyday language without requiring specific formats          | System prompt with guidance for parameter extraction                 |
| Query Flexibility              | Handles unexpected or novel request types beyond training examples                       | Zero-shot capability in system prompts and general query handling    |
| Consistent Output Formatting   | Ensures recommendations follow standardized, user-friendly formats                       | One-shot learning with example templates in explainer.py             |
| Intelligent Function Selection | Automatically selects appropriate search functions based on user needs                   | Tool calling via OpenAI function API with custom tools               |
| Semantic Search                | Finds relevant books beyond exact keyword matching, improving results                    | RAG (Retrieval Augmented Generation) with ChromaDB vector embeddings |
| Conversational Memory          | Remembers previous interactions for natural, ongoing conversations                       | Context-aware memory system with Redis and automatic summarization   |
| PDF Metadata Extraction        | Automatically extracts structured metadata from PDF books with high accuracy             | AI agent crew with specialized roles for content analysis            |
| Voice Assistant                | Voice input/output for book recommendations and FAQ                                      | ElevenLabs integration, backend webhook, system prompt engineering   |
| Voice AI                       | Natural language voice interaction for book search and FAQ                               | ElevenLabs, backend webhook, prompt engineering                      |
| FAQ Vector Search              | Answers common questions using vector-based FAQ index (chat: backend, voice: ElevenLabs) | System prompt, vector DB, and ElevenLabs knowledge base              |
| Explainable Recommendations    | Provides clear, human-style explanations for all suggestions                             | Explainer module, prompt engineering, and output schema enforcement  |
| Modular, Extensible Backend    | Rapid feature development and integration with new tools/APIs                            | Feature-based folder structure, Pydantic, LangChain, FastAPI         |
| Security & Observability       | Secure, predictable, and debuggable flows for all major features                         | x_api_key, structured logging, strict schema validation              |

---

## System Flow

The following diagram illustrates the flow for both chat and voice interactions, including FAQ and book recommendation logic:

```mermaid
flowchart TD
    %% Frontend group: User, UI, Chat Input, and ElevenLabs Widget
    subgraph Frontend["Frontend"]
        User["User"]
        UI["Frontend UI (Next.js)"]
        ChatInput["Chat Input"]
        ElevenLabs["ElevenLabs Widget"]
        User --> UI
        UI -->|Type message| ChatInput
        UI --> ElevenLabs
    end

    %% Backend group: POST /chat and all backend logic (left of ElevenLabs)
    subgraph BackendSection["Backend"]
        ChatAPI["POST /chat"]
        Orchestrator["LangChain Orchestrator"]
        LangChain["Agent/Tool Selection"]
        FAQTool["FAQ Tool"]
        BookRecTool["Book Rec Tool"]
        Memory["Session Memory (Redis/In-Memory)"]
        Logging["Structured Logging/Error Handling"]
        ChatAPI --> Orchestrator
        Orchestrator --> LangChain
        LangChain --> FAQTool
        LangChain --> BookRecTool
        LangChain --> Memory
        Orchestrator --> Logging
        Orchestrator --> UI
    end

    %% Voice (ElevenLabs) group: Widget, POST /voice, Knowledge Base (right)
    subgraph ElevenLabsSection["Voice (ElevenLabs)"]
        ElevenLabs["ElevenLabs Widget"]
        VoiceAPI["POST /voice"]
        EL_KB["Knowledge Base"]
        ElevenLabs --> EL_KB
        ElevenLabs -->|Speech| User
        ElevenLabs --> VoiceAPI
        VoiceAPI --> Orchestrator
    end

    %% Data Sources (bottom)
    subgraph DataSources["Data Sources"]
        FAQTool --> ChromaDB["ChromaDB"]
        BookRecTool --> MySQL["MySQL"]
    end

    %% Cross-group arrows
    ChatInput --> ChatAPI

    %% Styling for Backend
    classDef backend fill:#ffe599,stroke:#333,stroke-width:2px;
    class BackendSection,Orchestrator,LangChain,FAQTool,BookRecTool,Memory,Logging,ChatAPI backend;
    classDef data fill:#bbf,stroke:#333,stroke-width:1px;
    class ChromaDB,MySQL data;
```

Note: All arrows represent main data/request flow.

---

## Book Metadata Extraction Flow

The following diagram shows the automated pipeline for extracting structured metadata from PDF books:

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

---

## 📁 Modern Project Structure

```
.
├── backend/               # Backend Python code
│   ├── src/
│   │   └── ai_book_seeker/
│   │       ├── api/         # API endpoints and routes
│   │       │   ├── routes/  # Feature-based route files (chat, session, voice_assistant)
│   │       │   └── schemas/ # Pydantic schemas for API
│   │       ├── core/        # Core config and logging
│   │       ├── db/          # Database models, connection, migrations
│   │       ├── features/    # Modular features (get_book_recommendation, search_faq, purchase_book)
│   │       ├── metadata_extraction/ # Book metadata extraction pipeline
│   │       ├── prompts/     # Prompt templates (including voice_assistant/elevenlabs)
│   │       ├── services/    # Orchestrator, tools, memory, explainer, etc.
│   │       ├── utils/       # Utility functions
│   │       └── main.py      # Application entry point
│   ├── docs/                # Documentation (feature specs, technical docs)
│   ├── tests/               # Unit and integration tests
│   ├── pyproject.toml       # Project configuration
│   └── README.md            # Project overview
├── frontend/                # Next.js frontend
│   ├── app/                 # Main app pages and layout
│   ├── components/          # UI components (Chat, Voice, etc.)
│   ├── types.ts             # Shared types
│   └── README.md            # Frontend overview
├── images/                  # UI and architecture diagrams
└── README.md                # Main project overview
```

---

## 📚 API Endpoints

- **POST `/chat`** — Conversational chat interface (FAQ + book recommendations)
- **POST `/voice`** — Voice webhook for book recommendations (x_api_key required)
- **POST `/api/metadata_extraction`** — PDF metadata extraction

**Security:**

- `/voice` endpoint requires `x_api_key` header for secure server-to-server calls (never exposed to frontend).

**Schemas:**

- All endpoints use strict Pydantic schemas for request/response validation.

---

## 🧪 Testing & Quality

- **Test Suite:** Comprehensive unit and integration tests for backend features, orchestrator, and API endpoints.
- **How to Run:**
  - Backend: `uv run pytest tests/ -v`
- **Coverage:** Tests for chat, book recommendation, FAQ, and metadata extraction. Voice endpoint tests in progress.

---

## 🗺️ Roadmap

### ✅ Live

- Natural language chat (text)
- FAQ search (vector-based)
- Book recommendations (explainable, personalized)
- PDF metadata extraction
- Voice assistant (ElevenLabs integration, `/voice` endpoint)
- Modular, feature-based backend

### 🔜 Next

- More external APIs (Amazon, Google Books)
- User accounts and history
- Advanced personalized suggestions (Chain-of-Thought, multi-factor analysis)
- Full test coverage for voice endpoint

---

## 👥 Contributing

Contributions are welcome! Please fork the repo, create a feature branch, and open a pull request. Ensure your code follows the existing style and passes all tests.

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
