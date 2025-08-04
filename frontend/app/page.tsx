"use client";

import { useState } from 'react';
import ChatInput from '../components/ChatInput';
import ChatMessages from '../components/ChatMessages';
import ElevenLabsWidget from '../components/ElevenLabsWidget';
import { BookType, MessageType } from '../types';

// API response types
interface AgentResults {
    book_recommendation?: {
        text: string;
        data: BookType[];
    };
}

interface ResponseData {
    node?: string;
    agent_results?: AgentResults;
}

interface ServerResponse {
    session_id?: string;
    response?: {
        output?: string;
        data?: ResponseData;
    };
}

// Constants
const WELCOME_MESSAGE = 'Welcome to AI Book Seeker! Ask me about books for specific ages, interests, or learning needs.';
const COMPLETION_SIGNAL = '[DONE]';
const ERROR_PREFIX = 'Error:';

export default function Home() {
    const [messages, setMessages] = useState<MessageType[]>([
        { role: 'system', content: WELCOME_MESSAGE }
    ]);

    const [sessionId, setSessionIdState] = useState<string | null>(() => {
        if (typeof window !== 'undefined') {
            return localStorage.getItem('chatSessionId');
        }
        return null;
    });

    const [isLoading, setIsLoading] = useState(false);
    const [books, setBooks] = useState<BookType[]>([]);

    const setSessionId = (id: string | null) => {
        setSessionIdState(id);
        if (id) {
            localStorage.setItem('chatSessionId', id);
        } else {
            localStorage.removeItem('chatSessionId');
        }
    };

    const handleResetSession = () => {
        setSessionId(null);
        setMessages([{ role: 'system', content: WELCOME_MESSAGE }]);
        setBooks([]);
    };

    const isUserFacingContent = (data: ServerResponse): boolean => {
        const node = data.response?.data?.node;
        return Boolean(node && (node.endsWith("_tool") || node === "format_response"));
    };

    const extractBooksFromResponse = (data: ServerResponse): BookType[] => {
        return data.response?.data?.agent_results?.book_recommendation?.data || [];
    };

    const handleSendMessage = async (message: string) => {
        if (!message.trim()) return;

        setMessages(prev => [...prev, { role: 'user', content: message }]);
        setIsLoading(true);

        try {
            const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || '';
            const response = await fetch(`${apiBase}/api/chat/stream`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message, session_id: sessionId }),
            });

            if (!response.body) throw new Error('No response body');

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let newSessionId: string | null = null;

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });

                const lines = buffer.split('\n');
                buffer = lines.pop()!;

                for (const line of lines) {
                    if (line.trim()) {
                        try {
                            const data: ServerResponse = JSON.parse(line);
                            if (data.session_id) {
                                newSessionId = data.session_id;
                            }

                            if (data.response?.output !== undefined &&
                                data.response.output !== COMPLETION_SIGNAL &&
                                !data.response.output.startsWith(ERROR_PREFIX) &&
                                isUserFacingContent(data)) {

                                const output = data.response.output;
                                setMessages(prev => [...prev, { role: 'assistant' as const, content: output }]);
                            }

                            const extractedBooks = extractBooksFromResponse(data);
                            if (extractedBooks.length > 0) {
                                setBooks(extractedBooks);
                            }

                        } catch (e) {
                            // Log JSON parse errors
                            console.warn('[STREAM] Failed to parse streaming response:', e, line);
                        }
                    }
                }
            }

            if (newSessionId) {
                setSessionId(newSessionId);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Sorry, there was an error processing your request. Please try again.'
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex flex-col min-h-[calc(100vh-160px)]">
            <div className="bg-white p-6 rounded-lg shadow-md mb-6">
                <h1 className="text-xl font-semibold mb-2">Find the Perfect Books</h1>
                <p className="text-gray-600">
                    Ask about books by age, interests, and budget. For example:
                    "I need books for my 6-year-old who is learning to read. My budget is around $50."
                </p>
                <button
                    className="mt-4 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
                    onClick={handleResetSession}
                >
                    Reset Chat Session
                </button>
            </div>

            <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                <div className="md:col-span-2 flex flex-col h-full">
                    <div className="flex-1 overflow-y-auto bg-white rounded-lg shadow-md p-4 mb-4">
                        <ChatMessages messages={messages} isLoading={isLoading} />
                    </div>
                    <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
                </div>
                <div className="bg-white rounded-lg shadow-md p-4 overflow-y-auto">
                    <h2 className="font-semibold text-lg mb-4">Book Recommendations</h2>
                    {books.length > 0 ? (
                        <ul className="space-y-4">
                            {books.map((book) => (
                                <li key={book.id} className="border-b pb-3">
                                    <h3 className="font-bold">{book.title}</h3>
                                    <p className="text-sm text-gray-600">by {book.author}</p>
                                    <p className="my-1">{book.description}</p>
                                    {book.reason && (
                                        <p className="mt-2 text-sm italic text-gray-700 bg-yellow-50 p-2 rounded">
                                            <span className="font-semibold">Why this matches:</span> {book.reason}
                                        </p>
                                    )}
                                    <div className="mt-2 text-sm">
                                        <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded mr-2">
                                            Age: {book.from_age && book.to_age
                                                ? `${book.from_age}-${book.to_age}`
                                                : "All ages"}
                                        </span>
                                        <span className="bg-green-100 text-green-800 px-2 py-1 rounded">
                                            ${book.price.toFixed(2)}
                                        </span>
                                    </div>
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <p className="text-gray-500 italic">Book recommendations will appear here.</p>
                    )}
                </div>
            </div>
            <ElevenLabsWidget />
        </div>
    );
}
