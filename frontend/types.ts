export interface MessageType {
    role: 'user' | 'assistant' | 'system';
    content: string;
}

export interface BookType {
    id: number;
    title: string;
    author: string;
    description: string;
    from_age: number;
    to_age: number;
    purpose: string;
    genre: string;
    price: number;
    tags: string[];
    quantity: number;
    explanation?: string;
}
