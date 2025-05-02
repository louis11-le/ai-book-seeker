"use client";

import { useState } from 'react';
import ChatInput from '../components/ChatInput';
import ChatMessages from '../components/ChatMessages';
import { BookType, MessageType } from '../types';

export default function Home() {
    const [messages, setMessages] = useState<MessageType[]>([
        {
            role: 'system',
            content: 'Welcome to AI Book Seeker! Ask me about children\'s books for specific ages, interests, or learning needs.'
        }
    ]);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [books, setBooks] = useState<BookType[]>([]);

    const handleSendMessage = async (message: string) => {
        if (!message.trim()) return;

        // Add user message to chat
        setMessages(prev => [...prev, { role: 'user', content: message }]);
        setIsLoading(true);

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message,
                    session_id: sessionId,
                }),
            });

            const data = await response.json();

            // Store session ID if it's new
            if (!sessionId && data.session_id) {
                setSessionId(data.session_id);
            }

            // Add AI response to chat
            setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);

            // Store book results if any
            if (data.books && data.books.length > 0) {
                setBooks(data.books);
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
                <h1 className="text-xl font-semibold mb-2">Find the Perfect Children's Books</h1>
                <p className="text-gray-600">
                    Ask about books by age, interests, and budget. For example:
                    "I need books for my 6-year-old who is learning to read. My budget is around $50."
                </p>
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
        </div>
    );
}
