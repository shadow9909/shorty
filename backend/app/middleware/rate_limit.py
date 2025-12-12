"""Middleware for rate limiting API requests."""
import logging
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting API requests."""
    
    def __init__(self, app):
        super().__init__(app)
        
        # Define rate limits per endpoint pattern
        # Format: (path_pattern, requests_per_minute)
        self.rate_limits = {
            "/api/urls/": 20,  # URL creation
            "/api/auth/register": 5,  # Registration
            "/api/auth/login": 10,  # Login
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limits before processing request."""
        from app.services.rate_limiter import check_rate_limit
        
        # Skip rate limiting for health checks and docs
        if request.url.path.startswith(("/health", "/docs", "/openapi.json", "/redoc")):
            return await call_next(request)
        
        # Get client identifier (IP address)
        client_ip = request.client.host if request.client else "unknown"
        
        # Find matching rate limit
        limit_per_minute = None
        for path_pattern, limit in self.rate_limits.items():
            if request.url.path.startswith(path_pattern):
                limit_per_minute = limit
                break
        
        # Apply rate limiting if configured for this endpoint
        if limit_per_minute:
            identifier = f"{client_ip}:{request.url.path}"
            
            is_allowed, remaining = await check_rate_limit(
                identifier=identifier,
                limit=limit_per_minute,
                window_seconds=60
            )
            
            if not is_allowed:
                # Calculate retry-after time
                retry_after = 60
                
                logger.warning(
                    "Rate limit exceeded",
                    extra={
                        "client_ip": client_ip,
                        "path": request.url.path,
                        "limit": limit_per_minute,
                    }
                )
                
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": f"Rate limit exceeded. Maximum {limit_per_minute} requests per minute.",
                        "retry_after": retry_after
                    },
                    headers={"Retry-After": str(retry_after)}
                )
        
        return await call_next(request)
