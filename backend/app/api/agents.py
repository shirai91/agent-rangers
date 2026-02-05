"""API endpoints for agent execution operations."""

import asyncio
import json
import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.agent_orchestrator import AgentOrchestrator
from app.schemas.agent import (
    StartAgentWorkflowRequest,
    AgentExecutionResponse,
    AgentOutputResponse,
    ExecutionStatusResponse,
    ClarifyRequest,
    ClarifyResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# Task Agent Execution Endpoints
# ============================================================================


@router.post(
    "/tasks/{task_id}/agent/start",
    response_model=AgentExecutionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_agent_workflow(
    task_id: UUID,
    request_data: StartAgentWorkflowRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Start an agent workflow for a task.

    Args:
        task_id: Task UUID
        request_data: Workflow configuration including type and context

    Returns:
        Created execution record

    Raises:
        HTTPException: 404 if task not found, 400 if validation fails
    """
    # Fetch the task to get board_id
    from app.models.task import Task

    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    # Validate workflow type
    valid_workflows = ["development", "quick_development", "architecture_only", "review_only"]
    if request_data.workflow_type not in valid_workflows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid workflow_type. Must be one of: {', '.join(valid_workflows)}",
        )

    # Build context with plan_execution_id if provided
    context = request_data.context or {}
    if request_data.plan_execution_id:
        context["plan_execution_id"] = str(request_data.plan_execution_id)
    
    # Create execution
    execution = await AgentOrchestrator.create_execution(
        db=db,
        task_id=task_id,
        board_id=task.board_id,
        workflow_type=request_data.workflow_type,
        context=context,
    )
    await db.commit()
    await db.refresh(execution)

    # Start execution in background
    asyncio.create_task(_run_workflow_background(execution.id))

    return execution


async def _run_workflow_background(execution_id: UUID):
    """
    Run workflow in background task.

    Args:
        execution_id: Execution UUID
    """
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            execution = await AgentOrchestrator._get_execution(db, execution_id)
            if not execution:
                logger.error(f"Execution {execution_id} not found for background task")
                return

            await AgentOrchestrator.start_execution(db, execution_id)
            await db.commit()

            await AgentOrchestrator.run_workflow(db, execution)
            await db.commit()

        except Exception as e:
            logger.error(f"Background workflow execution failed: {e}", exc_info=True)
            await db.rollback()


# ============================================================================
# Execution Query Endpoints
# ============================================================================


@router.get("/executions/{execution_id}", response_model=AgentExecutionResponse)
async def get_execution(
    execution_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get execution details with all outputs.

    Args:
        execution_id: Execution UUID

    Returns:
        Full execution details with outputs

    Raises:
        HTTPException: 404 if execution not found
    """
    execution = await AgentOrchestrator._get_execution(db, execution_id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution {execution_id} not found",
        )

    return execution


@router.get(
    "/executions/{execution_id}/status",
    response_model=ExecutionStatusResponse,
)
async def get_execution_status(
    execution_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get current execution status (lightweight).

    Args:
        execution_id: Execution UUID

    Returns:
        Current status with lightweight output info

    Raises:
        HTTPException: 404 if execution not found
    """
    status_dict = await AgentOrchestrator.get_execution_status(db, execution_id)
    if not status_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution {execution_id} not found",
        )

    # Convert to response model
    return ExecutionStatusResponse(**status_dict)


@router.delete("/executions/{execution_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_execution(
    execution_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel a running execution.

    Args:
        execution_id: Execution UUID

    Raises:
        HTTPException: 404 if not found, 400 if cannot be cancelled
    """
    try:
        await AgentOrchestrator.cancel_execution(db, execution_id)
        await db.commit()
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )


@router.get(
    "/tasks/{task_id}/executions",
    response_model=List[AgentExecutionResponse],
)
async def get_task_executions(
    task_id: UUID,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """
    Get execution history for a task.

    Args:
        task_id: Task UUID
        limit: Maximum number of executions to return (default: 10)

    Returns:
        List of executions ordered by most recent
    """
    executions = await AgentOrchestrator.get_task_executions(
        db, task_id, limit=limit
    )
    
    # Sanitize response to prevent huge payloads
    for execution in executions:
        # Truncate files_affected in result_summary
        if execution.result_summary and 'files_affected' in execution.result_summary:
            files = execution.result_summary['files_affected']
            if isinstance(files, list) and len(files) > 50:
                execution.result_summary['files_affected'] = files[:50] + [f'... and {len(files) - 50} more files']
        # Truncate output content (keep metadata but limit content size)
        for output in execution.outputs:
            if output.output_content and len(output.output_content) > 5000:
                output.output_content = output.output_content[:5000] + '\n\n... [truncated]'
            # Limit files_created
            if output.files_created and len(output.files_created) > 50:
                output.files_created = output.files_created[:50]
    
    return executions


@router.post(
    "/tasks/{task_id}/clarify",
    response_model=ClarifyResponse,
)
async def submit_clarification(
    task_id: UUID,
    request_data: ClarifyRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit clarification answers and resume the planning phase.

    Args:
        task_id: Task UUID
        request_data: Clarification answers

    Returns:
        New execution details

    Raises:
        HTTPException: 404 if task not found, 400 if no pending clarification
    """
    from app.models.task import Task
    from app.models.agent_execution import AgentExecution
    from sqlalchemy import select

    # Validate task exists
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    # Find the execution awaiting clarification
    result = await db.execute(
        select(AgentExecution)
        .where(
            AgentExecution.task_id == task_id,
            AgentExecution.status == "awaiting_clarification",
        )
        .order_by(AgentExecution.created_at.desc())
        .limit(1)
    )
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No execution awaiting clarification for this task",
        )

    # Resume execution with clarification answers
    try:
        new_execution = await AgentOrchestrator.resume_with_clarification(
            db, execution.id, request_data.answers
        )
        await db.commit()

        # Start the new execution in background
        asyncio.create_task(_run_workflow_background(new_execution.id))

        return ClarifyResponse(
            execution_id=new_execution.id,
            task_id=task_id,
            status=new_execution.status,
            message="Planning resumed with clarification answers",
        )
    except Exception as e:
        logger.error(f"Failed to resume with clarification: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/tasks/{task_id}/plans",
)
async def get_task_plans(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get available plans (completed architecture_only executions) for a task.

    Args:
        task_id: Task UUID

    Returns:
        List of available plans that can be selected for development
    """
    from sqlalchemy import select
    from app.models.agent_execution import AgentExecution
    from app.models.agent_output import AgentOutput
    from app.models.task import Task
    
    # Get task title
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )
    
    # Get completed architecture_only executions
    result = await db.execute(
        select(AgentExecution)
        .where(
            AgentExecution.task_id == task_id,
            AgentExecution.workflow_type == "architecture_only",
            AgentExecution.status == "completed",
        )
        .order_by(AgentExecution.created_at.desc())
    )
    executions = result.scalars().all()
    
    plans = []
    for execution in executions:
        # Get the architecture output for this execution
        output_result = await db.execute(
            select(AgentOutput)
            .where(
                AgentOutput.execution_id == execution.id,
                AgentOutput.phase == "architecture",
                AgentOutput.status == "completed",
            )
        )
        output = output_result.scalar_one_or_none()
        
        if output and output.output_content:
            # Extract plan filename from files_created
            plan_filename = None
            if output.files_created:
                for f in output.files_created:
                    if isinstance(f, str) and f.endswith('.md'):
                        plan_filename = f.split('/')[-1]
                        break
            
            plans.append({
                "execution_id": str(execution.id),
                "created_at": execution.created_at.isoformat(),
                "plan_filename": plan_filename,
                "plan_preview": output.output_content[:200] + "..." if len(output.output_content) > 200 else output.output_content,
                "task_title": task.title,
            })
    
    return plans


@router.get(
    "/boards/{board_id}/executions",
    response_model=List[AgentExecutionResponse],
)
async def get_board_executions(
    board_id: UUID,
    status_filter: Optional[str] = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """
    Get executions for a board with optional status filter.

    Args:
        board_id: Board UUID
        status_filter: Optional status to filter by (pending, running, completed, failed, cancelled)
        limit: Maximum number of executions to return (default: 20)

    Returns:
        List of executions ordered by most recent
    """
    # Validate status filter if provided
    if status_filter:
        valid_statuses = ["pending", "running", "completed", "failed", "cancelled"]
        if status_filter not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status_filter. Must be one of: {', '.join(valid_statuses)}",
            )

    executions = await AgentOrchestrator.get_board_executions(
        db, board_id, status=status_filter, limit=limit
    )
    return executions


# ============================================================================
# Streaming Endpoint (SSE)
# ============================================================================


@router.get("/executions/{execution_id}/stream")
async def stream_execution_output(
    execution_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Stream agent output in real-time using Server-Sent Events.

    Args:
        execution_id: Execution UUID
        request: FastAPI request (for disconnect detection)

    Returns:
        StreamingResponse with text/event-stream

    Raises:
        HTTPException: 404 if execution not found
    """
    # Verify execution exists
    execution = await AgentOrchestrator._get_execution(db, execution_id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution {execution_id} not found",
        )

    async def event_generator():
        """
        Generate Server-Sent Events for execution progress.

        Yields SSE-formatted messages with execution updates.
        """
        from sqlalchemy import select
        from app.models.agent_execution import AgentExecution
        from app.models.agent_output import AgentOutput

        # Send initial status
        yield f"data: {json.dumps({'type': 'status', 'status': execution.status, 'phase': execution.current_phase})}\n\n"

        last_output_count = 0

        # Poll for updates while execution is running
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                logger.info(f"Client disconnected from stream for execution {execution_id}")
                break

            # Fetch current execution state
            async with AsyncSessionLocal() as stream_db:
                result = await stream_db.execute(
                    select(AgentExecution).where(AgentExecution.id == execution_id)
                )
                current_execution = result.scalar_one_or_none()

                if not current_execution:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Execution not found'})}\n\n"
                    break

                # Send status update
                status_update = {
                    "type": "status",
                    "status": current_execution.status,
                    "phase": current_execution.current_phase,
                    "iteration": current_execution.iteration,
                }
                yield f"data: {json.dumps(status_update)}\n\n"

                # Fetch new outputs
                outputs_result = await stream_db.execute(
                    select(AgentOutput)
                    .where(AgentOutput.execution_id == execution_id)
                    .order_by(AgentOutput.created_at)
                )
                outputs = list(outputs_result.scalars().all())

                # Send new outputs
                if len(outputs) > last_output_count:
                    for output in outputs[last_output_count:]:
                        output_data = {
                            "type": "output",
                            "output_id": str(output.id),
                            "agent_name": output.agent_name,
                            "phase": output.phase,
                            "status": output.status,
                            "content": output.output_content,
                            "structured": output.output_structured,
                        }
                        yield f"data: {json.dumps(output_data)}\n\n"
                    last_output_count = len(outputs)

                # Check if execution is complete
                if current_execution.status in ["completed", "failed", "cancelled"]:
                    completion_data = {
                        "type": "complete",
                        "status": current_execution.status,
                        "error_message": current_execution.error_message,
                        "result_summary": current_execution.result_summary,
                    }
                    yield f"data: {json.dumps(completion_data)}\n\n"
                    break

            # Wait before next poll
            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


# Import SessionLocal for background tasks and streaming
from app.database import AsyncSessionLocal


# ============================================================================
# Workspace File Access Endpoints
# ============================================================================


@router.get("/workspaces/{task_id}/files")
async def list_workspace_files(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    List all files in a task's workspace.

    Args:
        task_id: Task UUID

    Returns:
        List of file paths in the workspace
    """
    import os
    
    workspace_path = f"/tmp/workspaces/{task_id}"
    
    if not os.path.exists(workspace_path):
        return {"files": [], "workspace_path": workspace_path, "exists": False}
    
    files = []
    for root, dirs, filenames in os.walk(workspace_path):
        for filename in filenames:
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, workspace_path)
            stat = os.stat(full_path)
            files.append({
                "name": filename,
                "path": rel_path,
                "size": stat.st_size,
                "modified": stat.st_mtime,
            })
    
    return {
        "files": files,
        "workspace_path": workspace_path,
        "exists": True,
        "file_count": len(files),
    }


@router.get("/workspaces/{task_id}/files/{file_path:path}")
async def get_workspace_file(
    task_id: UUID,
    file_path: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get content of a specific file from the workspace.

    Args:
        task_id: Task UUID
        file_path: Relative path to the file within workspace

    Returns:
        File content with metadata

    Raises:
        HTTPException: 404 if file not found
    """
    import os
    from fastapi.responses import FileResponse, Response
    
    workspace_path = f"/tmp/workspaces/{task_id}"
    full_path = os.path.join(workspace_path, file_path)
    
    # Security: Ensure the path doesn't escape the workspace
    real_workspace = os.path.realpath(workspace_path)
    real_file = os.path.realpath(full_path)
    if not real_file.startswith(real_workspace):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied - path traversal detected",
        )
    
    if not os.path.exists(full_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {file_path}",
        )
    
    if not os.path.isfile(full_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Path is not a file: {file_path}",
        )
    
    # Determine content type
    extension = os.path.splitext(file_path)[1].lower()
    content_types = {
        ".md": "text/markdown",
        ".txt": "text/plain",
        ".py": "text/x-python",
        ".js": "text/javascript",
        ".ts": "text/typescript",
        ".json": "application/json",
        ".html": "text/html",
        ".css": "text/css",
        ".yaml": "text/yaml",
        ".yml": "text/yaml",
        ".xml": "application/xml",
        ".sh": "text/x-shellscript",
        ".sql": "text/x-sql",
    }
    content_type = content_types.get(extension, "text/plain")
    
    # Read file content
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        # Binary file - return as download
        return FileResponse(
            full_path,
            filename=os.path.basename(file_path),
        )
    
    stat = os.stat(full_path)
    
    return {
        "name": os.path.basename(file_path),
        "path": file_path,
        "content": content,
        "content_type": content_type,
        "size": stat.st_size,
        "modified": stat.st_mtime,
    }


@router.get("/workspaces/{task_id}/raw/{file_path:path}")
async def get_workspace_file_raw(
    task_id: UUID,
    file_path: str,
):
    """
    Get raw file content for direct viewing/downloading in browser.

    Args:
        task_id: Task UUID
        file_path: Relative path to the file within workspace

    Returns:
        Raw file content with appropriate content type for browser display

    Raises:
        HTTPException: 404 if file not found
    """
    import os
    from fastapi.responses import FileResponse, Response
    
    workspace_path = f"/tmp/workspaces/{task_id}"
    full_path = os.path.join(workspace_path, file_path)
    
    # Security: Ensure the path doesn't escape the workspace
    real_workspace = os.path.realpath(workspace_path)
    real_file = os.path.realpath(full_path)
    if not real_file.startswith(real_workspace):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied - path traversal detected",
        )
    
    if not os.path.exists(full_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {file_path}",
        )
    
    # Determine content type for inline display
    extension = os.path.splitext(file_path)[1].lower()
    content_types = {
        ".md": "text/markdown; charset=utf-8",
        ".txt": "text/plain; charset=utf-8",
        ".py": "text/plain; charset=utf-8",
        ".js": "text/plain; charset=utf-8",
        ".ts": "text/plain; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".html": "text/html; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".yaml": "text/plain; charset=utf-8",
        ".yml": "text/plain; charset=utf-8",
    }
    content_type = content_types.get(extension, "text/plain; charset=utf-8")
    
    # Read and return file
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        return Response(
            content=content,
            media_type=content_type,
            headers={
                "Content-Disposition": f'inline; filename="{os.path.basename(file_path)}"',
            },
        )
    except UnicodeDecodeError:
        # Binary file
        return FileResponse(full_path, filename=os.path.basename(file_path))


# ============================================================================
# Absolute File Path Endpoints (for project files outside workspaces)
# ============================================================================

# Allowed base paths for file reading (security)
ALLOWED_FILE_PATHS = [
    "/home/shirai91/projects/",
    "/tmp/workspaces/",
]


def is_path_allowed(file_path: str) -> bool:
    """Check if the file path is within allowed directories."""
    import os
    abs_path = os.path.abspath(file_path)
    return any(abs_path.startswith(allowed) for allowed in ALLOWED_FILE_PATHS)


@router.get("/files/read")
async def read_file_by_path(path: str):
    """
    Read a file from an absolute path.
    
    Limited to allowed directories for security.
    
    Args:
        path: Absolute file path
        
    Returns:
        File content as JSON
    """
    import os
    
    if not is_path_allowed(path):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="File path not in allowed directories",
        )
    
    if not os.path.exists(path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {path}",
        )
    
    if not os.path.isfile(path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path is not a file",
        )
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"path": path, "content": content}
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is not a text file",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read file: {str(e)}",
        )


@router.get("/files/raw")
async def get_raw_file_by_path(path: str):
    """
    Get raw file content for direct viewing in browser.
    
    Limited to allowed directories for security.
    
    Args:
        path: Absolute file path
        
    Returns:
        Raw file content with appropriate content type
    """
    import os
    from fastapi.responses import Response, FileResponse
    
    if not is_path_allowed(path):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="File path not in allowed directories",
        )
    
    if not os.path.exists(path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {path}",
        )
    
    if not os.path.isfile(path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path is not a file",
        )
    
    # Determine content type
    extension = os.path.splitext(path)[1].lower()
    content_types = {
        ".md": "text/markdown; charset=utf-8",
        ".txt": "text/plain; charset=utf-8",
        ".py": "text/plain; charset=utf-8",
        ".js": "text/plain; charset=utf-8",
        ".ts": "text/plain; charset=utf-8",
        ".tsx": "text/plain; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".html": "text/html; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".yaml": "text/plain; charset=utf-8",
        ".yml": "text/plain; charset=utf-8",
    }
    content_type = content_types.get(extension, "text/plain; charset=utf-8")
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return Response(
            content=content,
            media_type=content_type,
            headers={
                "Content-Disposition": f'inline; filename="{os.path.basename(path)}"',
            },
        )
    except UnicodeDecodeError:
        return FileResponse(path, filename=os.path.basename(path))
