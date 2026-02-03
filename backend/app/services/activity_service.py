"""Business logic for task activity operations."""

from typing import Optional, List, Any
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.task import Task
from app.models.task_activity import TaskActivity
from app.models.column import Column


class ActivityService:
    """Service for handling task activity logging and retrieval."""

    # ========================================================================
    # Activity Logging
    # ========================================================================

    @staticmethod
    async def log_activity(
        db: AsyncSession,
        task_id: UUID,
        board_id: UUID,
        activity_type: str,
        actor: str = "system",
        from_column_id: Optional[UUID] = None,
        to_column_id: Optional[UUID] = None,
        old_value: Optional[dict] = None,
        new_value: Optional[dict] = None,
        metadata: Optional[dict] = None,
    ) -> TaskActivity:
        """
        Log a task activity.

        Args:
            db: Database session
            task_id: Task UUID
            board_id: Board UUID
            activity_type: Type of activity (created, updated, moved, etc.)
            actor: Who performed the action
            from_column_id: Source column for move activities
            to_column_id: Target column for move activities
            old_value: Previous value(s) before change
            new_value: New value(s) after change
            metadata: Additional activity metadata

        Returns:
            Created activity
        """
        activity = TaskActivity(
            task_id=task_id,
            board_id=board_id,
            activity_type=activity_type,
            actor=actor,
            from_column_id=from_column_id,
            to_column_id=to_column_id,
            old_value=old_value,
            new_value=new_value,
            activity_metadata=metadata or {},
        )
        db.add(activity)
        await db.flush()
        await db.refresh(activity)
        return activity

    @staticmethod
    async def log_task_created(
        db: AsyncSession,
        task: Task,
        actor: str = "system",
    ) -> TaskActivity:
        """
        Log task creation activity.

        Args:
            db: Database session
            task: Created task
            actor: Who created the task

        Returns:
            Created activity
        """
        return await ActivityService.log_activity(
            db=db,
            task_id=task.id,
            board_id=task.board_id,
            activity_type="created",
            actor=actor,
            to_column_id=task.column_id,
            new_value={
                "title": task.title,
                "description": task.description,
                "priority": task.priority,
            },
        )

    @staticmethod
    async def log_task_updated(
        db: AsyncSession,
        task: Task,
        changes: dict[str, Any],
        actor: str = "system",
    ) -> Optional[TaskActivity]:
        """
        Log task update activity.

        Args:
            db: Database session
            task: Updated task
            changes: Dictionary of changed fields with old and new values
            actor: Who updated the task

        Returns:
            Created activity or None if no changes
        """
        if not changes:
            return None

        old_value = {k: v["old"] for k, v in changes.items()}
        new_value = {k: v["new"] for k, v in changes.items()}

        return await ActivityService.log_activity(
            db=db,
            task_id=task.id,
            board_id=task.board_id,
            activity_type="updated",
            actor=actor,
            old_value=old_value,
            new_value=new_value,
        )

    @staticmethod
    async def log_task_moved(
        db: AsyncSession,
        task: Task,
        from_column_id: UUID,
        to_column_id: UUID,
        actor: str = "system",
    ) -> TaskActivity:
        """
        Log task move activity.

        Args:
            db: Database session
            task: Moved task
            from_column_id: Source column UUID
            to_column_id: Target column UUID
            actor: Who moved the task

        Returns:
            Created activity
        """
        return await ActivityService.log_activity(
            db=db,
            task_id=task.id,
            board_id=task.board_id,
            activity_type="moved",
            actor=actor,
            from_column_id=from_column_id,
            to_column_id=to_column_id,
        )

    @staticmethod
    async def log_task_deleted(
        db: AsyncSession,
        task: Task,
        actor: str = "system",
    ) -> TaskActivity:
        """
        Log task deletion activity.

        Args:
            db: Database session
            task: Task to be deleted
            actor: Who deleted the task

        Returns:
            Created activity
        """
        return await ActivityService.log_activity(
            db=db,
            task_id=task.id,
            board_id=task.board_id,
            activity_type="deleted",
            actor=actor,
            old_value={
                "title": task.title,
                "column_id": str(task.column_id) if task.column_id else None,
            },
        )

    # ========================================================================
    # Activity Retrieval
    # ========================================================================

    @staticmethod
    async def get_task_activities(
        db: AsyncSession,
        task_id: UUID,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[List[TaskActivity], int]:
        """
        Get activities for a specific task with pagination.

        Args:
            db: Database session
            task_id: Task UUID
            page: Page number (1-based)
            page_size: Number of items per page

        Returns:
            Tuple of (activities, total_count)
        """
        # Get total count
        count_result = await db.execute(
            select(func.count(TaskActivity.id)).where(TaskActivity.task_id == task_id)
        )
        total = count_result.scalar() or 0

        # Get activities with pagination
        offset = (page - 1) * page_size
        result = await db.execute(
            select(TaskActivity)
            .where(TaskActivity.task_id == task_id)
            .order_by(TaskActivity.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        activities = list(result.scalars().all())

        # Enrich with column names
        activities = await ActivityService._enrich_with_column_names(db, activities)

        return activities, total

    @staticmethod
    async def get_board_activities(
        db: AsyncSession,
        board_id: UUID,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[List[TaskActivity], int]:
        """
        Get activities for a specific board with pagination.

        Args:
            db: Database session
            board_id: Board UUID
            page: Page number (1-based)
            page_size: Number of items per page

        Returns:
            Tuple of (activities, total_count)
        """
        # Get total count
        count_result = await db.execute(
            select(func.count(TaskActivity.id)).where(TaskActivity.board_id == board_id)
        )
        total = count_result.scalar() or 0

        # Get activities with pagination
        offset = (page - 1) * page_size
        result = await db.execute(
            select(TaskActivity)
            .options(selectinload(TaskActivity.task))
            .where(TaskActivity.board_id == board_id)
            .order_by(TaskActivity.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        activities = list(result.scalars().all())

        # Enrich with column names and task titles
        activities = await ActivityService._enrich_with_column_names(db, activities)

        return activities, total

    @staticmethod
    async def get_recent_board_activities(
        db: AsyncSession,
        board_id: UUID,
        limit: int = 20,
    ) -> List[TaskActivity]:
        """
        Get recent activities for a board.

        Args:
            db: Database session
            board_id: Board UUID
            limit: Maximum number of activities to return

        Returns:
            List of recent activities
        """
        result = await db.execute(
            select(TaskActivity)
            .options(selectinload(TaskActivity.task))
            .where(TaskActivity.board_id == board_id)
            .order_by(TaskActivity.created_at.desc())
            .limit(limit)
        )
        activities = list(result.scalars().all())

        # Enrich with column names
        activities = await ActivityService._enrich_with_column_names(db, activities)

        return activities

    @staticmethod
    async def _enrich_with_column_names(
        db: AsyncSession,
        activities: List[TaskActivity],
    ) -> List[TaskActivity]:
        """
        Enrich activities with column names for display.

        Args:
            db: Database session
            activities: List of activities

        Returns:
            Enriched activities
        """
        # Collect all column IDs
        column_ids = set()
        for activity in activities:
            if activity.from_column_id:
                column_ids.add(activity.from_column_id)
            if activity.to_column_id:
                column_ids.add(activity.to_column_id)

        if not column_ids:
            return activities

        # Fetch column names
        result = await db.execute(
            select(Column).where(Column.id.in_(column_ids))
        )
        columns = {c.id: c.name for c in result.scalars().all()}

        # Add names to activities (as non-persistent attributes)
        for activity in activities:
            # Store as dynamic attributes (won't be saved to DB)
            object.__setattr__(
                activity,
                "_from_column_name",
                columns.get(activity.from_column_id) if activity.from_column_id else None,
            )
            object.__setattr__(
                activity,
                "_to_column_name",
                columns.get(activity.to_column_id) if activity.to_column_id else None,
            )

        return activities
