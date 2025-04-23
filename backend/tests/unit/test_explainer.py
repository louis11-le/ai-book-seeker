import unittest
from unittest.mock import MagicMock, patch

from db.models import Book
from explainer import (
    BookPreferences,
    _create_prompt,
    _generate_batch_explanations,
    _parse_explanations,
    generate_explanations,
)


class TestExplainer(unittest.TestCase):
    def setUp(self):
        """Set up test data before each test"""
        # Sample books for testing
        self.books = [
            Book(
                id=1,
                title="Test Book 1",
                author="Author 1",
                description="Description 1",
                age_range="5-7",
                purpose="learning",
                genre="fiction",
                price=19.99,
                tags=["tag1", "tag2"],
            ),
            Book(
                id=2,
                title="Test Book 2",
                author="Author 2",
                description="Description 2",
                age_range="6-8",
                purpose="entertainment",
                genre="adventure",
                price=24.99,
                tags=["tag3", "tag4"],
            ),
        ]

        # Sample preferences
        self.preferences = BookPreferences(
            age=6,
            purpose="learning",
            budget=50.0,
            genre="fiction",
            query_text="Books for learning to read",
        )

    def test_create_prompt(self):
        """Test the prompt creation function"""
        prompt = _create_prompt(self.books, self.preferences)

        # Check that book details are included in the prompt
        self.assertIn("Test Book 1", prompt)
        self.assertIn("Test Book 2", prompt)
        self.assertIn("Author 1", prompt)
        self.assertIn("Author 2", prompt)

        # Check that preferences are included
        self.assertIn("Age: 6", prompt)
        self.assertIn("Purpose: learning", prompt)
        self.assertIn("Budget: $50.0", prompt)
        self.assertIn("Genre: fiction", prompt)
        self.assertIn("Query: Books for learning to read", prompt)

        # Check that format instructions are included
        self.assertIn("[BOOK_ID:", prompt)
        self.assertIn("[/BOOK_ID]", prompt)

    def test_parse_explanations_with_closing_tags(self):
        """Test parsing explanations with proper closing tags"""
        content = """
        [BOOK_ID:1]
        This is an explanation for book 1.
        It's a great book for learning to read.
        [/BOOK_ID]

        [BOOK_ID:2]
        This is an explanation for book 2.
        It's perfect for entertainment.
        [/BOOK_ID]
        """

        explanations = _parse_explanations(content, self.books)

        self.assertEqual(len(explanations), 2)
        self.assertIn(1, explanations)
        self.assertIn(2, explanations)
        self.assertIn("This is an explanation for book 1.", explanations[1])
        self.assertIn("This is an explanation for book 2.", explanations[2])

    def test_parse_explanations_without_closing_tags(self):
        """Test parsing explanations without closing tags"""
        content = """
        [BOOK_ID:1] This is an explanation for book 1. It's a great book for learning to read.
        [BOOK_ID:2] This is an explanation for book 2. It's perfect for entertainment.
        """

        explanations = _parse_explanations(content, self.books)

        self.assertEqual(len(explanations), 2)
        self.assertIn(1, explanations)
        self.assertIn(2, explanations)
        self.assertIn("This is an explanation for book 1.", explanations[1])
        self.assertIn("This is an explanation for book 2.", explanations[2])

    def test_parse_explanations_consecutive_format(self):
        """Test parsing explanations in the consecutive format"""
        content = (
            "[BOOK_ID:1] This is an explanation for book 1. It's a great book for learning to read. "
            "[BOOK_ID:2] This is an explanation for book 2. It's perfect for entertainment."
        )

        explanations = _parse_explanations(content, self.books)

        self.assertEqual(len(explanations), 2)
        self.assertIn(1, explanations)
        self.assertIn(2, explanations)
        self.assertIn("This is an explanation for book 1.", explanations[1])
        self.assertIn("This is an explanation for book 2.", explanations[2])

    def test_parse_explanations_invalid_book_id(self):
        """Test parsing explanations with invalid book IDs"""
        content = """
        [BOOK_ID:999]
        This is an explanation for a nonexistent book.
        [/BOOK_ID]

        [BOOK_ID:1]
        This is an explanation for book 1.
        [/BOOK_ID]
        """

        explanations = _parse_explanations(content, self.books)

        # Should only include explanations for valid book IDs
        self.assertEqual(len(explanations), 1)
        self.assertIn(1, explanations)
        self.assertNotIn(999, explanations)

    def test_parse_explanations_malformed_content(self):
        """Test parsing explanations with malformed content"""
        content = """
        BOOK_ID:1
        This is an explanation for book 1.
        /BOOK_ID

        [BOOK_ID:2]
        This is an explanation for book 2.
        [/BOOK_ID]
        """

        explanations = _parse_explanations(content, self.books)

        # Should still extract the valid explanation
        self.assertEqual(len(explanations), 1)
        self.assertIn(2, explanations)
        self.assertNotIn(1, explanations)

    @patch("explainer.client.chat.completions.create")
    def test_generate_batch_explanations_success(self, mock_openai):
        """Test successful batch explanation generation"""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices[
            0
        ].message.content = """
        [BOOK_ID:1]
        This is an explanation for book 1.
        [/BOOK_ID]

        [BOOK_ID:2]
        This is an explanation for book 2.
        [/BOOK_ID]
        """
        mock_openai.return_value = mock_response

        explanations = _generate_batch_explanations(self.books, self.preferences)

        # Check that the function called OpenAI API
        mock_openai.assert_called_once()

        # Check that explanations were correctly extracted
        self.assertEqual(len(explanations), 2)
        self.assertIn(1, explanations)
        self.assertIn(2, explanations)

    @patch("explainer.client.chat.completions.create")
    def test_generate_batch_explanations_empty_response(self, mock_openai):
        """Test batch explanation generation with empty API response"""
        # Mock empty OpenAI response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = ""
        mock_openai.return_value = mock_response

        explanations = _generate_batch_explanations(self.books, self.preferences)

        # Should return empty dictionary
        self.assertEqual(len(explanations), 0)

    @patch("explainer.client.chat.completions.create")
    def test_generate_batch_explanations_api_error(self, mock_openai):
        """Test batch explanation generation with API error"""
        # Mock API error
        mock_openai.side_effect = Exception("API Error")

        explanations = _generate_batch_explanations(self.books, self.preferences)

        # Should handle the error and return empty dictionary
        self.assertEqual(len(explanations), 0)

    @patch("explainer._generate_batch_explanations")
    def test_generate_explanations(self, mock_generate_batch):
        """Test the main generate_explanations function"""
        # Mock the batch function to return sample explanations
        mock_generate_batch.return_value = {
            1: "Explanation for book 1",
            2: "Explanation for book 2",
        }

        explanations = generate_explanations(self.books, self.preferences)

        # Check that batch function was called
        mock_generate_batch.assert_called_once()

        # Check that explanations were returned
        self.assertEqual(len(explanations), 2)
        self.assertEqual(explanations[1], "Explanation for book 1")
        self.assertEqual(explanations[2], "Explanation for book 2")

    @patch("explainer._generate_batch_explanations")
    def test_generate_explanations_with_batching(self, mock_generate_batch):
        """Test explanation generation with batching"""
        # Create a larger list of books to test batching
        books = [Book(id=i, title=f"Book {i}", author=f"Author {i}") for i in range(1, 12)]

        # Mock the batch function to return different explanations for each call
        mock_generate_batch.side_effect = [
            {
                1: "Batch 1, Book 1",
                2: "Batch 1, Book 2",
                3: "Batch 1, Book 3",
                4: "Batch 1, Book 4",
                5: "Batch 1, Book 5",
            },
            {
                6: "Batch 2, Book 6",
                7: "Batch 2, Book 7",
                8: "Batch 2, Book 8",
                9: "Batch 2, Book 9",
                10: "Batch 2, Book 10",
            },
            {11: "Batch 3, Book 11"},
        ]

        # Patch the batch size to 5 for testing
        with patch("explainer.BATCH_SIZE", 5):
            explanations = generate_explanations(books, self.preferences)

        # Check that batch function was called multiple times
        self.assertEqual(mock_generate_batch.call_count, 3)

        # Check that all explanations were combined
        self.assertEqual(len(explanations), 11)
        self.assertEqual(explanations[1], "Batch 1, Book 1")
        self.assertEqual(explanations[6], "Batch 2, Book 6")
        self.assertEqual(explanations[11], "Batch 3, Book 11")


if __name__ == "__main__":
    unittest.main()
