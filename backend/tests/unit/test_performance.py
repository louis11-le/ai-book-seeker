"""
Unit tests for performance optimization utilities.
"""

from unittest.mock import Mock

from ai_book_seeker.workflows.utils.performance import (
    MergeCache,
    cache_merge_result,
    optimize_merge_operation,
)


class TestMergeCache:
    """Test the MergeCache class."""

    def test_cache_operations(self):
        """Test basic cache operations."""
        cache = MergeCache(max_size=2)

        left = Mock()
        right = Mock()
        result = Mock()

        # Test cache miss
        assert cache.get(left, right) is None

        # Test cache set and get
        cache.set(left, right, result)
        assert cache.get(left, right) == result

    def test_cache_eviction(self):
        """Test LRU cache eviction."""
        cache = MergeCache(max_size=2)

        left1, right1, result1 = Mock(), Mock(), Mock()
        left2, right2, result2 = Mock(), Mock(), Mock()
        left3, right3, result3 = Mock(), Mock(), Mock()

        # Fill cache
        cache.set(left1, right1, result1)
        cache.set(left2, right2, result2)

        # Add third item (should evict first)
        cache.set(left3, right3, result3)

        # First item should be evicted
        assert cache.get(left1, right1) is None
        assert cache.get(left2, right2) == result2
        assert cache.get(left3, right3) == result3

    def test_cache_access_order(self):
        """Test that cache access updates LRU order."""
        cache = MergeCache(max_size=2)

        left1, right1, result1 = Mock(), Mock(), Mock()
        left2, right2, result2 = Mock(), Mock(), Mock()
        left3, right3, result3 = Mock(), Mock(), Mock()

        # Fill cache
        cache.set(left1, right1, result1)
        cache.set(left2, right2, result2)

        # Access first item (should make it most recently used)
        cache.get(left1, right1)

        # Add third item (should evict second, not first)
        cache.set(left3, right3, result3)

        assert cache.get(left1, right1) == result1
        assert cache.get(left2, right2) is None
        assert cache.get(left3, right3) == result3

    def test_cache_clear(self):
        """Test cache clearing."""
        cache = MergeCache()

        left, right, result = Mock(), Mock(), Mock()
        cache.set(left, right, result)

        assert cache.get(left, right) == result

        cache.clear()
        assert cache.get(left, right) is None

    def test_cache_stats(self):
        """Test cache statistics."""
        cache = MergeCache(max_size=10)

        left, right, result = Mock(), Mock(), Mock()
        cache.set(left, right, result)

        stats = cache.get_stats()
        assert stats["size"] == 1
        assert stats["max_size"] == 10
        assert stats["oldest_entry"] is not None

    def test_cache_key_generation(self):
        """Test cache key generation."""
        cache = MergeCache()

        left = Mock()
        right = Mock()

        # Test that same objects generate same key
        key1 = cache._generate_cache_key(left, right)
        key2 = cache._generate_cache_key(left, right)
        assert key1 == key2

        # Test that different objects generate different keys
        different_right = Mock()
        key3 = cache._generate_cache_key(left, different_right)
        assert key1 != key3


class TestCachingDecorators:
    """Test caching decorators."""

    def test_cache_merge_result(self):
        """Test cache_merge_result decorator."""
        call_count = 0

        @cache_merge_result
        def test_merge(left, right):
            nonlocal call_count
            call_count += 1
            return f"merged_{left}_{right}"

        left, right = Mock(), Mock()

        # First call should execute function
        result1 = test_merge(left, right)
        assert result1 == "merged_{}_{}".format(left, right)
        assert call_count == 1

        # Second call should use cache
        result2 = test_merge(left, right)
        assert result2 == result1
        assert call_count == 1  # Should not increment

    def test_optimize_merge_operation(self):
        """Test optimize_merge_operation decorator."""
        call_count = 0

        @optimize_merge_operation
        def test_merge(left, right):
            nonlocal call_count
            call_count += 1
            return f"optimized_{left}_{right}"

        left, right = Mock(), Mock()

        # First call should execute function
        result1 = test_merge(left, right)
        assert result1 == "optimized_{}_{}".format(left, right)
        assert call_count == 1

        # Second call should use cache
        result2 = test_merge(left, right)
        assert result2 == result1
        assert call_count == 1  # Should not increment


class TestIntegrationScenarios:
    """Test integration scenarios for performance optimization."""

    def test_full_optimization_pipeline(self):
        """Test the complete optimization pipeline."""
        call_count = 0

        @optimize_merge_operation
        def test_merge(left, right):
            nonlocal call_count
            call_count += 1
            return f"pipeline_{left}_{right}"

        left, right = Mock(), Mock()

        # Test multiple calls
        for i in range(3):
            result = test_merge(left, right)
            assert result == "pipeline_{}_{}".format(left, right)

        # Should only call function once due to caching
        assert call_count == 1

    def test_cache_and_optimization_integration(self):
        """Test integration between caching and optimization."""
        call_count = 0

        @optimize_merge_operation
        def cached_merge(left, right):
            nonlocal call_count
            call_count += 1
            return f"cached_{left}_{right}"

        left1, right1 = Mock(), Mock()
        left2, right2 = Mock(), Mock()

        # Test different inputs
        result1 = cached_merge(left1, right1)
        result2 = cached_merge(left2, right2)

        assert result1 != result2
        assert call_count == 2  # Each unique input should call function once

        # Test cache hits
        result1_again = cached_merge(left1, right1)
        result2_again = cached_merge(left2, right2)

        assert result1_again == result1
        assert result2_again == result2
        assert call_count == 2  # Should not increment for cache hits
