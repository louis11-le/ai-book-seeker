"use client";

import { useState, useEffect } from 'react';
import ChatInput from '../components/ChatInput';
import ChatMessages from '../components/ChatMessages';
import { BookType, MessageType } from '../types';
import Script from "next/script";

export default function Home() {
    const [messages, setMessages] = useState<MessageType[]>([
        {
            role: 'system',
            content: 'Welcome to AI Book Seeker! Ask me about books for specific ages, interests, or learning needs.'
        }
    ]);

    // Initialize sessionId from localStorage if available
    const [sessionId, setSessionIdState] = useState<string | null>(() => {
        if (typeof window !== 'undefined') {
            return localStorage.getItem('chatSessionId');
        }
        return null;
    });

    const setSessionId = (id: string | null) => {
        setSessionIdState(id);
        if (id) {
            localStorage.setItem('chatSessionId', id);
        } else {
            localStorage.removeItem('chatSessionId');
        }
    };
    const [isLoading, setIsLoading] = useState(false);
    const [books, setBooks] = useState<BookType[]>([]);

    // Optional: Clear session handler
    const handleResetSession = () => {
        setSessionId(null);
        setMessages([
            {
                role: 'system',
                content: "Welcome to AI Book Seeker! Ask me about books for specific ages, interests, or learning needs."
            }
        ]);
        setBooks([]);
    };

    const handleSendMessage = async (message: string) => {
        if (!message.trim()) return;

        // Add user message to chat
        setMessages(prev => [...prev, { role: 'user', content: message }]);
        setIsLoading(true);

        try {
            // Use environment variable for API base URL (production ready)
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

                // Split on newlines (each line is a JSON object)
                let lines = buffer.split('\n');
                buffer = lines.pop()!; // Last item may be incomplete

                for (const line of lines) {
                    if (line.trim()) {
                        try {
                            const data = JSON.parse(line);
                            // Update sessionId if present
                            if (data.session_id) newSessionId = data.session_id;
                            // Append streamed assistant message
                            if (data.response && data.response.output !== undefined) {
                                assistantMessage += data.response.output;
                                if (isFirstChunk) {
                                    setMessages(prev => [...prev, { role: 'assistant' as const, content: assistantMessage }]);
                                    isFirstChunk = false;
                                } else {
                                    setMessages(prev => {
                                        // Update the last assistant message
                                        const updated = [...prev];
                                        const lastIdx = updated.length - 1;
                                        if (updated[lastIdx]?.role === 'assistant') {
                                            updated[lastIdx] = { ...updated[lastIdx], content: assistantMessage };
                                        }
                                        return updated;
                                    });
                                }
                            }
                            // Set books if data is present
                            // console.log(data);
                            // if (data.data && Array.isArray(data.data)) {
                            //     setBooks(data.data);
                            // }
                        } catch (e) {
                            // Ignore JSON parse errors for incomplete lines
                        }
                    }
                }
            }
            // Persist sessionId if updated
            if (newSessionId) setSessionId(newSessionId);
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
                {/* Reset Session Button */}
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

                {/* <div className="bg-white rounded-lg shadow-md p-4 overflow-y-auto">
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
                </div> */}
            </div>
            {/* ElevenLabs Voice Assistant Widget */}
            <div id="elevenlabs-widget" dangerouslySetInnerHTML={{ __html: `<elevenlabs-convai agent-id=\"agent_01jzafryw2fmpbg8pfm6q1apc1\"></elevenlabs-convai>` }} />
            <Script src="https://unpkg.com/@elevenlabs/convai-widget-embed" async strategy="afterInteractive" />
        </div>
    );
}
