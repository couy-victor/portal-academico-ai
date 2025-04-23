"""
Cache utilities for the Academic Agent system.
"""
import os
import json
import time
import hashlib
from typing import Any, Dict, Optional
from diskcache import Cache

from src.config.settings import CACHE_ENABLED, CACHE_DIR, CACHE_TTL

# Initialize cache
cache = Cache(CACHE_DIR)

def get_cache_key(query: str, user_context: Dict[str, Any]) -> str:
    """
    Generates a unique cache key for a query.

    Args:
        query (str): The user query
        user_context (Dict[str, Any]): User context information

    Returns:
        str: A unique cache key
    """
    # Extract only relevant context for caching
    relevant_context = {
        k: v for k, v in user_context.items()
        if k in ['user_id', 'periodo_atual', 'curso_id']
    }

    # Create a string representation of the context
    context_str = json.dumps(relevant_context, sort_keys=True)

    # Combine query and context for the key
    key_data = f"{query}:{context_str}"

    # Generate MD5 hash as the key
    return hashlib.md5(key_data.encode()).hexdigest()

def get_cache(key: str) -> Optional[Any]:
    """
    Retrieves a value from cache if it exists and is not expired.

    Args:
        key (str): Cache key

    Returns:
        Optional[Any]: Cached value or None if not found or expired
    """
    if not CACHE_ENABLED:
        return None

    cached_data = cache.get(key)

    if cached_data is None:
        return None

    # Check if the cached data is expired
    if time.time() - cached_data.get("timestamp", 0) > CACHE_TTL:
        cache.delete(key)
        return None

    return cached_data.get("data")

def set_cache(key: str, data: Any, ttl: Optional[int] = None) -> None:
    """
    Stores a value in cache with timestamp.

    Args:
        key (str): Cache key
        data (Any): Data to cache
        ttl (Optional[int]): Time-to-live in seconds, defaults to CACHE_TTL
    """
    if not CACHE_ENABLED:
        return

    cache_data = {
        "timestamp": time.time(),
        "data": data
    }

    cache.set(key, cache_data, expire=ttl or CACHE_TTL)

def invalidate_cache(key_pattern: str = None) -> None:
    """
    Invalidates cache entries matching a pattern.
    If no pattern is provided, clears the entire cache.

    Args:
        key_pattern (str, optional): Pattern to match cache keys
    """
    if not CACHE_ENABLED:
        return

    if key_pattern is None:
        cache.clear()
    else:
        # This is a simple implementation that iterates through all keys
        # For large caches, a more efficient approach would be needed
        for key in cache.iterkeys():
            if key_pattern in str(key):
                cache.delete(key)

def clear_cache() -> None:
    """
    Clears the entire cache.
    """
    if not CACHE_ENABLED:
        return

    print("Clearing cache...")
    cache.clear()
    print("Cache cleared successfully!")
