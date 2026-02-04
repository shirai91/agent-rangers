"""Agent orchestrator service for managing Claude-Flow agent execution."""

import asyncio
import json
import logging
import os
import tempfile
from datetime import datetime
from typing import Optional, AsyncGenerator, Callable, Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.task import Task
from app.models.agent_execution import AgentExecution
from app.models.agent_output import AgentOutput
from app.services.agent_context_builder import AgentContextBuilder
from app.services.activity_service import ActivityService

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrator for managing Claude-Flow agent execution.

    Handles spawning agents, managing workflow phases, streaming output,
    and coordinating the architect → developer → reviewer pipeline.
    """

    # ========================================================================
    # Execution Management
    # ========================================================================

    @staticmethod
    async def create_execution(
        db: AsyncSession,
        task_id: UUID,
        board_id: UUID,
        workflow_type: str = "development",
        context: Optional[dict] = None,
    ) -> AgentExecution:
        """
        Create a new agent execution.

        Args:
            db: Database session
            task_id: Task UUID
            board_id: Board UUID
            workflow_type: Type of workflow to run
            context: Additional execution context

        Returns:
            Created execution
        """
        execution = AgentExecution(
            task_id=task_id,
            board_id=board_id,
            workflow_type=workflow_type,
            status="pending",
            context=context or {},
        )
        db.add(execution)
        await db.flush()
        await db.refresh(execution)

        # Update task with current execution reference
        task = await db.get(Task, task_id)
        if task:
            task.current_execution_id = execution.id
            task.agent_status = "pending"
            await db.flush()

        return execution

    @staticmethod
    async def start_execution(
        db: AsyncSession,
        execution_id: UUID,
        on_output: Optional[Callable[[str, dict], Any]] = None,
    ) -> AgentExecution:
        """
        Start an agent execution.

        Args:
            db: Database session
            execution_id: Execution UUID
            on_output: Optional callback for streaming output

        Returns:
            Updated execution
        """
        execution = await AgentOrchestrator._get_execution(db, execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        if execution.status != "pending":
            raise ValueError(f"Execution {execution_id} is not in pending status")

        # Update status
        execution.status = "running"
        execution.started_at = datetime.utcnow()
        await db.flush()

        # Update task status
        task = await db.get(Task, execution.task_id)
        if task:
            task.agent_status = "running"
            await db.flush()

        # Log activity
        await ActivityService.log_activity(
            db=db,
            task_id=execution.task_id,
            board_id=execution.board_id,
            activity_type="agent_started",
            actor="queen-coordinator",
            metadata={
                "execution_id": str(execution_id),
                "workflow_type": execution.workflow_type,
            },
        )

        return execution

    @staticmethod
    async def run_workflow(
        db: AsyncSession,
        execution: AgentExecution,
        on_output: Optional[Callable[[str, dict], Any]] = None,
    ) -> AgentExecution:
        """
        Run the complete agent workflow.

        Args:
            db: Database session
            execution: Execution to run
            on_output: Optional callback for streaming output

        Returns:
            Completed execution
        """
        task = await db.get(Task, execution.task_id)
        if not task:
            raise ValueError(f"Task {execution.task_id} not found")

        phases = AgentContextBuilder.get_workflow_phases(execution.workflow_type)

        try:
            for phase in phases:
                execution.current_phase = phase
                if task:
                    task.agent_status = phase
                await db.flush()

                # Build context for this phase
                context = await AgentOrchestrator._build_phase_context(
                    db, task, execution, phase
                )

                # Run the agent for this phase
                output = await AgentOrchestrator._run_agent_phase(
                    db, execution, task, phase, context, on_output
                )

                # Check if review requires changes
                if phase == "review" and output.output_structured:
                    review_status = output.output_structured.get("status")
                    if review_status == "CHANGES_REQUESTED":
                        if execution.iteration < execution.max_iterations:
                            # Increment iteration and re-run development + review
                            execution.iteration += 1
                            await db.flush()

                            # Re-run development phase
                            dev_context = await AgentOrchestrator._build_phase_context(
                                db, task, execution, "development"
                            )
                            await AgentOrchestrator._run_agent_phase(
                                db, execution, task, "development", dev_context, on_output
                            )

                            # Re-run review phase
                            review_context = await AgentOrchestrator._build_phase_context(
                                db, task, execution, "review"
                            )
                            await AgentOrchestrator._run_agent_phase(
                                db, execution, task, "review", review_context, on_output
                            )

            # Mark execution as completed
            execution.status = "completed"
            execution.completed_at = datetime.utcnow()
            execution.result_summary = await AgentOrchestrator._build_result_summary(
                db, execution
            )

            if task:
                task.agent_status = "completed"

            await db.flush()

            # Log completion activity
            await ActivityService.log_activity(
                db=db,
                task_id=execution.task_id,
                board_id=execution.board_id,
                activity_type="agent_completed",
                actor="queen-coordinator",
                metadata={
                    "execution_id": str(execution.id),
                    "workflow_type": execution.workflow_type,
                    "iterations": execution.iteration,
                },
            )

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            execution.status = "failed"
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()

            if task:
                task.agent_status = "failed"

            await db.flush()

            # Log failure activity
            await ActivityService.log_activity(
                db=db,
                task_id=execution.task_id,
                board_id=execution.board_id,
                activity_type="agent_failed",
                actor="queen-coordinator",
                metadata={
                    "execution_id": str(execution.id),
                    "error": str(e),
                },
            )

            raise

        return execution

    @staticmethod
    async def cancel_execution(
        db: AsyncSession,
        execution_id: UUID,
    ) -> AgentExecution:
        """
        Cancel a running execution.

        Args:
            db: Database session
            execution_id: Execution UUID

        Returns:
            Updated execution
        """
        execution = await AgentOrchestrator._get_execution(db, execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        if execution.status not in ("pending", "running"):
            raise ValueError(f"Execution {execution_id} cannot be cancelled")

        execution.status = "cancelled"
        execution.completed_at = datetime.utcnow()
        await db.flush()

        # Update task status
        task = await db.get(Task, execution.task_id)
        if task:
            task.agent_status = None
            await db.flush()

        # Log cancellation activity
        await ActivityService.log_activity(
            db=db,
            task_id=execution.task_id,
            board_id=execution.board_id,
            activity_type="agent_cancelled",
            actor="system",
            metadata={
                "execution_id": str(execution_id),
            },
        )

        return execution

    # ========================================================================
    # Agent Phase Execution
    # ========================================================================

    @staticmethod
    async def _run_agent_phase(
        db: AsyncSession,
        execution: AgentExecution,
        task: Task,
        phase: str,
        context: dict,
        on_output: Optional[Callable[[str, dict], Any]] = None,
    ) -> AgentOutput:
        """
        Run a single agent phase.

        Args:
            db: Database session
            execution: Parent execution
            task: Task being processed
            phase: Phase name
            context: Input context for the agent
            on_output: Optional callback for streaming output

        Returns:
            Agent output
        """
        agent_name = AgentContextBuilder.get_agent_for_phase(phase)

        # Create output record
        output = AgentOutput(
            execution_id=execution.id,
            task_id=task.id,
            agent_name=agent_name,
            phase=phase,
            iteration=execution.iteration,
            status="running",
            input_context=context,
            started_at=datetime.utcnow(),
        )
        db.add(output)
        await db.flush()

        # Log phase start activity
        await ActivityService.log_activity(
            db=db,
            task_id=task.id,
            board_id=execution.board_id,
            activity_type=f"agent_phase_started",
            actor=agent_name,
            metadata={
                "execution_id": str(execution.id),
                "output_id": str(output.id),
                "phase": phase,
                "iteration": execution.iteration,
            },
        )

        try:
            # Execute the agent (simulated for now)
            # In production, this would call claude-flow
            result = await AgentOrchestrator._execute_agent(
                agent_name, context, on_output
            )

            # Update output with result
            output.status = "completed"
            output.completed_at = datetime.utcnow()
            output.output_content = result.get("content", "")
            output.output_structured = result.get("structured")
            output.files_created = result.get("files", [])
            output.tokens_used = result.get("tokens_used")
            output.duration_ms = (
                int((output.completed_at - output.started_at).total_seconds() * 1000)
                if output.started_at
                else None
            )

            await db.flush()

            # Log phase completion
            await ActivityService.log_activity(
                db=db,
                task_id=task.id,
                board_id=execution.board_id,
                activity_type=f"agent_phase_completed",
                actor=agent_name,
                metadata={
                    "execution_id": str(execution.id),
                    "output_id": str(output.id),
                    "phase": phase,
                    "iteration": execution.iteration,
                    "duration_ms": output.duration_ms,
                },
            )

        except Exception as e:
            logger.error(f"Agent phase {phase} failed: {e}")
            output.status = "failed"
            output.error_message = str(e)
            output.completed_at = datetime.utcnow()
            await db.flush()
            raise

        return output

    @staticmethod
    async def _execute_agent(
        agent_name: str,
        context: dict,
        on_output: Optional[Callable[[str, dict], Any]] = None,
    ) -> dict:
        """
        Execute an agent with the given context using claude-flow CLI.

        Args:
            agent_name: Name of the agent
            context: Input context
            on_output: Optional callback for streaming output

        Returns:
            Agent result dictionary with content, structured data, files, and token usage
        """
        # Map phase names to agent names for claude-flow CLI
        phase = context.get("phase", "unknown")
        agent_mapping = {
            "architecture": "software-architect",
            "development": "software-developer",
            "review": "code-reviewer",
        }
        cli_agent_name = agent_mapping.get(phase, agent_name)

        # Working directory where .claude/ config exists
        working_dir = "/home/shirai91/projects/personal/agent-rangers"

        # Create temporary file for input context
        temp_input_file = None
        try:
            # Create temp file with context
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.json',
                delete=False,
                dir=working_dir
            ) as f:
                json.dump(context, f, indent=2)
                temp_input_file = f.name

            if on_output:
                await on_output("progress", {
                    "agent": agent_name,
                    "phase": phase,
                    "message": f"Starting {cli_agent_name} agent...",
                })

            # Build command
            cmd = [
                "npx",
                "@claude-flow/cli@latest",
                "agent",
                "run",
                cli_agent_name,
                "--input",
                temp_input_file,
                "--output",
                "json"
            ]

            # Execute subprocess asynchronously
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir
            )

            # Stream output asynchronously
            stdout_lines = []
            stderr_lines = []

            async def read_stdout():
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    line_text = line.decode('utf-8').strip()
                    stdout_lines.append(line_text)

                    # Stream progress updates
                    if on_output and line_text:
                        await on_output("progress", {
                            "agent": agent_name,
                            "phase": phase,
                            "message": line_text[:200],  # Truncate long lines
                        })

            async def read_stderr():
                while True:
                    line = await process.stderr.readline()
                    if not line:
                        break
                    line_text = line.decode('utf-8').strip()
                    stderr_lines.append(line_text)

                    # Log errors but don't fail yet
                    if line_text:
                        logger.warning(f"Agent stderr: {line_text}")

            # Read both streams concurrently with timeout
            try:
                await asyncio.wait_for(
                    asyncio.gather(read_stdout(), read_stderr()),
                    timeout=300  # 5 minute timeout
                )
                await asyncio.wait_for(process.wait(), timeout=5)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise Exception(f"Agent execution timed out after 300 seconds")

            # Check return code
            if process.returncode != 0:
                error_msg = "\n".join(stderr_lines) if stderr_lines else "Unknown error"
                raise Exception(f"Agent execution failed with code {process.returncode}: {error_msg}")

            # Parse JSON output from stdout
            stdout_text = "\n".join(stdout_lines)

            # Try to find JSON in output (may have other text mixed in)
            result_data = None
            for line in stdout_lines:
                if line.strip().startswith('{'):
                    try:
                        result_data = json.loads(line)
                        break
                    except json.JSONDecodeError:
                        continue

            # If no JSON found in individual lines, try the whole output
            if result_data is None:
                try:
                    result_data = json.loads(stdout_text)
                except json.JSONDecodeError:
                    # If still no valid JSON, create a basic result
                    logger.warning(f"Could not parse JSON output, using raw text")
                    result_data = {
                        "content": stdout_text,
                        "structured": None,
                        "files": [],
                        "tokens_used": None
                    }

            # Ensure required keys exist
            result = {
                "content": result_data.get("content", stdout_text),
                "structured": result_data.get("structured"),
                "files": result_data.get("files", []),
                "tokens_used": result_data.get("tokens_used")
            }

            if on_output:
                await on_output("progress", {
                    "agent": agent_name,
                    "phase": phase,
                    "message": f"Completed {cli_agent_name} agent",
                })

            return result

        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            if on_output:
                await on_output("error", {
                    "agent": agent_name,
                    "phase": phase,
                    "message": f"Error: {str(e)}",
                })
            raise
        finally:
            # Clean up temp file
            if temp_input_file and os.path.exists(temp_input_file):
                try:
                    os.unlink(temp_input_file)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {temp_input_file}: {e}")

    # ========================================================================
    # Helper Methods
    # ========================================================================

    @staticmethod
    async def _get_execution(
        db: AsyncSession,
        execution_id: UUID,
    ) -> Optional[AgentExecution]:
        """Get execution by ID with outputs loaded."""
        result = await db.execute(
            select(AgentExecution)
            .options(selectinload(AgentExecution.outputs))
            .where(AgentExecution.id == execution_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def _build_phase_context(
        db: AsyncSession,
        task: Task,
        execution: AgentExecution,
        phase: str,
    ) -> dict:
        """Build context for a specific phase."""
        if phase == "architecture":
            return await AgentContextBuilder.build_architecture_context(
                db, task, execution
            )
        elif phase == "development":
            return await AgentContextBuilder.build_development_context(
                db, task, execution
            )
        elif phase == "review":
            return await AgentContextBuilder.build_review_context(
                db, task, execution
            )
        else:
            raise ValueError(f"Unknown phase: {phase}")

    @staticmethod
    async def _build_result_summary(
        db: AsyncSession,
        execution: AgentExecution,
    ) -> dict:
        """Build result summary for completed execution."""
        outputs = await AgentContextBuilder._get_all_execution_outputs(db, execution.id)

        total_tokens = sum(o.tokens_used or 0 for o in outputs)
        total_duration = sum(o.duration_ms or 0 for o in outputs)
        all_files = []
        for o in outputs:
            all_files.extend(o.files_created or [])

        # Get final review status if available
        final_review = next(
            (o for o in reversed(outputs) if o.phase == "review" and o.output_structured),
            None
        )

        return {
            "phases_completed": len(outputs),
            "iterations": execution.iteration,
            "total_tokens": total_tokens,
            "total_duration_ms": total_duration,
            "files_affected": all_files,
            "review_status": final_review.output_structured.get("status") if final_review else None,
        }

    # ========================================================================
    # Query Methods
    # ========================================================================

    @staticmethod
    async def get_execution_status(
        db: AsyncSession,
        execution_id: UUID,
    ) -> Optional[dict]:
        """
        Get current status of an execution.

        Args:
            db: Database session
            execution_id: Execution UUID

        Returns:
            Status dictionary or None
        """
        execution = await AgentOrchestrator._get_execution(db, execution_id)
        if not execution:
            return None

        return {
            "execution_id": str(execution.id),
            "task_id": str(execution.task_id),
            "workflow_type": execution.workflow_type,
            "status": execution.status,
            "current_phase": execution.current_phase,
            "iteration": execution.iteration,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "error_message": execution.error_message,
            "outputs": [
                {
                    "id": str(o.id),
                    "agent_name": o.agent_name,
                    "phase": o.phase,
                    "iteration": o.iteration,
                    "status": o.status,
                }
                for o in execution.outputs
            ],
        }

    @staticmethod
    async def get_task_executions(
        db: AsyncSession,
        task_id: UUID,
        limit: int = 10,
    ) -> list[AgentExecution]:
        """
        Get executions for a task.

        Args:
            db: Database session
            task_id: Task UUID
            limit: Maximum number to return

        Returns:
            List of executions
        """
        result = await db.execute(
            select(AgentExecution)
            .options(selectinload(AgentExecution.outputs))
            .where(AgentExecution.task_id == task_id)
            .order_by(AgentExecution.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_board_executions(
        db: AsyncSession,
        board_id: UUID,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> list[AgentExecution]:
        """
        Get executions for a board.

        Args:
            db: Database session
            board_id: Board UUID
            status: Optional status filter
            limit: Maximum number to return

        Returns:
            List of executions
        """
        query = (
            select(AgentExecution)
            .options(selectinload(AgentExecution.outputs))
            .where(AgentExecution.board_id == board_id)
        )

        if status:
            query = query.where(AgentExecution.status == status)

        query = query.order_by(AgentExecution.created_at.desc()).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())
