"""API endpoints for workflow operations."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.workflow_service import WorkflowService
from app.schemas.workflow import (
    WorkflowDefinitionCreate,
    WorkflowDefinitionUpdate,
    WorkflowDefinitionResponse,
    WorkflowDefinitionWithTransitionsResponse,
    WorkflowTransitionCreate,
    WorkflowTransitionUpdate,
    WorkflowTransitionResponse,
    AllowedTargetResponse,
    AllowedTransitionsResponse,
)

router = APIRouter()


# ============================================================================
# Workflow Definition Endpoints
# ============================================================================

@router.get(
    "/boards/{board_id}/workflows",
    response_model=List[WorkflowDefinitionWithTransitionsResponse],
)
async def get_board_workflows(
    board_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get all workflow definitions for a board.

    Args:
        board_id: Board UUID

    Returns:
        List of workflow definitions with transitions
    """
    workflows = await WorkflowService.get_workflows_for_board(db, board_id)
    return workflows


@router.get(
    "/boards/{board_id}/workflows/active",
    response_model=WorkflowDefinitionWithTransitionsResponse,
)
async def get_active_workflow(
    board_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get the active workflow definition for a board.

    Args:
        board_id: Board UUID

    Returns:
        Active workflow definition or 404 if none

    Raises:
        HTTPException: 404 if no active workflow
    """
    workflow = await WorkflowService.get_active_workflow(db, board_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active workflow found for this board",
        )
    return workflow


@router.post(
    "/boards/{board_id}/workflows",
    response_model=WorkflowDefinitionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_workflow(
    board_id: UUID,
    workflow_data: WorkflowDefinitionCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new workflow definition for a board.

    Args:
        board_id: Board UUID
        workflow_data: Workflow creation data

    Returns:
        Created workflow definition
    """
    workflow = await WorkflowService.create_workflow(db, board_id, workflow_data)
    return workflow


@router.get(
    "/workflows/{workflow_id}",
    response_model=WorkflowDefinitionWithTransitionsResponse,
)
async def get_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a workflow definition by ID.

    Args:
        workflow_id: Workflow UUID

    Returns:
        Workflow definition with transitions

    Raises:
        HTTPException: 404 if not found
    """
    workflow = await WorkflowService.get_workflow(db, workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found",
        )
    return workflow


@router.put(
    "/workflows/{workflow_id}",
    response_model=WorkflowDefinitionResponse,
)
async def update_workflow(
    workflow_id: UUID,
    workflow_data: WorkflowDefinitionUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a workflow definition.

    Args:
        workflow_id: Workflow UUID
        workflow_data: Workflow update data

    Returns:
        Updated workflow definition

    Raises:
        HTTPException: 404 if not found
    """
    workflow = await WorkflowService.update_workflow(db, workflow_id, workflow_data)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found",
        )
    return workflow


@router.delete(
    "/workflows/{workflow_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a workflow definition.

    Args:
        workflow_id: Workflow UUID

    Raises:
        HTTPException: 404 if not found
    """
    deleted = await WorkflowService.delete_workflow(db, workflow_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found",
        )


# ============================================================================
# Workflow Transition Endpoints
# ============================================================================

@router.get(
    "/workflows/{workflow_id}/transitions",
    response_model=List[WorkflowTransitionResponse],
)
async def get_workflow_transitions(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get all transitions for a workflow.

    Args:
        workflow_id: Workflow UUID

    Returns:
        List of transitions
    """
    transitions = await WorkflowService.get_transitions_for_workflow(db, workflow_id)
    return transitions


@router.post(
    "/workflows/{workflow_id}/transitions",
    response_model=WorkflowTransitionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_transition(
    workflow_id: UUID,
    transition_data: WorkflowTransitionCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new transition for a workflow.

    Args:
        workflow_id: Workflow UUID
        transition_data: Transition creation data

    Returns:
        Created transition

    Raises:
        HTTPException: 404 if workflow not found, 400 if columns invalid, 409 if duplicate
    """
    transition = await WorkflowService.create_transition(db, workflow_id, transition_data)
    return transition


@router.get(
    "/transitions/{transition_id}",
    response_model=WorkflowTransitionResponse,
)
async def get_transition(
    transition_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a transition by ID.

    Args:
        transition_id: Transition UUID

    Returns:
        Transition details

    Raises:
        HTTPException: 404 if not found
    """
    transition = await WorkflowService.get_transition(db, transition_id)
    if not transition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transition {transition_id} not found",
        )
    return transition


@router.put(
    "/transitions/{transition_id}",
    response_model=WorkflowTransitionResponse,
)
async def update_transition(
    transition_id: UUID,
    transition_data: WorkflowTransitionUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a transition.

    Args:
        transition_id: Transition UUID
        transition_data: Transition update data

    Returns:
        Updated transition

    Raises:
        HTTPException: 404 if not found
    """
    transition = await WorkflowService.update_transition(db, transition_id, transition_data)
    if not transition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transition {transition_id} not found",
        )
    return transition


@router.delete(
    "/transitions/{transition_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_transition(
    transition_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a transition.

    Args:
        transition_id: Transition UUID

    Raises:
        HTTPException: 404 if not found
    """
    deleted = await WorkflowService.delete_transition(db, transition_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transition {transition_id} not found",
        )


# ============================================================================
# Transition Validation Endpoints
# ============================================================================

@router.get(
    "/boards/{board_id}/columns/{column_id}/allowed-targets",
    response_model=List[AllowedTargetResponse],
)
async def get_allowed_targets(
    board_id: UUID,
    column_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get allowed target columns for moves from a specific column.

    Args:
        board_id: Board UUID
        column_id: Source column UUID

    Returns:
        List of allowed target columns
    """
    columns = await WorkflowService.get_allowed_targets(db, board_id, column_id)
    return [
        AllowedTargetResponse(column_id=c.id, column_name=c.name)
        for c in columns
    ]


@router.get(
    "/boards/{board_id}/allowed-transitions",
)
async def get_all_allowed_transitions(
    board_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get all allowed transitions for a board.

    Returns a dictionary mapping each column ID to its allowed target column IDs.

    Args:
        board_id: Board UUID

    Returns:
        Dictionary of column_id -> list of allowed target column_ids
    """
    return await WorkflowService.get_all_allowed_transitions_for_board(db, board_id)
