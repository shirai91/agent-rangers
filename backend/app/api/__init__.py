"""API routes for Agent Rangers."""

from fastapi import APIRouter
from app.api import boards, columns, tasks, websocket

api_router = APIRouter()

# Include all route modules
api_router.include_router(boards.router, prefix="/boards", tags=["boards"])
api_router.include_router(columns.router, prefix="/columns", tags=["columns"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])

__all__ = ["api_router"]
