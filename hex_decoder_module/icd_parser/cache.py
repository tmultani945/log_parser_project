"""
In-memory cache for parsed logcode data.
"""

from typing import Optional, Any
from collections import OrderedDict


class ICDCache:
    """LRU cache for parsed logcode metadata"""

    def __init__(self, max_size: int = 50):
        """
        Initialize cache.

        Args:
            max_size: Maximum number of items to cache
        """
        self.max_size = max_size
        self.cache: OrderedDict[str, Any] = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        """
        Get item from cache (moves to end if found).

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """
        Set item in cache (evict oldest if full).

        Args:
            key: Cache key
            value: Value to cache
        """
        if key in self.cache:
            # Update existing
            self.cache.move_to_end(key)
        else:
            # Add new
            if len(self.cache) >= self.max_size:
                # Evict oldest
                self.cache.popitem(last=False)

        self.cache[key] = value

    def clear(self) -> None:
        """Clear entire cache"""
        self.cache.clear()

    def size(self) -> int:
        """Get current cache size"""
        return len(self.cache)

    def has(self, key: str) -> bool:
        """Check if key exists in cache"""
        return key in self.cache
