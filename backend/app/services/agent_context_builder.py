"""Agent context builder service for constructing agent input context."""

from typing import Optional, Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.task import Task
from app.models.board import Board
from app.models.column import Column
from app.models.agent_execution import AgentExecution
from app.models.agent_output import AgentOutput


class AgentContextBuilder:
    """Service for building context for agent execution."""

    # ========================================================================
    # Main Context Building Methods
    # ========================================================================

    @staticmethod
    async def build_architecture_context(
        db: AsyncSession,
        task: Task,
        execution: AgentExecution,
        project_context: Optional[dict] = None,
    ) -> dict:
        """
        Build context for the architecture phase.

        Args:
            db: Database session
            task: Task to process
            execution: Current execution
            project_context: Optional additional project context

        Returns:
            Context dictionary for architect agent
        """
        board = await AgentContextBuilder._get_board_with_columns(db, task.board_id)

        return {
            "task_id": str(task.id),
            "task_title": task.title,
            "task_description": task.description or "",
            "task_priority": task.priority,
            "task_labels": task.labels,
            "board_name": board.name if board else "",
            "board_description": board.description if board else "",
            "execution_id": str(execution.id),
            "workflow_type": execution.workflow_type,
            "project_context": project_context or {},
            "phase": "architecture",
            "iteration": execution.iteration,
        }

    @staticmethod
    async def build_development_context(
        db: AsyncSession,
        task: Task,
        execution: AgentExecution,
        project_context: Optional[dict] = None,
    ) -> dict:
        """
        Build context for the development phase.

        Args:
            db: Database session
            task: Task to process
            execution: Current execution
            project_context: Optional additional project context

        Returns:
            Context dictionary for developer agent
        """
        # Get architecture output from previous phase
        architecture_output = await AgentContextBuilder._get_phase_output(
            db, execution.id, "architecture"
        )

        board = await AgentContextBuilder._get_board_with_columns(db, task.board_id)

        context = {
            "task_id": str(task.id),
            "task_title": task.title,
            "task_description": task.description or "",
            "task_priority": task.priority,
            "task_labels": task.labels,
            "board_name": board.name if board else "",
            "execution_id": str(execution.id),
            "workflow_type": execution.workflow_type,
            "project_context": project_context or {},
            "phase": "development",
            "iteration": execution.iteration,
        }

        # Include architecture plan if available
        if architecture_output:
            context["architecture_plan"] = architecture_output.output_content
            context["architecture_structured"] = architecture_output.output_structured

        # Include previous review feedback if this is a revision iteration
        if execution.iteration > 1:
            review_output = await AgentContextBuilder._get_phase_output(
                db, execution.id, "review", execution.iteration - 1
            )
            if review_output:
                context["review_feedback"] = review_output.output_content
                context["review_structured"] = review_output.output_structured

        return context

    @staticmethod
    async def build_review_context(
        db: AsyncSession,
        task: Task,
        execution: AgentExecution,
        project_context: Optional[dict] = None,
    ) -> dict:
        """
        Build context for the review phase.

        Args:
            db: Database session
            task: Task to process
            execution: Current execution
            project_context: Optional additional project context

        Returns:
            Context dictionary for reviewer agent
        """
        # Get architecture and development outputs
        architecture_output = await AgentContextBuilder._get_phase_output(
            db, execution.id, "architecture"
        )
        development_output = await AgentContextBuilder._get_phase_output(
            db, execution.id, "development", execution.iteration
        )

        board = await AgentContextBuilder._get_board_with_columns(db, task.board_id)

        context = {
            "task_id": str(task.id),
            "task_title": task.title,
            "task_description": task.description or "",
            "board_name": board.name if board else "",
            "execution_id": str(execution.id),
            "workflow_type": execution.workflow_type,
            "project_context": project_context or {},
            "phase": "review",
            "iteration": execution.iteration,
        }

        # Include architecture plan for reference
        if architecture_output:
            context["architecture_plan"] = architecture_output.output_content
            context["architecture_structured"] = architecture_output.output_structured

        # Include code to review
        if development_output:
            context["code_to_review"] = development_output.output_content
            context["files_created"] = development_output.files_created
            context["implementation_context"] = development_output.output_structured

        # Include previous review for comparison if iteration > 1
        if execution.iteration > 1:
            prev_review = await AgentContextBuilder._get_phase_output(
                db, execution.id, "review", execution.iteration - 1
            )
            if prev_review:
                context["previous_review"] = prev_review.output_content
                context["previous_review_structured"] = prev_review.output_structured

        return context

    @staticmethod
    async def build_coordinator_context(
        db: AsyncSession,
        task: Task,
        execution: AgentExecution,
    ) -> dict:
        """
        Build context for the coordinator agent.

        Args:
            db: Database session
            task: Task to process
            execution: Current execution

        Returns:
            Context dictionary for coordinator agent
        """
        # Get all outputs for this execution
        outputs = await AgentContextBuilder._get_all_execution_outputs(db, execution.id)

        board = await AgentContextBuilder._get_board_with_columns(db, task.board_id)

        phase_summaries = []
        for output in outputs:
            phase_summaries.append({
                "phase": output.phase,
                "agent": output.agent_name,
                "iteration": output.iteration,
                "status": output.status,
                "started_at": output.started_at.isoformat() if output.started_at else None,
                "completed_at": output.completed_at.isoformat() if output.completed_at else None,
                "duration_ms": output.duration_ms,
                "has_output": bool(output.output_content),
            })

        return {
            "task_id": str(task.id),
            "task_title": task.title,
            "task_description": task.description or "",
            "board_name": board.name if board else "",
            "execution_id": str(execution.id),
            "workflow_type": execution.workflow_type,
            "current_phase": execution.current_phase,
            "status": execution.status,
            "iteration": execution.iteration,
            "max_iterations": execution.max_iterations,
            "phase_summaries": phase_summaries,
        }

    # ========================================================================
    # Helper Methods
    # ========================================================================

    @staticmethod
    async def _get_board_with_columns(
        db: AsyncSession,
        board_id: UUID,
    ) -> Optional[Board]:
        """Get board with columns loaded."""
        result = await db.execute(
            select(Board)
            .options(selectinload(Board.columns))
            .where(Board.id == board_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def _get_phase_output(
        db: AsyncSession,
        execution_id: UUID,
        phase: str,
        iteration: Optional[int] = None,
    ) -> Optional[AgentOutput]:
        """
        Get output for a specific phase.

        Args:
            db: Database session
            execution_id: Execution UUID
            phase: Phase name
            iteration: Specific iteration (optional, defaults to latest)

        Returns:
            Agent output or None
        """
        query = (
            select(AgentOutput)
            .where(AgentOutput.execution_id == execution_id)
            .where(AgentOutput.phase == phase)
            .where(AgentOutput.status == "completed")
        )

        if iteration is not None:
            query = query.where(AgentOutput.iteration == iteration)

        query = query.order_by(AgentOutput.iteration.desc()).limit(1)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def _get_all_execution_outputs(
        db: AsyncSession,
        execution_id: UUID,
    ) -> list[AgentOutput]:
        """Get all outputs for an execution."""
        result = await db.execute(
            select(AgentOutput)
            .where(AgentOutput.execution_id == execution_id)
            .order_by(AgentOutput.created_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_previous_outputs_for_task(
        db: AsyncSession,
        task_id: UUID,
        limit: int = 5,
    ) -> list[dict]:
        """
        Get previous execution outputs for a task.

        Useful for building context from past work on the same task.

        Args:
            db: Database session
            task_id: Task UUID
            limit: Maximum number of executions to include

        Returns:
            List of output summaries
        """
        result = await db.execute(
            select(AgentExecution)
            .options(selectinload(AgentExecution.outputs))
            .where(AgentExecution.task_id == task_id)
            .where(AgentExecution.status == "completed")
            .order_by(AgentExecution.created_at.desc())
            .limit(limit)
        )
        executions = list(result.scalars().all())

        summaries = []
        for execution in executions:
            summaries.append({
                "execution_id": str(execution.id),
                "workflow_type": execution.workflow_type,
                "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
                "result_summary": execution.result_summary,
                "outputs": [
                    {
                        "agent": o.agent_name,
                        "phase": o.phase,
                        "iteration": o.iteration,
                        "status": o.status,
                    }
                    for o in execution.outputs
                ],
            })

        return summaries

    @staticmethod
    def get_workflow_phases(workflow_type: str) -> list[str]:
        """
        Get the phases for a workflow type.

        Args:
            workflow_type: Type of workflow

        Returns:
            List of phase names
        """
        workflows = {
            "development": ["architecture", "development", "review"],
            "quick_development": ["development", "review"],
            "architecture_only": ["architecture"],
        }
        return workflows.get(workflow_type, ["development", "review"])

    @staticmethod
    def get_agent_for_phase(phase: str) -> str:
        """
        Get the agent name for a phase.

        Args:
            phase: Phase name

        Returns:
            Agent name
        """
        agents = {
            "architecture": "software-architect",
            "development": "software-developer",
            "review": "code-reviewer",
        }
        return agents.get(phase, "software-developer")
