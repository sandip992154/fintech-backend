from functools import lru_cache
import json
import time
from typing import Optional, List, Dict, Any

# Simple in-memory cache
_cache = {}
_cache_timestamps = {}
CACHE_TTL = 300  # 5 minutes

def get_cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments"""
    key_parts = [str(arg) for arg in args]
    key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
    return "|".join(key_parts)

def is_cache_valid(key: str) -> bool:
    """Check if cache entry is still valid"""
    if key not in _cache_timestamps:
        return False
    return time.time() - _cache_timestamps[key] < CACHE_TTL

def set_cache(key: str, value: Any) -> None:
    """Set cache entry"""
    _cache[key] = value
    _cache_timestamps[key] = time.time()

def get_cache(key: str) -> Optional[Any]:
    """Get cache entry if valid"""
    if key in _cache and is_cache_valid(key):
        return _cache[key]
    
    # Clean up expired entry
    if key in _cache:
        del _cache[key]
        del _cache_timestamps[key]
    
    return None

def clear_cache() -> None:
    """Clear all cache entries"""
    _cache.clear()
    _cache_timestamps.clear()

def cache_response(cache_key_prefix: str = ""):
    """Decorator for caching API responses"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{cache_key_prefix}:{get_cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_result = get_cache(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            set_cache(cache_key, result)
            
            return result
        return wrapper
    return decorator

# Specialized cache functions for common operations

@lru_cache(maxsize=100)
def get_categories_cache() -> List[str]:
    """LRU cache for categories (longer TTL since they change rarely)"""
    pass  # Implementation will be in the actual service

@lru_cache(maxsize=200) 
def get_brands_cache(category: Optional[str] = None) -> List[str]:
    """LRU cache for brands by category"""
    pass  # Implementation will be in the actual service

def cache_search_results(query_params: Dict[str, Any], results: Any) -> None:
    """Cache search results with query parameters as key"""
    cache_key = f"search:{get_cache_key(**query_params)}"
    set_cache(cache_key, results)

def get_cached_search_results(query_params: Dict[str, Any]) -> Optional[Any]:
    """Get cached search results"""
    cache_key = f"search:{get_cache_key(**query_params)}"
    return get_cache(cache_key)