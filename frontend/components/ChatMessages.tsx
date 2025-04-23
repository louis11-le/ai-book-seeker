"use client";

import { useEffect, useRef } from 'react';
import { MessageType } from '../types';

interface ChatMessagesProps {
    messages: MessageType[];
    isLoading: boolean;
}

export default function ChatMessages({ messages, isLoading }: ChatMessagesProps) {
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom on new messages
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    return (
        <div className="space-y-4">
            {messages.map((message, index) => (
                <div
                    key={index}
                    className={`p-3 rounded-lg ${message.role === 'user'
                            ? 'bg-blue-50 ml-8'
                            : message.role === 'system'
                                ? 'bg-gray-100 text-gray-700'
                                : 'bg-gray-200 mr-8'
                        }`}
                >
                    <div className="font-semibold mb-1">
                        {message.role === 'user' ? 'You' : message.role === 'system' ? 'System' : '📚 AI Book Seeker'}
                    </div>
                    <div className="whitespace-pre-wrap">{message.content}</div>
                </div>
            ))}

            {isLoading && (
                <div className="p-3 rounded-lg bg-gray-200 mr-8 animate-pulse">
                    <div className="font-semibold mb-1">📚 AI Book Seeker</div>
                    <div>Thinking...</div>
                </div>
            )}

            <div ref={messagesEndRef} />
        </div>
    );
}
