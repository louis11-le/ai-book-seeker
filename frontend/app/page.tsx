"use client";

import { useState } from 'react';
import ChatInput from '../components/ChatInput';
import ChatMessages from '../components/ChatMessages';
import ElevenLabsWidget from '../components/ElevenLabsWidget';
import { BookType, MessageType } from '../types';

// Types for better type safety
interface ServerResponse {
    session_id?: string;
    response?: {
        output?: string;
        data?: {
            node?: string;
            agent_results?: {
                faq?: any;
            };
        } | BookType[];
    };
}

interface ResponseData {
    node?: string;
    agent_results?: {
        faq?: any;
    };
}

const WELCOME_MESSAGE = 'Welcome to AI Book Seeker! Ask me about books for specific ages, interests, or learning needs.';

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

    const hasMeaningfulContent = (data: ServerResponse): boolean => {
        const responseData = data.response?.data;

        // Primary check: Final formatted response from the backend
        if (responseData && !Array.isArray(responseData) && responseData.node === 'format_response') {
            return true;
        }

        // Fallback checks for legacy or edge cases
        if (responseData && Array.isArray(responseData) && responseData.length > 0) {
            return true;
        }

        if (responseData && !Array.isArray(responseData) && responseData.agent_results?.faq) {
            return true;
        }

        return false;
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
            let assistantMessage = '';
            let newSessionId: string | null = null;
            let isFirstChunk = true;

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

                            if (data.response && data.response.output !== undefined && hasMeaningfulContent(data)) {
                                const output = data.response.output;
                                assistantMessage += output;

                                if (isFirstChunk) {
                                    setMessages(prev => [...prev, { role: 'assistant' as const, content: assistantMessage }]);
                                    isFirstChunk = false;
                                } else {
                                    setMessages(prev => {
                                        const updated = [...prev];
                                        const lastIdx = updated.length - 1;
                                        if (updated[lastIdx]?.role === 'assistant') {
                                            updated[lastIdx] = { ...updated[lastIdx], content: assistantMessage };
                                        }
                                        return updated;
                                    });
                                }
                            }

                            // Book recommendations from book_recommendation_tool node
                            const responseData = data.response?.data;
                            if (
                                responseData &&
                                typeof responseData === "object" &&
                                !Array.isArray(responseData) &&
                                (responseData as any).node === "book_recommendation_tool" &&
                                (responseData as any).update?.agent_results?.book_recommendation?.data &&
                                Array.isArray((responseData as any).update.agent_results.book_recommendation.data)
                            ) {
                                setBooks((responseData as any).update.agent_results.book_recommendation.data);
                            }

                            // Legacy/other cases
                            if (data.response && Array.isArray(data.response.data)) {
                                setBooks(data.response.data);
                            }
                        } catch (e) {
                            // Ignore JSON parse errors for incomplete lines
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
                                    {book.explanation && (
                                        <p className="mt-2 text-sm italic text-gray-700 bg-yellow-50 p-2 rounded">
                                            <span className="font-semibold">Why this matches:</span> {book.explanation}
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
