"""Business logic for board, column, and task operations."""

from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.board import Board
from app.models.column import Column
from app.models.task import Task
from app.schemas.board import BoardCreate, BoardUpdate
from app.schemas.column import ColumnCreate, ColumnUpdate
from app.schemas.task import TaskCreate, TaskUpdate, TaskMove
from app.services.workflow_service import WorkflowService
from app.services.activity_service import ActivityService


class BoardService:
    """Service for handling board, column, and task operations."""

    @staticmethod
    async def get_boards(db: AsyncSession) -> List[Board]:
        """
        Get all boards without columns (for list view).

        Args:
            db: Database session

        Returns:
            List of boards
        """
        result = await db.execute(select(Board).order_by(Board.created_at.desc()))
        return list(result.scalars().all())

    @staticmethod
    async def get_board(db: AsyncSession, board_id: UUID) -> Optional[Board]:
        """
        Get a board by ID with all columns.

        Args:
            db: Database session
            board_id: Board UUID

        Returns:
            Board or None if not found
        """
        result = await db.execute(
            select(Board)
            .options(selectinload(Board.columns))
            .where(Board.id == board_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_board(db: AsyncSession, board_data: BoardCreate) -> Board:
        """
        Create a new board.

        Args:
            db: Database session
            board_data: Board creation data

        Returns:
            Created board
        """
        board = Board(**board_data.model_dump())
        db.add(board)
        await db.flush()
        await db.refresh(board)
        return board

    @staticmethod
    async def update_board(
        db: AsyncSession, board_id: UUID, board_data: BoardUpdate
    ) -> Optional[Board]:
        """
        Update a board.

        Args:
            db: Database session
            board_id: Board UUID
            board_data: Board update data

        Returns:
            Updated board or None if not found
        """
        board = await BoardService.get_board(db, board_id)
        if not board:
            return None

        update_dict = board_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(board, key, value)

        await db.flush()
        await db.refresh(board)
        return board

    @staticmethod
    async def delete_board(db: AsyncSession, board_id: UUID) -> bool:
        """
        Delete a board.

        Args:
            db: Database session
            board_id: Board UUID

        Returns:
            True if deleted, False if not found
        """
        board = await BoardService.get_board(db, board_id)
        if not board:
            return False

        await db.delete(board)
        await db.flush()
        return True

    @staticmethod
    async def get_columns(db: AsyncSession, board_id: UUID) -> List[Column]:
        """
        Get all columns for a board.

        Args:
            db: Database session
            board_id: Board UUID

        Returns:
            List of columns ordered by position
        """
        result = await db.execute(
            select(Column)
            .where(Column.board_id == board_id)
            .order_by(Column.order)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_column(
        db: AsyncSession, board_id: UUID, column_data: ColumnCreate
    ) -> Column:
        """
        Create a new column for a board.

        If order is not provided, places the column at the end.

        Args:
            db: Database session
            board_id: Board UUID
            column_data: Column creation data

        Returns:
            Created column
        """
        # Verify board exists
        board = await BoardService.get_board(db, board_id)
        if not board:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Board {board_id} not found",
            )

        # Calculate order if not provided
        order = column_data.order
        if order is None:
            result = await db.execute(
                select(func.max(Column.order)).where(Column.board_id == board_id)
            )
            max_order = result.scalar()
            order = (max_order or 0) + 1000.0

        column = Column(
            board_id=board_id,
            name=column_data.name,
            order=order,
            color=column_data.color,
            wip_limit=column_data.wip_limit,
        )
        db.add(column)
        await db.flush()
        await db.refresh(column)
        return column

    @staticmethod
    async def update_column(
        db: AsyncSession, column_id: UUID, column_data: ColumnUpdate
    ) -> Optional[Column]:
        """
        Update a column.

        Args:
            db: Database session
            column_id: Column UUID
            column_data: Column update data

        Returns:
            Updated column or None if not found
        """
        result = await db.execute(select(Column).where(Column.id == column_id))
        column = result.scalar_one_or_none()
        if not column:
            return None

        update_dict = column_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(column, key, value)

        await db.flush()
        await db.refresh(column)
        return column

    @staticmethod
    async def delete_column(db: AsyncSession, column_id: UUID) -> bool:
        """
        Delete a column.

        Args:
            db: Database session
            column_id: Column UUID

        Returns:
            True if deleted, False if not found
        """
        result = await db.execute(select(Column).where(Column.id == column_id))
        column = result.scalar_one_or_none()
        if not column:
            return False

        await db.delete(column)
        await db.flush()
        return True

    @staticmethod
    async def get_tasks(db: AsyncSession, board_id: UUID) -> List[Task]:
        """
        Get all tasks for a board.

        Args:
            db: Database session
            board_id: Board UUID

        Returns:
            List of tasks
        """
        result = await db.execute(
            select(Task)
            .where(Task.board_id == board_id)
            .order_by(Task.column_id, Task.order)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_task(db: AsyncSession, task_id: UUID) -> Optional[Task]:
        """
        Get a task by ID.

        Args:
            db: Database session
            task_id: Task UUID

        Returns:
            Task or None if not found
        """
        result = await db.execute(select(Task).where(Task.id == task_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_task(
        db: AsyncSession, board_id: UUID, task_data: TaskCreate
    ) -> Task:
        """
        Create a new task for a board.

        If order is not provided, places the task at the end of its column.

        Args:
            db: Database session
            board_id: Board UUID
            task_data: Task creation data

        Returns:
            Created task
        """
        # Verify board exists
        board = await BoardService.get_board(db, board_id)
        if not board:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Board {board_id} not found",
            )

        # Verify column exists if provided
        if task_data.column_id:
            result = await db.execute(
                select(Column).where(
                    and_(
                        Column.id == task_data.column_id,
                        Column.board_id == board_id,
                    )
                )
            )
            column = result.scalar_one_or_none()
            if not column:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Column {task_data.column_id} not found in board {board_id}",
                )

        # Calculate order if not provided
        order = task_data.order
        if order is None:
            result = await db.execute(
                select(func.max(Task.order)).where(
                    and_(
                        Task.board_id == board_id,
                        Task.column_id == task_data.column_id,
                    )
                )
            )
            max_order = result.scalar()
            order = (max_order or 0) + 1000.0

        task = Task(
            board_id=board_id,
            column_id=task_data.column_id,
            title=task_data.title,
            description=task_data.description,
            order=order,
            priority=task_data.priority,
            labels=task_data.labels,
        )
        db.add(task)
        await db.flush()
        await db.refresh(task)

        # Log task creation activity
        await ActivityService.log_task_created(db, task, actor="user")

        return task

    @staticmethod
    async def update_task(
        db: AsyncSession, task_id: UUID, task_data: TaskUpdate
    ) -> Optional[Task]:
        """
        Update a task with optimistic locking.

        Args:
            db: Database session
            task_id: Task UUID
            task_data: Task update data

        Returns:
            Updated task or None if not found

        Raises:
            HTTPException: If version mismatch (optimistic lock conflict)
        """
        task = await BoardService.get_task(db, task_id)
        if not task:
            return None

        # Check version for optimistic locking
        if task_data.version is not None and task.version != task_data.version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "VERSION_CONFLICT",
                    "message": "Task was modified by another user",
                    "server_version": task.version,
                    "client_version": task_data.version,
                },
            )

        update_dict = task_data.model_dump(exclude_unset=True, exclude={"version"})
        for key, value in update_dict.items():
            setattr(task, key, value)

        # Increment version
        task.version += 1

        await db.flush()
        await db.refresh(task)
        return task

    @staticmethod
    async def move_task(
        db: AsyncSession,
        task_id: UUID,
        move_data: TaskMove,
        validate_workflow: bool = True,
    ) -> Optional[Task]:
        """
        Move a task to a different column with optimistic locking.

        Args:
            db: Database session
            task_id: Task UUID
            move_data: Move operation data
            validate_workflow: Whether to validate against workflow rules

        Returns:
            Updated task or None if not found

        Raises:
            HTTPException: If version mismatch, invalid column, or workflow violation
        """
        task = await BoardService.get_task(db, task_id)
        if not task:
            return None

        # Check version for optimistic locking
        if task.version != move_data.version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "VERSION_CONFLICT",
                    "message": "Task was modified by another user",
                    "server_version": task.version,
                    "client_version": move_data.version,
                },
            )

        # Verify target column exists in same board
        result = await db.execute(
            select(Column).where(
                and_(
                    Column.id == move_data.column_id,
                    Column.board_id == task.board_id,
                )
            )
        )
        column = result.scalar_one_or_none()
        if not column:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Column {move_data.column_id} not found in board",
            )

        # Store original column for activity logging
        from_column_id = task.column_id

        # Validate workflow transition if moving to a different column
        if validate_workflow and from_column_id and from_column_id != move_data.column_id:
            is_valid = await WorkflowService.validate_transition(
                db, task.board_id, from_column_id, move_data.column_id
            )
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "WORKFLOW_VIOLATION",
                        "message": "This transition is not allowed by the workflow",
                        "from_column_id": str(from_column_id),
                        "to_column_id": str(move_data.column_id),
                    },
                )

        # Update task position and column
        task.column_id = move_data.column_id
        task.order = move_data.order
        task.version += 1

        await db.flush()

        # Log activity if column changed
        if from_column_id and from_column_id != move_data.column_id:
            await ActivityService.log_task_moved(
                db, task, from_column_id, move_data.column_id, actor="user"
            )

        await db.refresh(task)
        return task

    @staticmethod
    async def delete_task(db: AsyncSession, task_id: UUID) -> bool:
        """
        Delete a task.

        Args:
            db: Database session
            task_id: Task UUID

        Returns:
            True if deleted, False if not found
        """
        task = await BoardService.get_task(db, task_id)
        if not task:
            return False

        await db.delete(task)
        await db.flush()
        return True
