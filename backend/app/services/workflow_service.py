"""Business logic for workflow operations."""

from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.workflow_definition import WorkflowDefinition
from app.models.workflow_transition import WorkflowTransition
from app.models.column import Column
from app.schemas.workflow import (
    WorkflowDefinitionCreate,
    WorkflowDefinitionUpdate,
    WorkflowTransitionCreate,
    WorkflowTransitionUpdate,
)


class WorkflowService:
    """Service for handling workflow definition and transition operations."""

    # ========================================================================
    # Workflow Definition Operations
    # ========================================================================

    @staticmethod
    async def get_workflow(
        db: AsyncSession, workflow_id: UUID
    ) -> Optional[WorkflowDefinition]:
        """
        Get a workflow definition by ID with transitions.

        Args:
            db: Database session
            workflow_id: Workflow UUID

        Returns:
            WorkflowDefinition or None if not found
        """
        result = await db.execute(
            select(WorkflowDefinition)
            .options(selectinload(WorkflowDefinition.transitions))
            .where(WorkflowDefinition.id == workflow_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_workflows_for_board(
        db: AsyncSession, board_id: UUID
    ) -> List[WorkflowDefinition]:
        """
        Get all workflow definitions for a board.

        Args:
            db: Database session
            board_id: Board UUID

        Returns:
            List of workflow definitions
        """
        result = await db.execute(
            select(WorkflowDefinition)
            .options(selectinload(WorkflowDefinition.transitions))
            .where(WorkflowDefinition.board_id == board_id)
            .order_by(WorkflowDefinition.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_active_workflow(
        db: AsyncSession, board_id: UUID
    ) -> Optional[WorkflowDefinition]:
        """
        Get the active workflow definition for a board.

        Args:
            db: Database session
            board_id: Board UUID

        Returns:
            Active WorkflowDefinition or None
        """
        result = await db.execute(
            select(WorkflowDefinition)
            .options(selectinload(WorkflowDefinition.transitions))
            .where(
                and_(
                    WorkflowDefinition.board_id == board_id,
                    WorkflowDefinition.is_active == True,
                )
            )
            .order_by(WorkflowDefinition.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_workflow(
        db: AsyncSession, board_id: UUID, workflow_data: WorkflowDefinitionCreate
    ) -> WorkflowDefinition:
        """
        Create a new workflow definition for a board.

        Args:
            db: Database session
            board_id: Board UUID
            workflow_data: Workflow creation data

        Returns:
            Created workflow definition
        """
        workflow = WorkflowDefinition(
            board_id=board_id,
            **workflow_data.model_dump(),
        )
        db.add(workflow)
        await db.flush()
        await db.refresh(workflow)
        return workflow

    @staticmethod
    async def update_workflow(
        db: AsyncSession, workflow_id: UUID, workflow_data: WorkflowDefinitionUpdate
    ) -> Optional[WorkflowDefinition]:
        """
        Update a workflow definition.

        Args:
            db: Database session
            workflow_id: Workflow UUID
            workflow_data: Workflow update data

        Returns:
            Updated workflow definition or None if not found
        """
        workflow = await WorkflowService.get_workflow(db, workflow_id)
        if not workflow:
            return None

        update_dict = workflow_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(workflow, key, value)

        await db.flush()
        await db.refresh(workflow)
        return workflow

    @staticmethod
    async def delete_workflow(db: AsyncSession, workflow_id: UUID) -> bool:
        """
        Delete a workflow definition.

        Args:
            db: Database session
            workflow_id: Workflow UUID

        Returns:
            True if deleted, False if not found
        """
        workflow = await WorkflowService.get_workflow(db, workflow_id)
        if not workflow:
            return False

        await db.delete(workflow)
        await db.flush()
        return True

    # ========================================================================
    # Workflow Transition Operations
    # ========================================================================

    @staticmethod
    async def get_transition(
        db: AsyncSession, transition_id: UUID
    ) -> Optional[WorkflowTransition]:
        """
        Get a workflow transition by ID.

        Args:
            db: Database session
            transition_id: Transition UUID

        Returns:
            WorkflowTransition or None if not found
        """
        result = await db.execute(
            select(WorkflowTransition).where(WorkflowTransition.id == transition_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_transitions_for_workflow(
        db: AsyncSession, workflow_id: UUID
    ) -> List[WorkflowTransition]:
        """
        Get all transitions for a workflow.

        Args:
            db: Database session
            workflow_id: Workflow UUID

        Returns:
            List of transitions
        """
        result = await db.execute(
            select(WorkflowTransition)
            .where(WorkflowTransition.workflow_id == workflow_id)
            .order_by(WorkflowTransition.created_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_transition(
        db: AsyncSession, workflow_id: UUID, transition_data: WorkflowTransitionCreate
    ) -> WorkflowTransition:
        """
        Create a new transition for a workflow.

        Args:
            db: Database session
            workflow_id: Workflow UUID
            transition_data: Transition creation data

        Returns:
            Created transition

        Raises:
            HTTPException: If workflow not found or columns invalid
        """
        # Verify workflow exists
        workflow = await WorkflowService.get_workflow(db, workflow_id)
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found",
            )

        # Verify columns exist and belong to the same board
        from_column = await db.execute(
            select(Column).where(
                and_(
                    Column.id == transition_data.from_column_id,
                    Column.board_id == workflow.board_id,
                )
            )
        )
        if not from_column.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Source column {transition_data.from_column_id} not found in board",
            )

        to_column = await db.execute(
            select(Column).where(
                and_(
                    Column.id == transition_data.to_column_id,
                    Column.board_id == workflow.board_id,
                )
            )
        )
        if not to_column.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Target column {transition_data.to_column_id} not found in board",
            )

        # Check for duplicate transition
        existing = await db.execute(
            select(WorkflowTransition).where(
                and_(
                    WorkflowTransition.workflow_id == workflow_id,
                    WorkflowTransition.from_column_id == transition_data.from_column_id,
                    WorkflowTransition.to_column_id == transition_data.to_column_id,
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This transition already exists",
            )

        transition = WorkflowTransition(
            workflow_id=workflow_id,
            **transition_data.model_dump(),
        )
        db.add(transition)
        await db.flush()
        await db.refresh(transition)
        return transition

    @staticmethod
    async def update_transition(
        db: AsyncSession, transition_id: UUID, transition_data: WorkflowTransitionUpdate
    ) -> Optional[WorkflowTransition]:
        """
        Update a workflow transition.

        Args:
            db: Database session
            transition_id: Transition UUID
            transition_data: Transition update data

        Returns:
            Updated transition or None if not found
        """
        transition = await WorkflowService.get_transition(db, transition_id)
        if not transition:
            return None

        update_dict = transition_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(transition, key, value)

        await db.flush()
        await db.refresh(transition)
        return transition

    @staticmethod
    async def delete_transition(db: AsyncSession, transition_id: UUID) -> bool:
        """
        Delete a workflow transition.

        Args:
            db: Database session
            transition_id: Transition UUID

        Returns:
            True if deleted, False if not found
        """
        transition = await WorkflowService.get_transition(db, transition_id)
        if not transition:
            return False

        await db.delete(transition)
        await db.flush()
        return True

    # ========================================================================
    # Validation Operations
    # ========================================================================

    @staticmethod
    async def get_allowed_targets(
        db: AsyncSession, board_id: UUID, from_column_id: UUID
    ) -> List[Column]:
        """
        Get allowed target columns for a move from a specific column.

        If no active workflow exists, all columns are allowed.
        If a workflow exists, only transitions defined in it are allowed.

        Args:
            db: Database session
            board_id: Board UUID
            from_column_id: Source column UUID

        Returns:
            List of allowed target columns
        """
        # Get active workflow
        workflow = await WorkflowService.get_active_workflow(db, board_id)

        if not workflow:
            # No workflow - all columns allowed
            result = await db.execute(
                select(Column)
                .where(Column.board_id == board_id)
                .order_by(Column.order)
            )
            return list(result.scalars().all())

        # Get allowed transitions from this column
        result = await db.execute(
            select(WorkflowTransition)
            .where(
                and_(
                    WorkflowTransition.workflow_id == workflow.id,
                    WorkflowTransition.from_column_id == from_column_id,
                    WorkflowTransition.is_enabled == True,
                )
            )
        )
        transitions = list(result.scalars().all())

        # Get target columns
        target_column_ids = [t.to_column_id for t in transitions]
        if not target_column_ids:
            return []

        result = await db.execute(
            select(Column)
            .where(Column.id.in_(target_column_ids))
            .order_by(Column.order)
        )
        return list(result.scalars().all())

    @staticmethod
    async def validate_transition(
        db: AsyncSession,
        board_id: UUID,
        from_column_id: UUID,
        to_column_id: UUID,
    ) -> bool:
        """
        Validate if a transition from one column to another is allowed.

        Args:
            db: Database session
            board_id: Board UUID
            from_column_id: Source column UUID
            to_column_id: Target column UUID

        Returns:
            True if transition is allowed, False otherwise
        """
        # Same column - always allowed
        if from_column_id == to_column_id:
            return True

        # Get active workflow
        workflow = await WorkflowService.get_active_workflow(db, board_id)

        if not workflow:
            # No workflow - all transitions allowed
            return True

        # Check if transition exists and is enabled
        result = await db.execute(
            select(WorkflowTransition).where(
                and_(
                    WorkflowTransition.workflow_id == workflow.id,
                    WorkflowTransition.from_column_id == from_column_id,
                    WorkflowTransition.to_column_id == to_column_id,
                    WorkflowTransition.is_enabled == True,
                )
            )
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def get_all_allowed_transitions_for_board(
        db: AsyncSession, board_id: UUID
    ) -> dict[str, List[str]]:
        """
        Get all allowed transitions for a board as a dictionary.

        Args:
            db: Database session
            board_id: Board UUID

        Returns:
            Dictionary mapping from_column_id to list of allowed to_column_ids
        """
        # Get active workflow
        workflow = await WorkflowService.get_active_workflow(db, board_id)

        # Get all columns
        result = await db.execute(
            select(Column)
            .where(Column.board_id == board_id)
            .order_by(Column.order)
        )
        columns = list(result.scalars().all())
        column_ids = [str(c.id) for c in columns]

        if not workflow:
            # No workflow - all columns allowed from any column
            return {cid: column_ids for cid in column_ids}

        # Build transition map from workflow
        result = await db.execute(
            select(WorkflowTransition)
            .where(
                and_(
                    WorkflowTransition.workflow_id == workflow.id,
                    WorkflowTransition.is_enabled == True,
                )
            )
        )
        transitions = list(result.scalars().all())

        transition_map: dict[str, List[str]] = {cid: [] for cid in column_ids}
        for t in transitions:
            from_id = str(t.from_column_id)
            to_id = str(t.to_column_id)
            if from_id in transition_map:
                transition_map[from_id].append(to_id)

        return transition_map
