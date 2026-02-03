"""Higher-level workflow orchestration service for agent tasks.

This service provides workflow-level operations for managing agent execution
through different phases (architecture, development, review) with support for
feedback loops and workflow recommendations.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.task import Task
from app.models.agent_execution import AgentExecution
from app.services.agent_orchestrator import AgentOrchestrator
from app.services.agent_context_builder import AgentContextBuilder
from app.services.activity_service import ActivityService

logger = logging.getLogger(__name__)


class AgentWorkflowService:
    """
    Service for higher-level workflow orchestration of agent tasks.

    Provides phase-specific execution methods, feedback handling, workflow
    status tracking, and intelligent workflow recommendations based on task
    properties.
    """

    # ========================================================================
    # Phase-Specific Workflow Execution
    # ========================================================================

    @staticmethod
    async def start_architecture_phase(
        db: AsyncSession,
        task_id: UUID,
        context: Optional[dict] = None,
    ) -> AgentExecution:
        """
        Start the architecture phase for a task.

        Creates a new execution with architecture_only workflow and begins
        the architect agent process.

        Args:
            db: Database session
            task_id: Task UUID
            context: Optional additional context for the architect

        Returns:
            Created and started execution

        Raises:
            ValueError: If task not found or has running execution
        """
        task = await AgentWorkflowService._get_task(db, task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        # Check for existing running execution
        if task.agent_status in ("pending", "running", "architecture", "development", "review"):
            raise ValueError(
                f"Task {task_id} already has a running execution (status: {task.agent_status})"
            )

        logger.info(f"Starting architecture phase for task {task_id}")

        # Create execution
        execution = await AgentOrchestrator.create_execution(
            db=db,
            task_id=task_id,
            board_id=task.board_id,
            workflow_type="architecture_only",
            context=context or {},
        )

        # Start execution
        await AgentOrchestrator.start_execution(db, execution.id)

        # Log activity
        await ActivityService.log_activity(
            db=db,
            task_id=task_id,
            board_id=task.board_id,
            activity_type="workflow_phase_started",
            actor="queen-coordinator",
            metadata={
                "execution_id": str(execution.id),
                "phase": "architecture",
                "workflow_type": "architecture_only",
            },
        )

        await db.commit()

        return execution

    @staticmethod
    async def start_development_phase(
        db: AsyncSession,
        task_id: UUID,
        context: Optional[dict] = None,
    ) -> AgentExecution:
        """
        Start the development phase for a task.

        Creates a new execution with quick_development workflow that skips
        architecture and goes straight to development and review.

        Args:
            db: Database session
            task_id: Task UUID
            context: Optional additional context for the developer

        Returns:
            Created and started execution

        Raises:
            ValueError: If task not found or has running execution
        """
        task = await AgentWorkflowService._get_task(db, task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        # Check for existing running execution
        if task.agent_status in ("pending", "running", "architecture", "development", "review"):
            raise ValueError(
                f"Task {task_id} already has a running execution (status: {task.agent_status})"
            )

        logger.info(f"Starting development phase for task {task_id}")

        # Create execution
        execution = await AgentOrchestrator.create_execution(
            db=db,
            task_id=task_id,
            board_id=task.board_id,
            workflow_type="quick_development",
            context=context or {},
        )

        # Start execution
        await AgentOrchestrator.start_execution(db, execution.id)

        # Log activity
        await ActivityService.log_activity(
            db=db,
            task_id=task_id,
            board_id=task.board_id,
            activity_type="workflow_phase_started",
            actor="queen-coordinator",
            metadata={
                "execution_id": str(execution.id),
                "phase": "development",
                "workflow_type": "quick_development",
            },
        )

        await db.commit()

        return execution

    @staticmethod
    async def start_review_phase(
        db: AsyncSession,
        task_id: UUID,
        context: Optional[dict] = None,
    ) -> AgentExecution:
        """
        Start the review phase for a task.

        This method is typically used to trigger a standalone review without
        going through full development workflow. It requires that development
        artifacts already exist.

        Args:
            db: Database session
            task_id: Task UUID
            context: Optional additional context for the reviewer (must include
                    code_to_review or reference to existing outputs)

        Returns:
            Created and started execution

        Raises:
            ValueError: If task not found, has running execution, or lacks
                       development artifacts for review
        """
        task = await AgentWorkflowService._get_task(db, task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        # Check for existing running execution
        if task.agent_status in ("pending", "running", "architecture", "development", "review"):
            raise ValueError(
                f"Task {task_id} already has a running execution (status: {task.agent_status})"
            )

        # Verify there's something to review
        if not context or not context.get("code_to_review"):
            # Check for previous development outputs
            previous_outputs = await AgentContextBuilder.get_previous_outputs_for_task(
                db, task_id, limit=1
            )
            if not previous_outputs:
                raise ValueError(
                    f"Task {task_id} has no development artifacts to review. "
                    "Run development phase first or provide code_to_review in context."
                )

        logger.info(f"Starting review phase for task {task_id}")

        # For standalone review, we create a minimal execution
        # Note: This is a special case - normally review is part of a workflow
        execution = await AgentOrchestrator.create_execution(
            db=db,
            task_id=task_id,
            board_id=task.board_id,
            workflow_type="review_only",
            context=context or {},
        )

        # Start execution
        await AgentOrchestrator.start_execution(db, execution.id)

        # Log activity
        await ActivityService.log_activity(
            db=db,
            task_id=task_id,
            board_id=task.board_id,
            activity_type="workflow_phase_started",
            actor="queen-coordinator",
            metadata={
                "execution_id": str(execution.id),
                "phase": "review",
                "workflow_type": "review_only",
            },
        )

        await db.commit()

        return execution

    # ========================================================================
    # Feedback Loop Handling
    # ========================================================================

    @staticmethod
    async def handle_review_feedback(
        db: AsyncSession,
        execution_id: UUID,
        approved: bool,
        feedback_notes: Optional[str] = None,
    ) -> AgentExecution:
        """
        Handle review feedback for an execution.

        If approved, marks the execution as completed. If not approved and
        iterations remain, triggers another development + review cycle.

        Args:
            db: Database session
            execution_id: Execution UUID
            approved: Whether the review approved the implementation
            feedback_notes: Optional additional feedback from user/reviewer

        Returns:
            Updated execution

        Raises:
            ValueError: If execution not found, not in reviewable state, or
                       max iterations exceeded
        """
        execution = await AgentOrchestrator._get_execution(db, execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        if execution.status not in ("running", "completed"):
            raise ValueError(
                f"Execution {execution_id} is not in a reviewable state (status: {execution.status})"
            )

        task = await db.get(Task, execution.task_id)
        if not task:
            raise ValueError(f"Task {execution.task_id} not found")

        logger.info(
            f"Handling review feedback for execution {execution_id}: approved={approved}"
        )

        if approved:
            # Mark as completed if not already
            if execution.status != "completed":
                execution.status = "completed"
                execution.completed_at = datetime.utcnow()
                if task:
                    task.agent_status = "completed"

                await ActivityService.log_activity(
                    db=db,
                    task_id=execution.task_id,
                    board_id=execution.board_id,
                    activity_type="workflow_approved",
                    actor="user",
                    metadata={
                        "execution_id": str(execution_id),
                        "feedback_notes": feedback_notes,
                    },
                )

            await db.commit()
            logger.info(f"Execution {execution_id} approved and completed")

        else:
            # Request changes - trigger feedback loop if iterations remain
            if execution.iteration >= execution.max_iterations:
                raise ValueError(
                    f"Execution {execution_id} has reached max iterations ({execution.max_iterations})"
                )

            logger.info(
                f"Changes requested for execution {execution_id}. "
                f"Starting iteration {execution.iteration + 1}/{execution.max_iterations}"
            )

            # Increment iteration
            execution.iteration += 1

            # Update context with feedback
            execution.context["user_feedback"] = feedback_notes
            execution.context["feedback_iteration"] = execution.iteration

            # Re-run development phase with feedback
            dev_context = await AgentContextBuilder.build_development_context(
                db, task, execution
            )
            dev_context["user_feedback"] = feedback_notes

            await AgentOrchestrator._run_agent_phase(
                db, execution, task, "development", dev_context
            )

            # Re-run review phase
            review_context = await AgentContextBuilder.build_review_context(
                db, task, execution
            )
            await AgentOrchestrator._run_agent_phase(
                db, execution, task, "review", review_context
            )

            await ActivityService.log_activity(
                db=db,
                task_id=execution.task_id,
                board_id=execution.board_id,
                activity_type="workflow_feedback_iteration",
                actor="user",
                metadata={
                    "execution_id": str(execution_id),
                    "iteration": execution.iteration,
                    "feedback_notes": feedback_notes,
                },
            )

            await db.commit()

        await db.refresh(execution)
        return execution

    # ========================================================================
    # Workflow Status and Query
    # ========================================================================

    @staticmethod
    async def get_workflow_status(
        db: AsyncSession,
        execution_id: UUID,
    ) -> Optional[dict]:
        """
        Get comprehensive workflow status for an execution.

        Provides detailed information about execution progress, phases
        completed, current state, and any errors.

        Args:
            db: Database session
            execution_id: Execution UUID

        Returns:
            Status dictionary with workflow details or None if not found
        """
        status = await AgentOrchestrator.get_execution_status(db, execution_id)
        if not status:
            return None

        execution = await AgentOrchestrator._get_execution(db, execution_id)
        if not execution:
            return None

        # Get phase summary
        phases = AgentContextBuilder.get_workflow_phases(execution.workflow_type)
        phase_status = []
        for phase in phases:
            phase_output = await AgentContextBuilder._get_phase_output(
                db, execution_id, phase
            )
            phase_status.append({
                "phase": phase,
                "agent": AgentContextBuilder.get_agent_for_phase(phase),
                "completed": phase_output is not None,
                "status": phase_output.status if phase_output else None,
                "duration_ms": phase_output.duration_ms if phase_output else None,
            })

        # Calculate progress percentage
        completed_phases = sum(1 for p in phase_status if p["completed"])
        progress = int((completed_phases / len(phases)) * 100) if phases else 0

        return {
            **status,
            "workflow_phases": phase_status,
            "progress_percentage": progress,
            "can_approve": execution.status == "completed" and execution.current_phase == "review",
            "can_request_changes": execution.status == "completed" and execution.iteration < execution.max_iterations,
            "remaining_iterations": execution.max_iterations - execution.iteration,
        }

    @staticmethod
    async def get_task_workflow_history(
        db: AsyncSession,
        task_id: UUID,
        limit: int = 10,
    ) -> list[dict]:
        """
        Get workflow execution history for a task.

        Args:
            db: Database session
            task_id: Task UUID
            limit: Maximum number of executions to return

        Returns:
            List of execution summaries with workflow details
        """
        executions = await AgentOrchestrator.get_task_executions(db, task_id, limit)

        history = []
        for execution in executions:
            phases = AgentContextBuilder.get_workflow_phases(execution.workflow_type)
            completed_phases = sum(
                1 for o in execution.outputs if o.status == "completed"
            )

            history.append({
                "execution_id": str(execution.id),
                "workflow_type": execution.workflow_type,
                "status": execution.status,
                "current_phase": execution.current_phase,
                "iteration": execution.iteration,
                "started_at": execution.started_at.isoformat() if execution.started_at else None,
                "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
                "phases_completed": completed_phases,
                "total_phases": len(phases),
                "error_message": execution.error_message,
            })

        return history

    # ========================================================================
    # Workflow Recommendations
    # ========================================================================

    @staticmethod
    async def get_recommended_workflow(
        db: AsyncSession,
        task: Task,
    ) -> dict:
        """
        Recommend a workflow type based on task properties.

        Analyzes task characteristics like description length, complexity
        indicators, priority, and labels to suggest the most appropriate
        workflow.

        Args:
            db: Database session
            task: Task to analyze

        Returns:
            Dictionary with recommendation details:
            - workflow_type: Recommended workflow
            - confidence: Confidence score (0-1)
            - reasoning: Explanation of recommendation
        """
        description = task.description or ""
        title = task.title or ""
        labels = task.labels or []
        priority = task.priority

        # Scoring factors
        score_full = 0.0
        score_quick = 0.0
        score_arch_only = 0.0
        reasoning_parts = []

        # Length-based scoring
        desc_length = len(description)
        if desc_length > 500:
            score_full += 0.3
            reasoning_parts.append("Detailed description suggests full workflow")
        elif desc_length < 100:
            score_quick += 0.2
            reasoning_parts.append("Brief description suggests quick workflow")

        # Complexity indicators in text
        complexity_keywords = [
            "architecture", "design", "system", "infrastructure",
            "scalable", "distributed", "microservice", "api design"
        ]
        complexity_count = sum(
            1 for keyword in complexity_keywords
            if keyword.lower() in description.lower() or keyword.lower() in title.lower()
        )
        if complexity_count >= 2:
            score_full += 0.4
            reasoning_parts.append("Multiple architectural keywords detected")
        elif complexity_count == 1:
            score_arch_only += 0.2

        # Simple task indicators
        simple_keywords = [
            "fix", "bug", "typo", "update", "change",
            "quick", "minor", "small", "simple"
        ]
        simple_count = sum(
            1 for keyword in simple_keywords
            if keyword.lower() in description.lower() or keyword.lower() in title.lower()
        )
        if simple_count >= 2:
            score_quick += 0.3
            reasoning_parts.append("Task appears to be straightforward")

        # Priority-based scoring
        if priority >= 4:  # Urgent
            score_quick += 0.2
            reasoning_parts.append("High priority suggests quick implementation")
        elif priority <= 1:  # Low priority
            score_full += 0.1

        # Label-based scoring
        label_str = " ".join(str(label).lower() for label in labels)
        if "architecture" in label_str or "design" in label_str:
            score_arch_only += 0.3
            score_full += 0.2
            reasoning_parts.append("Architecture/design labels present")
        if "bug" in label_str or "hotfix" in label_str:
            score_quick += 0.3
            reasoning_parts.append("Bug/hotfix labels suggest quick workflow")
        if "feature" in label_str or "enhancement" in label_str:
            score_full += 0.2

        # Check for existing architecture work
        previous_outputs = await AgentContextBuilder.get_previous_outputs_for_task(
            db, task.id, limit=5
        )
        has_architecture = any(
            "architecture" in str(output.get("outputs", [])).lower()
            for output in previous_outputs
        )
        if has_architecture:
            score_quick += 0.2
            reasoning_parts.append("Previous architecture work exists")

        # Normalize scores
        total = score_full + score_quick + score_arch_only
        if total > 0:
            score_full /= total
            score_quick /= total
            score_arch_only /= total

        # Determine recommendation
        max_score = max(score_full, score_quick, score_arch_only)
        confidence = max_score

        if max_score == score_full:
            workflow_type = "development"
            if not reasoning_parts:
                reasoning_parts.append("Comprehensive workflow recommended as default")
        elif max_score == score_quick:
            workflow_type = "quick_development"
            if not reasoning_parts:
                reasoning_parts.append("Quick workflow suitable for this task")
        else:
            workflow_type = "architecture_only"
            if not reasoning_parts:
                reasoning_parts.append("Architecture planning phase recommended")

        # Default to development if scores are equal
        if score_full == score_quick == score_arch_only:
            workflow_type = "development"
            confidence = 0.5
            reasoning_parts = ["Default comprehensive workflow recommended"]

        return {
            "workflow_type": workflow_type,
            "confidence": round(confidence, 2),
            "reasoning": "; ".join(reasoning_parts),
            "alternatives": {
                "development": round(score_full, 2),
                "quick_development": round(score_quick, 2),
                "architecture_only": round(score_arch_only, 2),
            },
        }

    # ========================================================================
    # Helper Methods
    # ========================================================================

    @staticmethod
    async def _get_task(
        db: AsyncSession,
        task_id: UUID,
    ) -> Optional[Task]:
        """Get task by ID with related data."""
        result = await db.execute(
            select(Task)
            .options(
                selectinload(Task.current_execution),
                selectinload(Task.board),
            )
            .where(Task.id == task_id)
        )
        return result.scalar_one_or_none()
