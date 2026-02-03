"""Main FastAPI application for Agent Rangers."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db, close_db
from app.api import api_router
from app.api.websocket import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.

    Handles database initialization and cleanup, as well as WebSocket manager setup.
    """
    # Startup
    print("Starting up Agent Rangers API...")
    if settings.DEBUG:
        print("Debug mode enabled - initializing database tables...")
        # await init_db()  # Uncomment for development without Alembic

    # Initialize WebSocket manager Redis connection
    await manager.initialize_redis()
    print("Redis connection initialized for WebSocket pub/sub")

    yield

    # Shutdown
    print("Shutting down Agent Rangers API...")
    await manager.close_redis()
    await close_db()
    print("Cleanup complete")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="FastAPI backend for Agent Rangers - AI Multi-Agent Kanban Framework",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom exception handler for better error responses
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors.

    Args:
        request: Request object
        exc: Exception that was raised

    Returns:
        JSON response with error details
    """
    if settings.DEBUG:
        import traceback
        error_detail = {
            "error": "Internal server error",
            "detail": str(exc),
            "traceback": traceback.format_exc(),
        }
    else:
        error_detail = {
            "error": "Internal server error",
            "detail": "An unexpected error occurred",
        }

    return JSONResponse(
        status_code=500,
        content=error_detail,
    )


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "agent-rangers-api",
        "version": "0.1.0",
    }


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint with API information.

    Returns:
        API information
    """
    return {
        "service": "Agent Rangers API",
        "version": "0.1.0",
        "description": "FastAPI backend for AI Multi-Agent Kanban Framework",
        "docs": "/docs",
        "health": "/health",
    }


# Include API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info",
    )
