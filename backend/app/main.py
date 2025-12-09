"""FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.auth import router as auth_router

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    description="Production-grade URL shortening service with analytics"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)


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