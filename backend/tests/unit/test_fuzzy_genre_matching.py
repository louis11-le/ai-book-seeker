"""
Unit tests for the fuzzy genre matching functionality

This module tests the fuzzy genre matching functions to ensure they correctly
implement genre matching with synonyms and fuzzy string matching.
"""

from unittest.mock import patch

import pytest
from ai_book_seeker.features.genre_matching import (
    GENRE_ALIASES,
    GENRE_SYNONYMS,
    get_genre_similarity,
    is_genre_match,
    normalize_genre,
)


class TestGenreNormalization:
    """Test cases for genre string normalization"""

    def test_normalize_genre_basic(self):
        """Test basic genre normalization"""
        assert normalize_genre("Fantasy") == "fantasy"
        assert normalize_genre("  Science Fiction  ") == "science fiction"
        assert normalize_genre("Mystery & Thriller") == "mystery & thriller"

    def test_normalize_genre_empty(self):
        """Test normalization of empty or None genres"""
        assert normalize_genre("") == ""
        assert normalize_genre(None) == ""
        assert normalize_genre("   ") == ""

    def test_normalize_genre_punctuation(self):
        """Test normalization with punctuation"""
        assert normalize_genre("Sci-Fi") == "sci-fi"
        assert normalize_genre("Young Adult") == "young adult"
        assert normalize_genre("Picture Book") == "picture book"


class TestGenreSynonyms:
    """Test cases for genre synonyms and aliases"""

    def test_genre_synonyms_structure(self):
        """Test that genre synonyms are properly structured"""
        assert isinstance(GENRE_SYNONYMS, dict)
        assert len(GENRE_SYNONYMS) > 0

        # Check that each main genre has aliases
        for main_genre, aliases in GENRE_SYNONYMS.items():
            assert isinstance(aliases, list)
            assert len(aliases) > 0

    def test_genre_aliases_mapping(self):
        """Test that genre aliases are properly mapped"""
        assert isinstance(GENRE_ALIASES, dict)
        assert len(GENRE_ALIASES) > 0

        # Check that main genres map to themselves
        for main_genre in GENRE_SYNONYMS:
            assert GENRE_ALIASES[main_genre] == main_genre

        # Check that aliases map to main genres
        assert GENRE_ALIASES["sci-fi"] == "science fiction"
        assert GENRE_ALIASES["sf"] == "science fiction"
        assert GENRE_ALIASES["detective"] == "mystery"
        assert GENRE_ALIASES["love story"] == "romance"

    def test_specific_genre_synonyms(self):
        """Test specific genre synonym mappings"""
        # Fiction genres
        assert "novel" in GENRE_SYNONYMS["fiction"]
        assert "magical" in GENRE_SYNONYMS["fantasy"]
        assert "sci-fi" in GENRE_SYNONYMS["science fiction"]
        assert "detective" in GENRE_SYNONYMS["mystery"]

        # Non-fiction genres
        assert "nonfiction" in GENRE_SYNONYMS["non-fiction"]
        assert "memoir" in GENRE_SYNONYMS["biography"]
        assert "scientific" in GENRE_SYNONYMS["science"]

        # Educational genres
        assert "learning" in GENRE_SYNONYMS["educational"]
        assert "course book" in GENRE_SYNONYMS["textbook"]

        # Children's genres
        assert "kids" in GENRE_SYNONYMS["children"]
        assert "picturebook" in GENRE_SYNONYMS["picture book"]


class TestGenreSimilarity:
    """Test cases for genre similarity calculation"""

    def test_exact_match(self):
        """Test exact genre matches"""
        assert get_genre_similarity("fantasy", "fantasy") == 100.0
        assert get_genre_similarity("Science Fiction", "science fiction") == 100.0
        assert get_genre_similarity("MYSTERY", "mystery") == 100.0

    def test_synonym_match(self):
        """Test synonym matches"""
        assert get_genre_similarity("sci-fi", "science fiction") == 95.0
        assert get_genre_similarity("detective", "mystery") == 95.0
        assert get_genre_similarity("love story", "romance") == 95.0
        assert get_genre_similarity("novel", "fiction") == 95.0

    def test_empty_genres(self):
        """Test handling of empty genres"""
        assert get_genre_similarity("", "fantasy") == 0.0
        assert get_genre_similarity("fantasy", "") == 0.0
        assert get_genre_similarity("", "") == 0.0
        assert get_genre_similarity(None, "fantasy") == 0.0

    def test_case_insensitive(self):
        """Test case insensitive matching"""
        assert get_genre_similarity("FANTASY", "fantasy") == 100.0
        assert get_genre_similarity("Science Fiction", "SCIENCE FICTION") == 100.0

    @patch("ai_book_seeker.features.genre_matching.logic.RAPIDFUZZ_AVAILABLE", False)
    def test_fallback_without_rapidfuzz(self):
        """Test fallback behavior when RapidFuzz is not available"""
        # Should fall back to exact matching only
        assert get_genre_similarity("fantasy", "fantasy") == 100.0
        # Synonym matching still works even without RapidFuzz (it's in constants)
        assert get_genre_similarity("sci-fi", "science fiction") == 95.0  # Synonym matching
        assert get_genre_similarity("detective", "mystery") == 95.0  # Synonym matching

    @patch("ai_book_seeker.features.genre_matching.logic.RAPIDFUZZ_AVAILABLE", True)
    @patch("ai_book_seeker.features.genre_matching.logic.fuzz")
    @patch("ai_book_seeker.features.genre_matching.logic.utils")
    def test_fuzzy_matching_with_rapidfuzz(self, mock_utils, mock_fuzz):
        """Test fuzzy matching when RapidFuzz is available"""
        # Mock RapidFuzz functions
        mock_fuzz.WRatio.return_value = 85.0
        mock_fuzz.token_set_ratio.return_value = 90.0
        mock_fuzz.partial_ratio.return_value = 75.0
        mock_utils.default_process = lambda x: x.lower()

        # Test fuzzy matching for non-exact, non-synonym matches
        result = get_genre_similarity("fantasy", "fantastical")

        # Should use the best score from all scorers
        assert result == 90.0  # Best score from token_set_ratio

        # Verify that all scorers were called
        mock_fuzz.WRatio.assert_called_once()
        mock_fuzz.token_set_ratio.assert_called_once()
        mock_fuzz.partial_ratio.assert_called_once()


class TestGenreMatching:
    """Test cases for genre matching decisions"""

    def test_exact_match_returns_true(self):
        """Test that exact matches return True"""
        assert is_genre_match("fantasy", "fantasy") is True
        assert is_genre_match("Science Fiction", "science fiction") is True

    def test_synonym_match_returns_true(self):
        """Test that synonym matches return True"""
        assert is_genre_match("sci-fi", "science fiction") is True
        assert is_genre_match("detective", "mystery") is True
        assert is_genre_match("love story", "romance") is True

    def test_empty_genres_return_false(self):
        """Test that empty genres return False"""
        assert is_genre_match("", "fantasy") is False
        assert is_genre_match("fantasy", "") is False
        assert is_genre_match("", "") is False

    def test_different_genres_return_false(self):
        """Test that completely different genres return False"""
        assert is_genre_match("fantasy", "mystery") is False
        assert is_genre_match("romance", "science fiction") is False

    def test_threshold_parameter(self):
        """Test that threshold parameter works correctly"""
        # With high threshold, only exact matches should pass
        assert is_genre_match("sci-fi", "science fiction", threshold=100.0) is False
        assert is_genre_match("fantasy", "fantasy", threshold=100.0) is True

        # With low threshold, even fuzzy matches should pass
        assert is_genre_match("sci-fi", "science fiction", threshold=50.0) is True

    @patch("ai_book_seeker.features.genre_matching.logic.get_genre_similarity")
    def test_threshold_logic(self, mock_similarity):
        """Test threshold logic with mocked similarity scores"""
        # Test with similarity above threshold
        mock_similarity.return_value = 80.0
        assert is_genre_match("test", "test", threshold=70.0) is True

        # Test with similarity below threshold
        mock_similarity.return_value = 60.0
        assert is_genre_match("test", "test", threshold=70.0) is False

        # Test with similarity exactly at threshold
        mock_similarity.return_value = 70.0
        assert is_genre_match("test", "test", threshold=70.0) is True


class TestGenreMatchingIntegration:
    """Integration tests for genre matching with real scenarios"""

    def test_fiction_genre_variations(self):
        """Test various fiction genre variations"""
        fiction_variations = ["fiction", "novel", "story", "narrative", "literary"]

        for variation in fiction_variations:
            assert is_genre_match(variation, "fiction") is True
            assert is_genre_match("fiction", variation) is True

    def test_science_fiction_variations(self):
        """Test various science fiction genre variations"""
        sf_variations = ["science fiction", "sci-fi", "sf", "futuristic", "space"]

        for variation in sf_variations:
            assert is_genre_match(variation, "science fiction") is True
            assert is_genre_match("science fiction", variation) is True

    def test_mystery_variations(self):
        """Test various mystery genre variations"""
        mystery_variations = ["mystery", "detective", "crime", "thriller", "suspense"]

        for variation in mystery_variations:
            assert is_genre_match(variation, "mystery") is True
            assert is_genre_match("mystery", variation) is True

    def test_educational_variations(self):
        """Test various educational genre variations"""
        educational_variations = ["educational", "education", "learning", "teaching", "academic"]

        for variation in educational_variations:
            assert is_genre_match(variation, "educational") is True
            assert is_genre_match("educational", variation) is True

    def test_children_genre_variations(self):
        """Test various children's genre variations"""
        children_variations = ["children", "kids", "young readers", "juvenile"]

        for variation in children_variations:
            assert is_genre_match(variation, "children") is True
            assert is_genre_match("children", variation) is True


class TestGenreMatchingEdgeCases:
    """Test edge cases and error handling"""

    def test_special_characters(self):
        """Test handling of special characters in genres"""
        assert normalize_genre("Sci-Fi & Fantasy") == "sci-fi & fantasy"
        assert normalize_genre("Mystery/Thriller") == "mystery/thriller"
        assert normalize_genre("Children's Books") == "children's books"

    def test_numbers_in_genres(self):
        """Test handling of numbers in genres"""
        assert normalize_genre("Grade 1-3") == "grade 1-3"
        assert normalize_genre("Ages 8-12") == "ages 8-12"

    def test_very_long_genres(self):
        """Test handling of very long genre descriptions"""
        long_genre = "Young Adult Science Fiction with Fantasy Elements and Adventure"
        normalized = normalize_genre(long_genre)
        assert len(normalized) > 0
        assert normalized == long_genre.lower()

    def test_unicode_characters(self):
        """Test handling of unicode characters"""
        assert normalize_genre("Fantasía") == "fantasía"
        assert normalize_genre("Mystère") == "mystère"

    @patch("ai_book_seeker.features.genre_matching.logic.fuzz")
    @patch("ai_book_seeker.features.genre_matching.logic.utils")
    def test_rapidfuzz_error_handling(self, mock_utils, mock_fuzz):
        """Test error handling when RapidFuzz functions fail"""
        # Mock RapidFuzz to raise exceptions
        mock_fuzz.WRatio.side_effect = Exception("RapidFuzz error")
        mock_fuzz.token_set_ratio.side_effect = Exception("RapidFuzz error")
        mock_fuzz.partial_ratio.return_value = 75.0  # This one works
        mock_utils.default_process = lambda x: x.lower()

        # Test with non-exact, non-synonym strings to trigger fuzzy matching
        result = get_genre_similarity("fantasy", "fantastical")

        # Should use the best score from all scorers
        assert result == 75.0  # From the working scorer

        # Verify that all scorers were called
        mock_fuzz.WRatio.assert_called_once()
        mock_fuzz.token_set_ratio.assert_called_once()
        mock_fuzz.partial_ratio.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
