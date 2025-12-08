"""Redis cache utilities for caching and rate limiting."""
import json
from typing import Optional, Any
import redis.asyncio as redis
from app.config import settings

# Global Redis connection pool
_redis_pool: Optional[redis.ConnectionPool] = None
_redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Get Redis client with connection pooling.
    
    Returns:
        Redis client instance
    """
    global _redis_pool, _redis_client
    
    if _redis_client is None:
        _redis_pool = redis.ConnectionPool.from_url(
            settings.redis_url,
            decode_responses=True,
            max_connections=10
        )
        _redis_client = redis.Redis(connection_pool=_redis_pool)
    
    return _redis_client


async def close_redis():
    """Close Redis connection pool."""
    global _redis_pool, _redis_client
    
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
    
    if _redis_pool:
        await _redis_pool.disconnect()
        _redis_pool = None


async def cache_get(key: str) -> Optional[str]:
    """Get value from cache.
    
    Args:
        key: Cache key
        
    Returns:
        Cached value if exists, None otherwise
    """
    client = await get_redis()
    return await client.get(key)


async def cache_set(key: str, value: str, ttl: Optional[int] = None) -> bool:
    """Set value in cache with optional TTL.
    
    Args:
        key: Cache key
        value: Value to cache
        ttl: Time to live in seconds (defaults to settings.redis_cache_ttl)
        
    Returns:
        True if successful
    """
    client = await get_redis()
    if ttl is None:
        ttl = settings.redis_cache_ttl
    
    return await client.setex(key, ttl, value)


async def cache_delete(key: str) -> bool:
    """Delete value from cache.
    
    Args:
        key: Cache key to delete
        
    Returns:
        True if key was deleted
    """
    client = await get_redis()
    result = await client.delete(key)
    return result > 0


async def cache_get_json(key: str) -> Optional[dict]:
    """Get JSON value from cache.
    
    Args:
        key: Cache key
        
    Returns:
        Parsed JSON dict if exists, None otherwise
    """
    value = await cache_get(key)
    if value:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None
    return None


async def cache_set_json(key: str, value: dict, ttl: Optional[int] = None) -> bool:
    """Set JSON value in cache.
    
    Args:
        key: Cache key
        value: Dictionary to cache as JSON
        ttl: Time to live in seconds
        
    Returns:
        True if successful
    """
    json_str = json.dumps(value)
    return await cache_set(key, json_str, ttl)


def make_cache_key(prefix: str, *args) -> str:
    """Create a cache key from prefix and arguments.
    
    Args:
        prefix: Key prefix
        *args: Additional key components
        
    Returns:
        Formatted cache key
    """
    parts = [prefix] + [str(arg) for arg in args]
    return ":".join(parts)