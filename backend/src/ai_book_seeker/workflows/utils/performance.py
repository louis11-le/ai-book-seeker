"""
Performance optimization utilities for LangGraph workflow state management.

This module provides caching for merge operations to ensure optimal performance.
"""

import functools
import logging
import time
from typing import Any, Callable, Dict, Optional, TypeVar
from weakref import WeakValueDictionary

logger = logging.getLogger(__name__)

# Type variables for generic performance functions
F = TypeVar("F", bound=Callable)

# =============================================================================
# CONFIGURATION CONSTANTS
# =============================================================================

# Cache configuration
CACHE_SIZE_LIMIT = 1000
CACHE_KEY_MAX_LENGTH = 100

# =============================================================================
# CACHING SYSTEM
# =============================================================================


class MergeCache:
    """LRU cache for merge operations to improve performance."""

    def __init__(self, max_size: int = CACHE_SIZE_LIMIT):
        self.max_size = max_size
        self.cache = WeakValueDictionary()
        self.access_order = []
        self.access_times = {}

    def _generate_cache_key(self, left: Any, right: Any) -> str:
        """Generate a cache key for merge operation."""
        try:
            left_id = id(left)
            right_id = id(right)
            left_hash = hash(str(left)) if hasattr(left, "__hash__") else 0
            right_hash = hash(str(right)) if hasattr(right, "__hash__") else 0
            return f"{left_id}_{right_id}_{left_hash}_{right_hash}"
        except Exception:
            return f"{str(left)[:CACHE_KEY_MAX_LENGTH]}_{str(right)[:CACHE_KEY_MAX_LENGTH]}"

    def get(self, left: Any, right: Any) -> Optional[Any]:
        """Get cached result for merge operation."""
        cache_key = self._generate_cache_key(left, right)

        if cache_key in self.cache:
            self._update_access_order(cache_key)
            return self.cache[cache_key]

        return None

    def set(self, left: Any, right: Any, result: Any):
        """Cache result for merge operation."""
        cache_key = self._generate_cache_key(left, right)

        if len(self.cache) >= self.max_size:
            self._evict_oldest()

        self.cache[cache_key] = result
        self.access_order.append(cache_key)
        self.access_times[cache_key] = time.time()

    def _update_access_order(self, cache_key: str):
        """Update access order for LRU tracking."""
        if cache_key in self.access_order:
            self.access_order.remove(cache_key)
        self.access_order.append(cache_key)
        self.access_times[cache_key] = time.time()

    def _evict_oldest(self):
        """Evict the least recently used cache entry."""
        if self.access_order:
            oldest_key = self.access_order.pop(0)
            if oldest_key in self.cache:
                del self.cache[oldest_key]
            if oldest_key in self.access_times:
                del self.access_times[oldest_key]

    def clear(self):
        """Clear all cached entries."""
        self.cache.clear()
        self.access_order.clear()
        self.access_times.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "oldest_entry": min(self.access_times.values()) if self.access_times else None,
        }


# Global cache instance
merge_cache = MergeCache()


# =============================================================================
# CACHING DECORATORS
# =============================================================================


def cache_merge_result(func: F) -> F:
    """Decorator to cache merge operation results."""

    @functools.wraps(func)
    def wrapper(left: Any, right: Any) -> Any:
        cached_result = merge_cache.get(left, right)
        if cached_result is not None:
            return cached_result

        result = func(left, right)
        merge_cache.set(left, right, result)
        return result

    return wrapper


# =============================================================================
# PERFORMANCE OPTIMIZATION UTILITIES
# =============================================================================


def optimize_merge_operation(func: F) -> F:
    """Apply caching to a merge function."""

    @cache_merge_result
    @functools.wraps(func)
    def optimized_wrapper(left: Any, right: Any) -> Any:
        return func(left, right)

    return optimized_wrapper
