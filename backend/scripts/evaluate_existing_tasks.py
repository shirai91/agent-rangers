#!/usr/bin/env python
"""Script to evaluate all existing tasks that don't have evaluations yet.

This script connects to the database, retrieves all tasks, and runs the
task_evaluator.evaluate_task() for any task that doesn't have an info.json
file in its outputs directory.

Usage:
    python scripts/evaluate_existing_tasks.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the backend directory to the path so we can import app modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal
from app.models.task import Task
from app.services.file_storage import file_storage
from app.services.task_evaluator import task_evaluator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def has_evaluation(board_id: str, task_id: str) -> bool:
    """
    Check if a task already has an info.json evaluation file.

    Args:
        board_id: The UUID of the board as a string.
        task_id: The UUID of the task as a string.

    Returns:
        True if info.json exists, False otherwise.
    """
    outputs_dir = (
        file_storage.base_dir / "boards" / board_id / "tasks" / task_id / "outputs"
    )
    info_path = outputs_dir / "info.json"
    return info_path.exists()


async def evaluate_existing_tasks() -> None:
    """
    Evaluate all existing tasks that don't have evaluations yet.

    Connects to the database, retrieves all tasks, checks for existing
    info.json files, and runs evaluate_task() for tasks without evaluations.
    """
    # Initialize file storage
    file_storage.initialize()

    logger.info("Starting evaluation of existing tasks...")

    async with AsyncSessionLocal() as session:
        # Get all tasks with their board relationship
        stmt = select(Task).options(selectinload(Task.board))
        result = await session.execute(stmt)
        tasks = result.scalars().all()

        total_tasks = len(tasks)
        logger.info(f"Found {total_tasks} tasks in database")

        evaluated_count = 0
        skipped_count = 0
        error_count = 0

        for i, task in enumerate(tasks, 1):
            board_id = str(task.board_id)
            task_id = str(task.id)

            logger.info(f"[{i}/{total_tasks}] Processing task: {task.title[:50]}...")

            # Check if evaluation already exists
            if has_evaluation(board_id, task_id):
                logger.info(f"  -> Skipping (already evaluated)")
                skipped_count += 1
                continue

            # Evaluate the task
            try:
                logger.info(f"  -> Evaluating...")
                await task_evaluator.evaluate_task(
                    board_id=board_id,
                    task_id=task_id,
                    task_title=task.title,
                    task_description=task.description or "",
                )
                logger.info(f"  -> Evaluation complete")
                evaluated_count += 1
            except Exception as e:
                logger.error(f"  -> Error evaluating task: {e}")
                error_count += 1

    logger.info("=" * 60)
    logger.info("Evaluation complete!")
    logger.info(f"  Total tasks:     {total_tasks}")
    logger.info(f"  Newly evaluated: {evaluated_count}")
    logger.info(f"  Skipped:         {skipped_count}")
    logger.info(f"  Errors:          {error_count}")


def main() -> None:
    """Main entry point for the script."""
    asyncio.run(evaluate_existing_tasks())


if __name__ == "__main__":
    main()
