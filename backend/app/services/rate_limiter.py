"""Rate limiting service using Redis sliding window algorithm."""
from typing import Optional
from datetime import datetime, timezone
from app.cache import get_redis
from app.config import settings


async def check_rate_limit(
    identifier: str,
    limit: int,
    window_seconds: int,
    prefix: str = "ratelimit"
) -> tuple[bool, int]:
    """Check if request is within rate limit using sliding window.
    
    Args:
        identifier: Unique identifier (IP address, user ID, etc.)
        limit: Maximum number of requests allowed
        window_seconds: Time window in seconds
        prefix: Redis key prefix
        
    Returns:
        Tuple of (is_allowed, remaining_requests)
    """
    client = await get_redis()
    key = f"{prefix}:{identifier}"
    now = datetime.now(timezone.utc).timestamp()
    window_start = now - window_seconds
    # Members are timestamps (as strings), scores are timestamps (as floats).
    # Use Redis pipeline for atomic operations
    pipe = client.pipeline()
    
    # Remove old entries outside the window
    pipe.zremrangebyscore(key, 0, window_start)
    
    # Count requests in current window
    pipe.zcard(key)
    
    # Add current request
    pipe.zadd(key, {str(now): now})
    
    # Set expiration
    pipe.expire(key, window_seconds)
    
    results = await pipe.execute()
    request_count = results[1]
    
    # Check if within limit
    is_allowed = request_count < limit
    remaining = max(0, limit - request_count - 1)
    
    return is_allowed, remaining


async def check_ip_rate_limit(ip_address: str) -> tuple[bool, int]:
    """Check rate limit for IP address.
    
    Args:
        ip_address: Client IP address
        
    Returns:
        Tuple of (is_allowed, remaining_requests)
    """
    return await check_rate_limit(
        identifier=ip_address,
        limit=settings.rate_limit_per_minute,
        window_seconds=60,
        prefix="ratelimit:ip"
    )


async def check_user_rate_limit(user_id: str) -> tuple[bool, int]:
    """Check rate limit for authenticated user.
    
    Args:
        user_id: User ID
        
    Returns:
        Tuple of (is_allowed, remaining_requests)
    """
    return await check_rate_limit(
        identifier=user_id,
        limit=settings.rate_limit_per_hour,
        window_seconds=3600,
        prefix="ratelimit:user"
    )


async def check_url_creation_limit(user_id: str) -> tuple[bool, int]:
    """Check rate limit for URL creation.
    
    Args:
        user_id: User ID
        
    Returns:
        Tuple of (is_allowed, remaining_requests)
    """
    return await check_rate_limit(
        identifier=user_id,
        limit=settings.url_creation_limit_per_minute,
        window_seconds=60,
        prefix="ratelimit:url_creation"
    )


async def reset_rate_limit(identifier: str, prefix: str = "ratelimit") -> bool:
    """Reset rate limit for an identifier.
    
    Args:
        identifier: Unique identifier
        prefix: Redis key prefix
        
    Returns:
        True if reset successful
    """
    client = await get_redis()
    key = f"{prefix}:{identifier}"
    result = await client.delete(key)
    return result > 0