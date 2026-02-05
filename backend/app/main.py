"""Main FastAPI application for Agent Rangers."""

from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import update, and_

from app.config import settings
from app.database import init_db, close_db, AsyncSessionLocal
from app.api import api_router
from app.api.websocket import manager, router as ws_router
from app.models.agent_execution import AgentExecution
from app.services.file_storage import file_storage


async def cleanup_stale_executions():
    """
    Clean up stale agent executions that were left running from previous server instances.
    
    Marks executions as 'failed' if they've been running for more than 1 hour,
    which indicates the backend was restarted while they were in progress.
    """
    try:
        async with AsyncSessionLocal() as db:
            stale_threshold = datetime.utcnow() - timedelta(hours=1)
            
            result = await db.execute(
                update(AgentExecution)
                .where(
                    and_(
                        AgentExecution.status == "running",
                        AgentExecution.started_at < stale_threshold
                    )
                )
                .values(
                    status="failed",
                    error_message="Execution timed out - backend was restarted while execution was in progress",
                    completed_at=datetime.utcnow()
                )
            )
            
            await db.commit()
            
            if result.rowcount > 0:
                print(f"Cleaned up {result.rowcount} stale agent execution(s)")
            else:
                print("No stale agent executions found")
                
    except Exception as e:
        print(f"Warning: Failed to cleanup stale executions: {e}")


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

    # Initialize file storage directory structure
    file_storage.initialize()
    print(f"File storage initialized at {file_storage.base_dir}")

    # Clean up stale executions from previous server instances
    await cleanup_stale_executions()

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

# Include WebSocket routes at root level (not under /api)
app.include_router(ws_router, prefix="/ws", tags=["websocket"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info",
    )
