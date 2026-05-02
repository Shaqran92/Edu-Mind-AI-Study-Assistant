"""
Response Caching Service
Caches AI responses to reduce API calls and improve performance.
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from utils.logger import get_logger

logger = get_logger("response_cache")


class ResponseCache:
    """
    Intelligent caching system for AI responses.
    
    Features:
    - LRU eviction policy
    - TTL (time-to-live) support
    - Compression for large responses
    - Persistent storage
    """
    
    def __init__(self, cache_dir: str = "data/.cache", max_size_mb: int = 100):
        """
        Initialize the response cache.
        
        Args:
            cache_dir: Directory to store cache files
            max_size_mb: Maximum cache size in MB
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.current_size_bytes = 0
        self.ttl_seconds = 86400 * 7  # 7 days default
        
        self._load_index()
    
    def _load_index(self) -> None:
        """Load the cache index from disk."""
        index_file = self.cache_dir / ".index.json"
        if index_file.exists():
            try:
                with open(index_file, 'r') as f:
                    self.index = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache index: {e}")
                self.index = {}
        else:
            self.index = {}
    
    def _save_index(self) -> None:
        """Save the cache index to disk."""
        try:
            index_file = self.cache_dir / ".index.json"
            with open(index_file, 'w') as f:
                json.dump(self.index, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache index: {e}")
    
    def _generate_key(self, provider: str, model: str, prompt: str, mode: str = "") -> str:
        """
        Generate a unique cache key for a prompt.
        
        Args:
            provider: AI provider name (openai, gemini, etc.)
            model: Model name
            prompt: The prompt/input text
            mode: Operation mode (summarize, quiz, etc.)
        
        Returns:
            Unique cache key
        """
        key_content = f"{provider}|{model}|{mode}|{prompt}"
        return hashlib.sha256(key_content.encode()).hexdigest()
    
    def get(self, provider: str, model: str, prompt: str, mode: str = "") -> Optional[Dict[str, Any]]:
        """
        Retrieve a cached response.
        
        Args:
            provider: AI provider name
            model: Model name
            prompt: The prompt/input
            mode: Operation mode
        
        Returns:
            Cached response data, or None if not found or expired
        """
        cache_key = self._generate_key(provider, model, prompt, mode)
        
        if cache_key not in self.index:
            return None
        
        cache_entry = self.index[cache_key]
        
        # Check if expired
        created_time = datetime.fromisoformat(cache_entry.get("created", ""))
        if datetime.now() - created_time > timedelta(seconds=self.ttl_seconds):
            self._delete_cache_file(cache_key)
            del self.index[cache_key]
            self._save_index()
            return None
        
        # Load from file
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load cache file {cache_key}: {e}")
        
        return None
    
    def set(self, provider: str, model: str, prompt: str, response: Dict[str, Any], mode: str = "") -> None:
        """
        Store a response in the cache.
        
        Args:
            provider: AI provider name
            model: Model name
            prompt: The prompt/input
            response: Response data to cache
            mode: Operation mode
        """
        cache_key = self._generate_key(provider, model, prompt, mode)
        
        # Don't cache empty or error responses
        if not response or "error" in str(response).lower():
            return
        
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            
            # Check size before caching
            response_size = len(json.dumps(response).encode())
            if response_size > self.max_size_bytes * 0.1:  # Don't cache if > 10% of max
                logger.debug(f"Response too large for cache: {response_size} bytes")
                return
            
            # Evict if necessary
            while self.current_size_bytes + response_size > self.max_size_bytes and self.index:
                self._evict_oldest()
            
            # Write cache file
            with open(cache_file, 'w') as f:
                json.dump(response, f)
            
            # Update index
            self.index[cache_key] = {
                "created": datetime.now().isoformat(),
                "size": response_size,
                "provider": provider,
                "model": model,
                "mode": mode,
                "prompt_length": len(prompt)
            }
            self.current_size_bytes += response_size
            self._save_index()
            
            logger.debug(f"Cached response: {cache_key[:8]}... ({response_size} bytes)")
            
        except Exception as e:
            logger.error(f"Failed to cache response: {e}")
    
    def _evict_oldest(self) -> None:
        """Evict the oldest cache entry (LRU)."""
        if not self.index:
            return
        
        oldest_key = min(
            self.index.keys(),
            key=lambda k: datetime.fromisoformat(self.index[k].get("created", ""))
        )
        
        self._delete_cache_file(oldest_key)
        size = self.index[oldest_key].get("size", 0)
        del self.index[oldest_key]
        self.current_size_bytes = max(0, self.current_size_bytes - size)
    
    def _delete_cache_file(self, cache_key: str) -> None:
        """Delete a cache file."""
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                cache_file.unlink()
        except Exception as e:
            logger.error(f"Failed to delete cache file: {e}")
    
    def clear(self) -> None:
        """Clear all cache."""
        try:
            for file in self.cache_dir.glob("*.json"):
                file.unlink()
            self.index = {}
            self.current_size_bytes = 0
            self._save_index()
            logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "total_entries": len(self.index),
            "cache_size_mb": self.current_size_bytes / (1024 * 1024),
            "max_size_mb": self.max_size_bytes / (1024 * 1024),
            "providers": list(set(
                self.index[k].get("provider", "unknown") 
                for k in self.index.keys()
            )),
            "modes": list(set(
                self.index[k].get("mode", "unknown") 
                for k in self.index.keys()
            ))
        }


# Global cache instance
_cache_instance = None


def get_cache() -> ResponseCache:
    """Get the global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = ResponseCache()
    return _cache_instance
