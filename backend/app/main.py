"""FastAPI application."""
from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.config import settings
from app.api.auth import router as auth_router
from app.api.urls import router as urls_router
from app.db import get_db
from app.middleware import LoggingMiddleware, RateLimitMiddleware

if settings.debug:
    import debugpy
    debugpy.listen(("0.0.0.0", 5678))
    print("🐛 Debugger listening on port 5678")
    # Uncomment to wait for debugger to attach for debugging the startup process
    # debugpy.wait_for_client()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    description="Production-grade URL shortening service with analytics"
)

# Add middleware (order matters - last added is executed first)
# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging middleware (executes first to log everything)
app.add_middleware(LoggingMiddleware)

# Rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Include routers
app.include_router(auth_router)
app.include_router(urls_router)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Shorty URL Shortener API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "shorty-backend"
    }


@app.get("/health/live")
async def liveness_check():
    """Liveness probe - checks if application is running."""
    return {
        "status": "alive",
        "service": "shorty-backend",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/health/ready")
async def readiness_check():
    """Readiness probe - checks if application can serve traffic."""
    from app.cache import get_redis
    
    health_status = {
        "status": "ready",
        "service": "shorty-backend",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {}
    }
    
    # Check database connectivity
    try:
        db = get_db()
        async for session in db:
            # Simple query to check connection, wrapped in text() for SQLAlchemy 2.0 compatibility
            await session.execute(text("SELECT 1"))
            health_status["checks"]["database"] = "healthy"
            break
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "not_ready"
    
    # Check Redis connectivity
    try:
        redis_client = await get_redis()
        await redis_client.ping()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "not_ready"
    
    # Return 503 if not ready
    if health_status["status"] == "not_ready":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status
        )
    
    return health_status


@app.get("/{short_code}")
async def redirect_to_url(short_code: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Redirect short URL to original URL with analytics tracking.
    
    This endpoint:
    1. Checks Redis cache for the URL
    2. If not cached, fetches from database
    3. Validates URL is active and not expired
    4. Tracks analytics (IP, user agent, referer)
    5. Increments click count
    6. Caches URL in Redis
    7. Redirects to the original URL
    """
    from app.db.repositories import URLRepository, AnalyticsRepository
    from app.cache import cache_get_json, cache_set_json, make_cache_key
    from app.services import is_valid_short_code
    
    # Validate short code format
    if not is_valid_short_code(short_code):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid short code format"
        )
    
    # Try to get from cache first
    cache_key = make_cache_key("url", short_code)
    cached_url = await cache_get_json(cache_key)
    
    if cached_url:
        long_url = cached_url.get("long_url")
        url_id = cached_url.get("id")
        
        # Still track analytics for cached URLs
        analytics_repo = AnalyticsRepository(db)
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        referer = request.headers.get("referer")
        
        await analytics_repo.create(
            url_id=url_id,
            ip_address=ip_address,
            user_agent=user_agent,
            referer=referer
        )
        
        # Note: We don't increment click count for cached URLs to avoid DB writes
        # Click count will be updated when cache expires
    else:
        # Get from database
        url_repo = URLRepository(db)
        url = await url_repo.get_by_short_code(short_code)
        
        if not url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Short URL not found"
            )
        
        # Check if URL is expired
        if url.expires_at and url.expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="This short URL has expired"
            )
        
        long_url = url.long_url
        url_id = url.id
        
        # Track analytics
        analytics_repo = AnalyticsRepository(db)
        
        # Extract request metadata
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        referer = request.headers.get("referer")
        
        await analytics_repo.create(
            url_id=url_id,
            ip_address=ip_address,
            user_agent=user_agent,
            referer=referer
        )
        
        # Increment click count
        await url_repo.increment_click_count(url)
        
        # Cache the URL for future requests
        await cache_set_json(
            cache_key,
            {"id": url_id, "long_url": long_url},
            ttl=settings.redis_cache_ttl
        )
    
    # Redirect to the original URL
    return RedirectResponse(url=long_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    print(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    print(f"📝 Debug mode: {settings.debug}")
    print(f"📚 API docs available at: http://localhost:8000/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    from app.cache import close_redis
    await close_redis()
    print("👋 Shutting down Shorty URL Shortener")