"""Caching utilities for LLM and embedding responses."""

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Optional

import diskcache


class Cache:
    """Disk-based cache for LLM responses and embeddings."""
    
    def __init__(self, cache_dir: str = ".cache", ttl_hours: int = 24):
        """Initialize cache.
        
        Args:
            cache_dir: Directory for cache storage
            ttl_hours: Time-to-live in hours
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache = diskcache.Cache(str(self.cache_dir))
        self.ttl_seconds = ttl_hours * 3600
    
    def _make_key(self, prefix: str, data: dict[str, Any]) -> str:
        """Create deterministic cache key from data.
        
        Args:
            prefix: Key prefix (e.g., 'llm', 'embedding')
            data: Data to hash
        
        Returns:
            SHA256 hash key
        """
        # Sort keys for deterministic serialization
        serialized = json.dumps(data, sort_keys=True)
        hash_input = f"{prefix}:{serialized}"
        return hashlib.sha256(hash_input.encode()).hexdigest()
    
    def get(self, prefix: str, data: dict[str, Any]) -> Optional[Any]:
        """Get cached value.
        
        Args:
            prefix: Key prefix
            data: Data to look up
        
        Returns:
            Cached value or None
        """
        key = self._make_key(prefix, data)
        return self.cache.get(key)
    
    def set(self, prefix: str, data: dict[str, Any], value: Any) -> None:
        """Set cached value.
        
        Args:
            prefix: Key prefix
            data: Data to hash for key
            value: Value to cache
        """
        key = self._make_key(prefix, data)
        self.cache.set(key, value, expire=self.ttl_seconds)
    
    def clear(self) -> None:
        """Clear all cached data."""
        self.cache.clear()
    
    def size(self) -> int:
        """Get number of cached items."""
        return len(self.cache)
    
    def cleanup(self) -> int:
        """Remove expired entries.
        
        Returns:
            Number of entries removed
        """
        count = 0
        for key in list(self.cache.iterkeys()):
            if self.cache.expire[key] and self.cache.expire[key] < time.time():
                del self.cache[key]
                count += 1
        return count
