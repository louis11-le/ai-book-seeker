# AI Book Seeker Frontend

A modern Next.js application for helping users find the perfect books based on age, interests, and budget through a conversational interface.

## 📚 Overview

AI Book Seeker provides an intuitive chat interface where users can describe what kind of books they're looking for. The application communicates with an AI-powered backend to provide personalized book recommendations with explanations of why each book matches the user's needs.

## 🚀 Getting Started

### Prerequisites

- Node.js 16.x or higher
- Yarn or npm

### Installation

```bash
# Clone the repository (if you haven't already)
git clone https://github.com/yourusername/ai-book-seeker.git
cd ai-book-seeker/frontend

# Install dependencies
yarn install
# or
npm install
```

### Running the Application

```bash
# Development mode
yarn dev
# or
npm run dev

# Build for production
yarn build
# or
npm run build

# Start production server
yarn start
# or
npm start
```

The application will be available at [http://localhost:3000](http://localhost:3000).

## 💻 Technologies

- [Next.js](https://nextjs.org/) - React framework
- [TypeScript](https://www.typescriptlang.org/) - Type-safe JavaScript
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS framework
- [Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API) - For API communication

## 🔄 Workflow

1. Users enter their book preferences in natural language
2. The frontend sends the query to the backend API
3. Backend processes the request using AI models
4. Results are returned with book recommendations and explanations
5. Frontend displays the recommendations in a user-friendly interface

## 🌐 API Integration

The frontend communicates with the backend through a REST API:

- **Endpoint**: `/api/chat`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "message": "User's input message",
    "session_id": "Optional session ID for continuing conversations"
  }
  ```
- **Response**:
  ```json
  {
    "session_id": "Unique session identifier",
    "response": {
      "input": "User's input message",
      "output": "AI assistant's latest response"
    }
  }
  ```

> Note: Only the latest assistant message is returned in the response. The client is responsible for managing chat history if needed.

## 🌐 Streaming API Integration

The backend supports real-time streaming of chat responses:

- **Endpoint**: `/api/chat/stream`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "message": "User's input message",
    "session_id": "Optional session ID for continuing conversations"
  }
  ```
- **Streaming Response**:
  - The response is a stream of newline-delimited JSON objects, each with an `output` field containing the latest chunk of the assistant's reply.
  - Example stream:
    ```json
    {"output": "Hello"}
    {"output": "Hello, how"}
    {"output": "Hello, how can I help you?"}
    ```
- **Usage**: Use the Fetch API with a ReadableStream to process each chunk as it arrives and update the UI in real time.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.
