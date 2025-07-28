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
- Modular, feature-based backend with LangGraph multi-agent workflow orchestration for rapid development and real-world integrations.

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

AI Book Seeker is a next-generation, AI-powered platform for book discovery. Designed for parents, educators, and curious readers, it combines chat and voice interfaces, advanced semantic search, and explainable recommendations. The system is built with a modular, production-ready architecture featuring LangGraph multi-agent workflow orchestration for rapid feature development and real-world integrations.

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
| AI Orchestration        | LangGraph (multi-agent workflow orchestration) |
| LLM                     | OpenAI GPT-4o (tool-calling, embeddings)     |
| Voice Assistant         | ElevenLabs (voice input/output)              |
| Data                    | MySQL (structured) + ChromaDB (vector store) |
| PDF Metadata Extraction | CrewAI + PyPDF2 + OpenAI model               |
| Schemas                 | Pydantic (strict validation)                 |
| Testing                 | Pytest (backend)                             |

---

## 🏗️ LangGraph Multi-Agent Architecture

AI Book Seeker uses a **LangGraph-based multi-agent workflow** that provides robust orchestration, parallel execution, and scalable agent coordination.

### **Core Workflow Components**

```mermaid
flowchart TD
    Start([Start]) --> Router[Router Node]
    Router --> ParameterExtraction[Parameter Extraction]
    ParameterExtraction --> AgentCoordinator[Agent Coordinator]
    AgentCoordinator --> GeneralAgent[General Agent]
    AgentCoordinator --> GeneralVoiceAgent[General Voice Agent]
    GeneralAgent --> FAQTool[FAQ Tool]
    GeneralAgent --> BookRecTool[Book Recommendation Tool]
    GeneralVoiceAgent --> BookRecTool
    FAQTool --> Merge[Merge Tools]
    BookRecTool --> Merge
    Merge --> Format[Format Response]
    Format --> End([End])

    %% Error handling via conditional edges
    Router -.->|Error| Error[Error Node]
    ParameterExtraction -.->|Error| Error
    AgentCoordinator -.->|Error| Error
    GeneralAgent -.->|Error| Error
    GeneralVoiceAgent -.->|Error| Error
    FAQTool -.->|Error| Error
    BookRecTool -.->|Error| Error
    Merge -.->|Error| Error
    Format -.->|Error| Error
    Error --> End
```

### **Key Architectural Features**

#### **Pure Conditional Edge System**
- **Static edges** only for deterministic routing (entry/exit points, result collection)
- **Conditional edges** for all dynamic routing decisions (agent selection, tool routing)
- **No edge conflicts** - clean separation of concerns
- **Explicit error handling** through conditional routing

#### **Multi-Agent Parallel Execution**
- **Router Node**: Analyzes queries and determines routing strategy
- **Parameter Extraction**: Extracts structured parameters using LLM
- **Agent Coordinator**: Manages multi-agent parallel execution
- **Specialized Agents**: General and Voice agents with specific tool access
- **Tool Execution**: Parallel tool execution with proper state merging

#### **State Management**
- **Concurrent Updates**: Support for multi-tool parallel execution
- **State Merging**: Intelligent merging of agent results and shared data
- **Memory Management**: Redis-based session memory with automatic cleanup
- **Performance Optimization**: Caching and memory optimization layers

### **Agent Types**

| Agent | Role | Tools | Interface Support |
|-------|------|-------|-------------------|
| **General Agent** | General query handling | FAQ Tool, Book Recommendation Tool | Chat |
| **General Voice Agent** | Voice interface specialist | Book Recommendation Tool | Voice |

### **Workflow Benefits**

- ✅ **Scalable Orchestration**: Easy to add new agents and tools
- ✅ **Parallel Execution**: Multi-agent and multi-tool parallelism
- ✅ **Streaming Responses**: Real-time workflow state updates
- ✅ **Error Recovery**: Graceful error handling and fallback mechanisms
- ✅ **Type Safety**: Full Pydantic validation throughout
- ✅ **Performance**: Optimized for production use with caching

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
   CHROMADB_BOOK_PERSIST_DIRECTORY=./chromadb_books
   CHROMADB_BOOK_COLLECTION_NAME=books_collection
   CHROMADB_FAQ_PERSIST_DIRECTORY=./chromadb_faq
   CHROMADB_FAQ_COLLECTION_NAME=faq_collection
   ELEVENLABS_API_KEY=your_elevenlabs_api_key
   X_API_KEY=your_backend_webhook_secret
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
| Natural Language Understanding | Processes user requests in everyday language without requiring specific formats          | LangGraph router node with LLM-powered query analysis                |
| Query Flexibility              | Handles unexpected or novel request types beyond training examples                       | Zero-shot capability in system prompts and general query handling    |
| Consistent Output Formatting   | Ensures recommendations follow standardized, user-friendly formats                       | One-shot learning with example templates in explainer.py             |
| Intelligent Function Selection | Automatically selects appropriate search functions based on user needs                   | LangGraph conditional edge routing with tool selection logic         |
| Semantic Search                | Finds relevant books beyond exact keyword matching, improving results                    | RAG (Retrieval Augmented Generation) with ChromaDB vector embeddings |
| Conversational Memory          | Remembers previous interactions for natural, ongoing conversations                       | Context-aware memory system with Redis and automatic summarization   |
| PDF Metadata Extraction        | Automatically extracts structured metadata from PDF books with high accuracy             | AI agent crew with specialized roles for content analysis            |
| Voice Assistant                | Voice input/output for book recommendations and FAQ                                      | ElevenLabs integration, backend webhook, system prompt engineering   |
| Voice AI                       | Natural language voice interaction for book search and FAQ                               | ElevenLabs, backend webhook, prompt engineering                      |
| FAQ Vector Search              | Answers common questions using vector-based FAQ index (chat: backend, voice: ElevenLabs) | System prompt, vector DB, and ElevenLabs knowledge base              |
| Explainable Recommendations    | Provides clear, human-style explanations for all suggestions                             | Explainer module, prompt engineering, and output schema enforcement  |
| Modular, Extensible Backend    | Rapid feature development and integration with new tools/APIs                            | Feature-based folder structure, Pydantic, LangGraph, FastAPI         |
| Security & Observability       | Secure, predictable, and debuggable flows for all major features                         | x_api_key, structured logging, strict schema validation              |
| Multi-Agent Parallel Execution | Simultaneous processing by multiple specialized agents                                   | LangGraph agent coordinator with parallel execution support          |
| Streaming Workflow Updates     | Real-time workflow state updates for better user experience                             | LangGraph streaming with immediate response formatting               |

---

## System Flow

The following diagram illustrates the LangGraph workflow for both chat and voice interactions:

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

    %% Backend group: POST /chat and LangGraph workflow
    subgraph BackendSection["Backend - LangGraph Workflow"]
        ChatAPI["POST /chat"]
        LangGraphOrchestrator["LangGraph Workflow Orchestrator"]
        RouterNode["Router Node"]
        ParameterExtraction["Parameter Extraction"]
        AgentCoordinator["Agent Coordinator"]
        GeneralAgent["General Agent"]
        GeneralVoiceAgent["General Voice Agent"]
        FAQTool["FAQ Tool"]
        BookRecTool["Book Recommendation Tool"]
        MergeTools["Merge Tools"]
        FormatResponse["Format Response"]
        Memory["Session Memory (Redis)"]
        Logging["Structured Logging/Error Handling"]

        ChatAPI --> LangGraphOrchestrator
        LangGraphOrchestrator --> RouterNode
        RouterNode --> ParameterExtraction
        ParameterExtraction --> AgentCoordinator
        AgentCoordinator --> GeneralAgent
        AgentCoordinator --> GeneralVoiceAgent
        GeneralAgent --> FAQTool
        GeneralAgent --> BookRecTool
        GeneralVoiceAgent --> BookRecTool
        FAQTool --> MergeTools
        BookRecTool --> MergeTools
        MergeTools --> FormatResponse
        FormatResponse --> Memory
        LangGraphOrchestrator --> Logging
        FormatResponse --> UI
    end

    %% Voice (ElevenLabs) group: Widget, POST /voice, Knowledge Base (right)
    subgraph ElevenLabsSection["Voice (ElevenLabs)"]
        ElevenLabs["ElevenLabs Widget"]
        VoiceAPI["POST /voice"]
        EL_KB["Knowledge Base"]
        ElevenLabs --> EL_KB
        ElevenLabs -->|Speech| User
        ElevenLabs --> VoiceAPI
        VoiceAPI --> LangGraphOrchestrator
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
    class BackendSection,LangGraphOrchestrator,RouterNode,ParameterExtraction,AgentCoordinator,GeneralAgent,GeneralVoiceAgent,FAQTool,BookRecTool,MergeTools,FormatResponse,Memory,Logging,ChatAPI backend;
    classDef data fill:#bbf,stroke:#333,stroke-width:1px;
    class ChromaDB,MySQL data;
```

Note: All arrows represent main data/request flow. The LangGraph workflow provides parallel execution, streaming responses, and robust error handling.

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
│   │       ├── services/    # Core services (tools, memory, explainer, etc.)
│   │       ├── utils/       # Utility functions
│   │       ├── workflows/   # LangGraph workflow orchestration
│   │       │   ├── agents/  # Agent implementations (general, general_voice, sales)
│   │       │   ├── nodes/   # Workflow nodes (router, coordinator, tools)
│   │       │   ├── prompts/ # Workflow-specific prompt templates
│   │       │   ├── schemas/ # Workflow state and data models
│   │       │   ├── utils/   # Workflow utilities (error_handling, message_factory, etc.)
│   │       │   └── orchestrator.py # Main workflow orchestration
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

### **Core Endpoints**

- **POST `/api/chat/stream`** — Streaming conversational chat interface with LangGraph workflow (FAQ + book recommendations)
- **POST `/api/voice`** — Voice webhook for book recommendations (x_api_key required)
- **POST `/api/metadata/extract`** — PDF metadata extraction

### **Session Management**

- **DELETE `/api/session/{session_id}`** — Delete a user session

### **Health & Monitoring**

- **GET `/`** — Basic API status
- **GET `/health`** — Comprehensive health check
- **POST `/health/cache/clear`** — Clear health check cache
- **GET `/health/state-management`** — State management metrics

**Security:**

- `/voice` endpoint requires `x_api_key` header for secure server-to-server calls (never exposed to frontend).

**Schemas:**

- All endpoints use strict Pydantic schemas for request/response validation.

---

## 🧪 Testing & Quality

- **Test Suite:** Comprehensive unit and integration tests for backend features, LangGraph workflows, and API endpoints.
- **How to Run:**
  - Backend: `uv run pytest tests/ -v`
- **Coverage:** Tests for chat, book recommendation, FAQ, metadata extraction, and LangGraph workflow components.
- **Current Status:** All systems operational with 100% test pass rate. LangGraph multi-agent architecture fully functional with comprehensive workflow testing.

---

## 🗺️ Roadmap

### ✅ Live

- Natural language chat (text) with LangGraph workflow orchestration
- FAQ search (vector-based) with multi-agent parallel execution
- Book recommendations (explainable, personalized) with streaming responses
- PDF metadata extraction with CrewAI agent pipeline
- Voice assistant (ElevenLabs integration, `/voice` endpoint)
- Modular, feature-based backend with LangGraph architecture
- Pure conditional edge system with no routing conflicts
- Multi-agent and multi-tool parallel execution

### 🔜 Next

- Performance optimizations and monitoring
- Dynamic agent creation and adaptive routing
- Improve accuracy



## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
