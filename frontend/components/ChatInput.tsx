"use client";

import { useState, FormEvent, ChangeEvent } from 'react';

interface ChatInputProps {
    onSendMessage: (message: string) => void;
    isLoading: boolean;
}

export default function ChatInput({ onSendMessage, isLoading }: ChatInputProps) {
    const [message, setMessage] = useState('');

    const handleSubmit = (e: FormEvent) => {
        e.preventDefault();
        if (message.trim() && !isLoading) {
            onSendMessage(message);
            setMessage('');
        }
    };

    const handleChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
        setMessage(e.target.value);
    };

    return (
        <form onSubmit={handleSubmit} className="flex items-center gap-2">
            <textarea
                value={message}
                onChange={handleChange}
                placeholder="Ask about books..."
                className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y min-h-[40px] max-h-40"
                disabled={isLoading}
                rows={5}
            />
            <button
                type="submit"
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                disabled={isLoading || !message.trim()}
            >
                {isLoading ? 'Sending...' : 'Send'}
            </button>
        </form>
    );
}
