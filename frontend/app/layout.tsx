import './globals.css'
import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
    title: 'AI Book Seeker',
    description: 'Find the perfect children\'s books based on age, interests, and budget',
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="en">
            <body className={inter.className}>
                <header className="bg-blue-600 p-4 text-white">
                    <div className="container mx-auto">
                        <h1 className="text-2xl font-bold">📚 AI Book Seeker</h1>
                    </div>
                </header>
                <main className="container mx-auto p-4">
                    {children}
                </main>
                <footer className="p-4 text-center text-gray-600 text-sm">
                    <p>© 2024 AI Book Seeker - Find the perfect books for children</p>
                </footer>
            </body>
        </html>
    )
}
