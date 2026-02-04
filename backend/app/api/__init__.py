"""API routes for Agent Rangers."""

from fastapi import APIRouter
from app.api import boards, columns, tasks, websocket, workflows, activities, agents

api_router = APIRouter()

# Include all route modules
api_router.include_router(boards.router, prefix="/boards", tags=["boards"])
api_router.include_router(columns.router, prefix="/columns", tags=["columns"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])
api_router.include_router(workflows.router, tags=["workflows"])
api_router.include_router(activities.router, tags=["activities"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])

__all__ = ["api_router"]
