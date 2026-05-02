# core/performance.py
"""
Performance optimization utilities for EduMind.
"""

import functools
import time
import threading
from typing import Any, Callable, Dict, Optional, TypeVar
from datetime import datetime, timedelta
from collections import OrderedDict

from utils.logger import get_logger

logger = get_logger("performance")

T = TypeVar('T')


class LRUCache:
    """
    Least Recently Used (LRU) cache with TTL support.
    
    Features:
    - Configurable max size
    - Optional time-to-live for entries
    - Thread-safe operations
    
    Example:
        >>> cache = LRUCache(max_size=100, ttl_seconds=300)
        >>> cache.set("key1", "value1")
        >>> cache.get("key1")
        'value1'
    """
    
    def __init__(self, max_size: int = 100, ttl_seconds: Optional[int] = None):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, tuple] = OrderedDict()
        self._lock = threading.Lock()
        self._hit_count = 0
        self._miss_count = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache."""
        with self._lock:
            if key not in self._cache:
                self._miss_count += 1
                return None
            
            value, timestamp = self._cache[key]
            
            # Check TTL
            if self.ttl_seconds and (datetime.now() - timestamp).total_seconds() > self.ttl_seconds:
                del self._cache[key]
                self._miss_count += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hit_count += 1
            return value
    
    def set(self, key: str, value: Any):
        """Set a value in the cache."""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = (value, datetime.now())
            
            # Evict oldest if over max size
            while len(self._cache) > self.max_size:
                self._cache.popitem(last=False)
    
    def delete(self, key: str):
        """Remove a key from the cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._hit_count + self._miss_count
        hit_rate = (self._hit_count / total * 100) if total > 0 else 0
        
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hit_count,
            "misses": self._miss_count,
            "hit_rate": f"{hit_rate:.1f}%"
        }


def cached(ttl_seconds: Optional[int] = None, max_size: int = 128):
    """
    Decorator for caching function results.
    
    Args:
        ttl_seconds: Optional time-to-live for cached results
        max_size: Maximum cache entries
    
    Example:
        >>> @cached(ttl_seconds=60)
        ... def expensive_function(x):
        ...     return x * 2
    """
    cache = LRUCache(max_size=max_size, ttl_seconds=ttl_seconds)
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = str((args, tuple(sorted(kwargs.items()))))
            
            result = cache.get(key)
            if result is not None:
                return result
            
            result = func(*args, **kwargs)
            cache.set(key, result)
            return result
        
        wrapper.cache = cache
        wrapper.clear_cache = cache.clear
        return wrapper
    
    return decorator


def timed(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to log function execution time.
    
    Example:
        >>> @timed
        ... def slow_function():
        ...     time.sleep(1)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        
        logger.debug(f"{func.__name__} executed in {elapsed:.3f}s")
        return result
    
    return wrapper


class RateLimiter:
    """
    Rate limiter for API calls and resource-intensive operations.
    
    Example:
        >>> limiter = RateLimiter(max_calls=10, period_seconds=60)
        >>> if limiter.acquire():
        ...     make_api_call()
    """
    
    def __init__(self, max_calls: int, period_seconds: float):
        self.max_calls = max_calls
        self.period = period_seconds
        self._calls: list = []
        self._lock = threading.Lock()
    
    def acquire(self) -> bool:
        """
        Try to acquire a rate limit slot.
        
        Returns:
            True if allowed, False if rate limited
        """
        with self._lock:
            now = time.time()
            
            # Remove old calls outside the period
            self._calls = [t for t in self._calls if now - t < self.period]
            
            if len(self._calls) < self.max_calls:
                self._calls.append(now)
                return True
            
            return False
    
    def wait_and_acquire(self, timeout: float = 30.0) -> bool:
        """
        Wait for a rate limit slot to become available.
        
        Args:
            timeout: Maximum time to wait in seconds
        
        Returns:
            True if acquired, False if timeout
        """
        start = time.time()
        
        while time.time() - start < timeout:
            if self.acquire():
                return True
            time.sleep(0.1)
        
        return False


class BatchProcessor:
    """
    Process items in batches for efficiency.
    
    Example:
        >>> processor = BatchProcessor(batch_size=10)
        >>> processor.add(item1)
        >>> processor.add(item2)
        >>> results = processor.process_all(my_batch_function)
    """
    
    def __init__(self, batch_size: int = 10):
        self.batch_size = batch_size
        self._items: list = []
    
    def add(self, item: Any):
        """Add an item to be processed."""
        self._items.append(item)
    
    def add_many(self, items: list):
        """Add multiple items."""
        self._items.extend(items)
    
    def process_all(self, processor: Callable[[list], list]) -> list:
        """
        Process all items in batches.
        
        Args:
            processor: Function that takes a list and returns results
        
        Returns:
            Combined results from all batches
        """
        results = []
        
        for i in range(0, len(self._items), self.batch_size):
            batch = self._items[i:i + self.batch_size]
            batch_results = processor(batch)
            results.extend(batch_results)
        
        self._items.clear()
        return results
    
    def __len__(self) -> int:
        return len(self._items)


# Global caches
_summary_cache = LRUCache(max_size=50, ttl_seconds=3600)  # 1 hour TTL
_quiz_cache = LRUCache(max_size=50, ttl_seconds=3600)

def get_summary_cache() -> LRUCache:
    return _summary_cache

def get_quiz_cache() -> LRUCache:
    return _quiz_cache
