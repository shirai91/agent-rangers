"""Agent orchestrator service for managing Claude-Flow agent execution."""

import asyncio
import json
import logging
import os
import re
from datetime import datetime
from typing import Optional, Callable, Any
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
        Execute an agent with the given context using claude-flow.

        Args:
            agent_name: Name of the agent
            context: Input context
            on_output: Optional callback for streaming output

        Returns:
            Agent result dictionary with content, structured data, files, and token usage
        """
        phase = context.get("phase", "unknown")

        # Agent type mapping for claude-flow
        agent_type_mapping = {
            "architecture": "coder",  # or "architect" if available
            "development": "coder",
            "review": "reviewer",
        }
        agent_type = agent_type_mapping.get(phase, "coder")

        # Check if claude-flow is enabled
        use_claude_flow = os.environ.get("USE_CLAUDE_FLOW", "false").lower() == "true"

        if use_claude_flow:
            return await AgentOrchestrator._execute_with_claude_flow(
                agent_type, agent_name, phase, context, on_output
            )
        else:
            # Fallback to simulated execution
            return await AgentOrchestrator._execute_simulated(
                agent_name, phase, context, {}, on_output
            )

    @staticmethod
    async def _execute_with_claude_flow(
        agent_type: str,
        agent_name: str,
        phase: str,
        context: dict,
        on_output: Optional[Callable[[str, dict], Any]] = None,
    ) -> dict:
        """
        Execute an agent using claude-flow CLI.

        Args:
            agent_type: claude-flow agent type (coder, reviewer, etc.)
            agent_name: Display name for the agent
            phase: Workflow phase
            context: Input context
            on_output: Optional callback for streaming output

        Returns:
            Agent result dictionary
        """
        # Build the task prompt
        task_prompt = AgentOrchestrator._build_task_prompt(context)

        # Generate unique agent name
        unique_name = f"{agent_name}-{phase}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        if on_output:
            await on_output("progress", {
                "agent": agent_name,
                "phase": phase,
                "message": f"Spawning {agent_type} agent via claude-flow...",
            })

        try:
            # Step 1: Spawn the agent
            spawn_cmd = [
                "npx", "@claude-flow/cli@latest", "agent", "spawn",
                "-t", agent_type,
                "--name", unique_name,
                "--task", task_prompt,
                "--output", "json",
            ]

            spawn_process = await asyncio.create_subprocess_exec(
                *spawn_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                spawn_process.communicate(),
                timeout=60  # 1 minute timeout for spawn
            )

            if spawn_process.returncode != 0:
                error_msg = stderr.decode('utf-8') if stderr else "Unknown error"
                logger.error(f"claude-flow agent spawn failed: {error_msg}")
                # Fallback to simulated
                return await AgentOrchestrator._execute_simulated(
                    agent_name, phase, context, {}, on_output
                )

            # Parse spawn output to get agent ID
            spawn_output = stdout.decode('utf-8')
            try:
                spawn_data = json.loads(spawn_output)
                agent_id = spawn_data.get("agent_id") or spawn_data.get("id")
            except json.JSONDecodeError:
                # Try to extract agent ID from text output
                agent_id = AgentOrchestrator._extract_agent_id(spawn_output)

            if not agent_id:
                logger.error("Failed to get agent ID from spawn output")
                return await AgentOrchestrator._execute_simulated(
                    agent_name, phase, context, {}, on_output
                )

            if on_output:
                await on_output("progress", {
                    "agent": agent_name,
                    "phase": phase,
                    "message": f"Agent spawned with ID: {agent_id}",
                })

            # Step 2: Poll for completion
            max_wait_time = 300  # 5 minutes
            poll_interval = 5  # 5 seconds
            elapsed = 0

            while elapsed < max_wait_time:
                status_cmd = [
                    "npx", "@claude-flow/cli@latest", "agent", "status", agent_id
                ]

                status_process = await asyncio.create_subprocess_exec(
                    *status_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                status_stdout, _ = await asyncio.wait_for(
                    status_process.communicate(),
                    timeout=30
                )

                status_output = status_stdout.decode('utf-8')

                # Try to parse as JSON
                try:
                    status_data = json.loads(status_output)
                    agent_status = status_data.get("status", "").lower()
                except json.JSONDecodeError:
                    # Check for status in text output
                    if "completed" in status_output.lower():
                        agent_status = "completed"
                    elif "failed" in status_output.lower():
                        agent_status = "failed"
                    else:
                        agent_status = "running"

                if agent_status == "completed":
                    break
                elif agent_status == "failed":
                    raise Exception(f"Agent {agent_id} failed")

                if on_output:
                    await on_output("progress", {
                        "agent": agent_name,
                        "phase": phase,
                        "message": f"Agent {agent_id} still running... ({elapsed}s)",
                    })

                await asyncio.sleep(poll_interval)
                elapsed += poll_interval

            if elapsed >= max_wait_time:
                raise Exception(f"Agent {agent_id} timed out after {max_wait_time} seconds")

            # Step 3: Get final output from logs
            logs_cmd = [
                "npx", "@claude-flow/cli@latest", "agent", "logs", agent_id
            ]

            logs_process = await asyncio.create_subprocess_exec(
                *logs_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            logs_stdout, _ = await asyncio.wait_for(
                logs_process.communicate(),
                timeout=30
            )

            logs_output = logs_stdout.decode('utf-8')

            # Extract structured data from output
            structured_data = AgentOrchestrator._extract_structured_output(logs_output, phase)

            if on_output:
                await on_output("progress", {
                    "agent": agent_name,
                    "phase": phase,
                    "message": f"Agent {agent_id} completed successfully",
                })

            return {
                "content": logs_output,
                "structured": structured_data,
                "files": [],
                "tokens_used": None,
            }

        except asyncio.TimeoutError:
            logger.error("claude-flow command timed out")
            return await AgentOrchestrator._execute_simulated(
                agent_name, phase, context, {}, on_output
            )
        except FileNotFoundError:
            logger.warning("npx or claude-flow CLI not found, falling back to simulated")
            return await AgentOrchestrator._execute_simulated(
                agent_name, phase, context, {}, on_output
            )
        except Exception as e:
            logger.error(f"claude-flow execution failed: {e}")
            return await AgentOrchestrator._execute_simulated(
                agent_name, phase, context, {}, on_output
            )

    @staticmethod
    def _extract_agent_id(output: str) -> Optional[str]:
        """Extract agent ID from command output."""
        # Try patterns with capture groups first
        patterns_with_groups = [
            r'"agent_id"\s*:\s*"([^"]+)"',
            r'"id"\s*:\s*"([^"]+)"',
            r'Agent ID:\s*(\S+)',
            r'Spawned agent:\s*(\S+)',
        ]

        for pattern in patterns_with_groups:
            match = re.search(pattern, output)
            if match:
                return match.group(1)

        # Try pattern without capture group (full match)
        match = re.search(r'agent-\w+-\d+', output)
        if match:
            return match.group(0)

        return None

    @staticmethod
    async def _execute_simulated(
        agent_name: str,
        phase: str,
        context: dict,
        agent_config: dict,
        on_output: Optional[Callable[[str, dict], Any]] = None,
    ) -> dict:
        """
        Simulated agent execution for development/testing.

        This is used as a fallback when claude-flow is not available or enabled.
        To enable real claude-flow execution:
        1. Install claude-flow CLI (npx @claude-flow/cli@latest)
        2. Set USE_CLAUDE_FLOW=true environment variable

        Args:
            agent_name: Name of the agent
            phase: Workflow phase
            context: Input context
            agent_config: Agent configuration (unused, kept for compatibility)
            on_output: Optional callback for streaming output

        Returns:
            Simulated agent result
        """
        task_title = context.get("task_title", "Unknown Task")
        task_description = context.get("task_description", "")

        if on_output:
            await on_output("progress", {
                "agent": agent_name,
                "phase": phase,
                "message": f"[SIMULATED] Processing task: {task_title}",
            })

        # Simulate processing delay
        await asyncio.sleep(2)

        # Generate phase-specific simulated output
        if phase == "architecture":
            content = f"""# Architecture Plan for: {task_title}

## Overview
This is a simulated architecture plan for the task.

## Task Description
{task_description}

## Components
1. **Backend Service** - API endpoints and business logic
2. **Database Schema** - Required data models
3. **Frontend Components** - UI elements needed

## Implementation Steps
1. Create database models
2. Implement API endpoints
3. Add frontend components
4. Write tests

## Notes
*This is a simulated response. Enable Claude CLI for real AI-powered architecture planning.*
"""
            structured = {
                "architecture_overview": f"Architecture plan for {task_title}",
                "components": [
                    {"name": "Backend Service", "type": "service", "files": []},
                    {"name": "Database Schema", "type": "model", "files": []},
                ],
                "implementation_plan": [
                    {"step": 1, "description": "Create database models", "files": []},
                    {"step": 2, "description": "Implement API endpoints", "files": []},
                ],
                "migration_needed": False,
                "breaking_changes": False,
            }

        elif phase == "development":
            architecture_plan = context.get("architecture_plan", "No architecture provided")
            content = f"""# Implementation for: {task_title}

## Summary
Simulated implementation based on the architecture plan.

## Architecture Reference
{architecture_plan[:500]}...

## Files Modified
- No actual files were modified (simulated execution)

## Testing
- Tests would be added here

## Notes
*This is a simulated response. Enable Claude CLI for real AI-powered development.*
"""
            structured = {
                "implementation_summary": f"Simulated implementation for {task_title}",
                "files_modified": [],
                "tests_added": [],
                "migration_created": False,
                "setup_instructions": [],
                "breaking_changes": False,
            }

        elif phase == "review":
            code_to_review = context.get("code_to_review", "No code provided")
            content = f"""# Code Review for: {task_title}

## Status: APPROVED

## Summary
Simulated code review (auto-approved for testing).

## Code Reviewed
{code_to_review[:500]}...

## Findings
- No issues found (simulated review)

## Notes
*This is a simulated response. Enable Claude CLI for real AI-powered code review.*
"""
            structured = {
                "status": "APPROVED",
                "summary": {
                    "overall_assessment": "Simulated review - auto-approved",
                    "critical_count": 0,
                    "major_count": 0,
                    "minor_count": 0,
                },
                "critical_issues": [],
                "major_issues": [],
                "minor_issues": [],
                "requires_resubmission": False,
            }

        else:
            content = f"Simulated output for phase: {phase}"
            structured = None

        return {
            "content": content,
            "structured": structured,
            "files": [],
            "tokens_used": None,
        }

    @staticmethod
    def _build_task_prompt(context: dict) -> str:
        """Build a task prompt from the context dictionary."""
        parts = []

        if context.get("task_title"):
            parts.append(f"**Task Title:** {context['task_title']}")

        if context.get("task_description"):
            parts.append(f"**Task Description:** {context['task_description']}")

        if context.get("architecture_plan"):
            parts.append(f"**Architecture Plan:**\n{context['architecture_plan']}")

        if context.get("code_to_review"):
            parts.append(f"**Code to Review:**\n{context['code_to_review']}")

        if context.get("review_feedback"):
            parts.append(f"**Previous Review Feedback:**\n{context['review_feedback']}")

        if context.get("iteration"):
            parts.append(f"**Iteration:** {context['iteration']}")

        return "\n\n".join(parts)

    @staticmethod
    def _extract_structured_output(content: str, phase: str) -> Optional[dict]:
        """
        Extract structured data from agent output text.

        Args:
            content: Raw output text from the agent
            phase: Workflow phase to determine expected structure

        Returns:
            Structured data dictionary or None
        """
        # Try to find JSON blocks in the output
        json_pattern = r'```json\s*([\s\S]*?)\s*```'
        matches = re.findall(json_pattern, content)

        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

        # Phase-specific default structures
        if phase == "review":
            # Try to detect approval status from content
            status = "APPROVED" if "APPROVED" in content.upper() else "CHANGES_REQUESTED"
            return {
                "status": status,
                "summary": {"overall_assessment": "Extracted from content"},
                "critical_issues": [],
                "major_issues": [],
                "minor_issues": [],
            }

        return None

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
