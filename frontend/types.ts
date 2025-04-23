export interface MessageType {
    role: 'user' | 'assistant' | 'system';
    content: string;
}

export interface BookType {
    id: number;
    title: string;
    author: string;
    description: string;
    age_range: string;
    purpose: string;
    genre: string;
    price: number;
    tags: string[];
    rating: number;
    explanation?: string;
}
