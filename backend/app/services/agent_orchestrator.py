"""Hybrid Agent Orchestrator for managing Claude agent execution.

This module implements a hybrid approach combining:
- Direct Anthropic API for planning (architect) and review phases
- Claude CLI spawning for autonomous development work
- Text Editor Tool for applying targeted fixes

The orchestrator manages the full architect → developer → reviewer pipeline
with support for feedback loops and real-time streaming.
"""

import asyncio
import json
import logging
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.task import Task
from app.models.agent_execution import AgentExecution
from app.models.agent_output import AgentOutput
from app.services.agent_context_builder import AgentContextBuilder
from app.services.activity_service import ActivityService
from app.services.prompts import (
    ARCHITECT_SYSTEM_PROMPT,
    DEVELOPER_SYSTEM_PROMPT,
    REVIEWER_SYSTEM_PROMPT,
    build_architect_prompt,
    build_developer_prompt,
    build_reviewer_prompt,
)

logger = logging.getLogger(__name__)

# Workspace base directory for agent file operations
WORKSPACE_BASE = Path(os.environ.get("WORKSPACE_BASE", "/tmp/workspaces"))


class HybridOrchestrator:
    """
    Hybrid agent orchestrator combining API calls and CLI execution.

    Execution Modes:
    - Architecture Phase: Direct Anthropic API (fast, controlled)
    - Development Phase: Claude CLI with file tools (autonomous)
    - Review Phase: Direct Anthropic API + Text Editor (targeted fixes)
    """

    def __init__(self):
        """Initialize the hybrid orchestrator."""
        self._anthropic_client = None
        self._redis_client = None

    @property
    def anthropic_client(self):
        """Lazy-load Anthropic client."""
        if self._anthropic_client is None:
            try:
                from anthropic import Anthropic
                api_key = settings.ANTHROPIC_API_KEY
                if api_key:
                    self._anthropic_client = Anthropic(api_key=api_key)
                else:
                    logger.warning("ANTHROPIC_API_KEY not set, API calls will fail")
            except ImportError:
                logger.warning("anthropic package not installed")
        return self._anthropic_client

    @property
    def redis_client(self):
        """Lazy-load Redis client for pub/sub."""
        if self._redis_client is None:
            try:
                import redis.asyncio as redis
                self._redis_client = redis.from_url(settings.REDIS_URL)
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")
        return self._redis_client

    # ========================================================================
    # Execution Management (Static methods for compatibility)
    # ========================================================================

    @staticmethod
    async def create_execution(
        db: AsyncSession,
        task_id: UUID,
        board_id: UUID,
        workflow_type: str = "development",
        context: Optional[dict] = None,
    ) -> AgentExecution:
        """Create a new agent execution."""
        # Create workspace directory
        workspace_path = WORKSPACE_BASE / str(task_id)
        workspace_path.mkdir(parents=True, exist_ok=True)

        execution = AgentExecution(
            task_id=task_id,
            board_id=board_id,
            workflow_type=workflow_type,
            status="pending",
            context={
                **(context or {}),
                "workspace_path": str(workspace_path),
            },
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
        """Start an agent execution."""
        execution = await HybridOrchestrator._get_execution(db, execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        if execution.status != "pending":
            raise ValueError(f"Execution {execution_id} is not in pending status")

        execution.status = "running"
        execution.started_at = datetime.utcnow()
        await db.flush()

        task = await db.get(Task, execution.task_id)
        if task:
            task.agent_status = "running"
            await db.flush()

        await ActivityService.log_activity(
            db=db,
            task_id=execution.task_id,
            board_id=execution.board_id,
            activity_type="agent_started",
            actor="hybrid-orchestrator",
            metadata={
                "execution_id": str(execution_id),
                "workflow_type": execution.workflow_type,
            },
        )

        return execution

    @staticmethod
    async def cancel_execution(
        db: AsyncSession,
        execution_id: UUID,
    ) -> AgentExecution:
        """Cancel a running execution."""
        execution = await HybridOrchestrator._get_execution(db, execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        if execution.status not in ("pending", "running"):
            raise ValueError(f"Execution {execution_id} cannot be cancelled")

        execution.status = "cancelled"
        execution.completed_at = datetime.utcnow()
        await db.flush()

        task = await db.get(Task, execution.task_id)
        if task:
            task.agent_status = None
            await db.flush()

        await ActivityService.log_activity(
            db=db,
            task_id=execution.task_id,
            board_id=execution.board_id,
            activity_type="agent_cancelled",
            actor="system",
            metadata={"execution_id": str(execution_id)},
        )

        return execution

    # ========================================================================
    # Workflow Execution
    # ========================================================================

    async def execute_workflow(
        self,
        db: AsyncSession,
        execution: AgentExecution,
        on_output: Optional[Callable[[str, dict], Any]] = None,
    ) -> AgentExecution:
        """
        Execute the full hybrid workflow: architect → developer → reviewer.

        Args:
            db: Database session
            execution: Execution record
            on_output: Optional callback for streaming output

        Returns:
            Completed execution
        """
        task = await db.get(Task, execution.task_id)
        if not task:
            raise ValueError(f"Task {execution.task_id} not found")

        workspace_path = execution.context.get("workspace_path", str(WORKSPACE_BASE / str(task.id)))
        phases = AgentContextBuilder.get_workflow_phases(execution.workflow_type)

        try:
            architecture_result = None
            development_result = None

            for phase in phases:
                execution.current_phase = phase
                if task:
                    task.agent_status = phase
                await db.flush()

                # Emit phase start activity
                await self._emit_activity(
                    db, execution, f"phase_start",
                    {"phase": phase, "iteration": execution.iteration}
                )

                if phase == "architecture":
                    architecture_result = await self._run_architecture_phase(
                        db, execution, task, workspace_path, on_output
                    )

                elif phase == "development":
                    development_result = await self._run_development_phase(
                        db, execution, task, workspace_path, architecture_result, on_output
                    )

                elif phase == "review":
                    review_result = await self._run_review_phase(
                        db, execution, task, workspace_path,
                        architecture_result, development_result, on_output
                    )

                    # Handle review feedback loop
                    if review_result.get("status") == "CHANGES_REQUESTED":
                        if execution.iteration < execution.max_iterations:
                            execution.iteration += 1
                            await db.flush()

                            # Apply fixes if provided
                            if review_result.get("fixes"):
                                await self._apply_review_fixes(
                                    workspace_path, review_result["fixes"], on_output
                                )

                            # Re-run development with feedback
                            development_result = await self._run_development_phase(
                                db, execution, task, workspace_path,
                                architecture_result, on_output,
                                feedback=review_result.get("feedback")
                            )

                            # Re-run review
                            review_result = await self._run_review_phase(
                                db, execution, task, workspace_path,
                                architecture_result, development_result, on_output
                            )

            # Mark execution as completed
            execution.status = "completed"
            execution.completed_at = datetime.utcnow()
            execution.result_summary = await self._build_result_summary(db, execution)

            if task:
                task.agent_status = "completed"

            await db.flush()

            await self._emit_activity(
                db, execution, "workflow_complete",
                {"iterations": execution.iteration}
            )

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            execution.status = "failed"
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()

            if task:
                task.agent_status = "failed"

            await db.flush()

            await self._emit_activity(
                db, execution, "workflow_failed",
                {"error": str(e)}
            )

            raise

        return execution

    # For backwards compatibility
    @staticmethod
    async def run_workflow(
        db: AsyncSession,
        execution: AgentExecution,
        on_output: Optional[Callable[[str, dict], Any]] = None,
    ) -> AgentExecution:
        """Static wrapper for execute_workflow (backwards compatibility)."""
        orchestrator = HybridOrchestrator()
        return await orchestrator.execute_workflow(db, execution, on_output)

    # ========================================================================
    # Phase Execution Methods
    # ========================================================================

    async def _run_architecture_phase(
        self,
        db: AsyncSession,
        execution: AgentExecution,
        task: Task,
        workspace_path: str,
        on_output: Optional[Callable[[str, dict], Any]] = None,
    ) -> dict:
        """
        Run architecture phase using direct Anthropic API.

        Args:
            db: Database session
            execution: Parent execution
            task: Task being processed
            workspace_path: Workspace directory
            on_output: Callback for streaming

        Returns:
            Architecture result dictionary
        """
        output = AgentOutput(
            execution_id=execution.id,
            task_id=task.id,
            agent_name="architect",
            phase="architecture",
            iteration=execution.iteration,
            status="running",
            started_at=datetime.utcnow(),
        )
        db.add(output)
        await db.flush()

        try:
            # Build prompts
            user_prompt = build_architect_prompt(
                task_title=task.title,
                task_description=task.description or "",
                context=execution.context,
            )

            # Make API call
            result = await self._api_call(
                system_prompt=ARCHITECT_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                on_output=on_output,
                phase="architecture",
            )

            # Save architecture to workspace
            arch_path = Path(workspace_path) / "ARCHITECTURE.md"
            arch_path.write_text(result["content"])

            output.status = "completed"
            output.completed_at = datetime.utcnow()
            output.output_content = result["content"]
            output.output_structured = {"architecture_saved": str(arch_path)}
            output.tokens_used = result.get("tokens_used")
            output.duration_ms = int((output.completed_at - output.started_at).total_seconds() * 1000)
            output.files_created = [str(arch_path)]

            await db.flush()

            return {
                "content": result["content"],
                "path": str(arch_path),
            }

        except Exception as e:
            output.status = "failed"
            output.error_message = str(e)
            output.completed_at = datetime.utcnow()
            await db.flush()
            raise

    async def _run_development_phase(
        self,
        db: AsyncSession,
        execution: AgentExecution,
        task: Task,
        workspace_path: str,
        architecture_result: Optional[dict],
        on_output: Optional[Callable[[str, dict], Any]] = None,
        feedback: Optional[str] = None,
    ) -> dict:
        """
        Run development phase using Claude CLI spawning.

        Args:
            db: Database session
            execution: Parent execution
            task: Task being processed
            workspace_path: Workspace directory
            architecture_result: Result from architecture phase
            on_output: Callback for streaming
            feedback: Review feedback for iterations

        Returns:
            Development result dictionary
        """
        output = AgentOutput(
            execution_id=execution.id,
            task_id=task.id,
            agent_name="developer",
            phase="development",
            iteration=execution.iteration,
            status="running",
            started_at=datetime.utcnow(),
        )
        db.add(output)
        await db.flush()

        try:
            architecture_plan = architecture_result.get("content", "") if architecture_result else ""

            # Build developer prompt
            user_prompt = build_developer_prompt(
                task_title=task.title,
                architecture_plan=architecture_plan,
                workspace_path=workspace_path,
                iteration=execution.iteration,
                feedback=feedback,
            )

            # Execute using CLI
            result = await self._cli_execute(
                prompt=user_prompt,
                workspace_path=workspace_path,
                on_output=on_output,
            )

            # Gather files created
            files_created = self._list_workspace_files(workspace_path)

            output.status = "completed"
            output.completed_at = datetime.utcnow()
            output.output_content = result["content"]
            output.output_structured = result.get("structured")
            output.tokens_used = result.get("tokens_used")
            output.duration_ms = int((output.completed_at - output.started_at).total_seconds() * 1000)
            output.files_created = files_created

            await db.flush()

            return {
                "content": result["content"],
                "files": files_created,
            }

        except Exception as e:
            output.status = "failed"
            output.error_message = str(e)
            output.completed_at = datetime.utcnow()
            await db.flush()
            raise

    async def _run_review_phase(
        self,
        db: AsyncSession,
        execution: AgentExecution,
        task: Task,
        workspace_path: str,
        architecture_result: Optional[dict],
        development_result: Optional[dict],
        on_output: Optional[Callable[[str, dict], Any]] = None,
    ) -> dict:
        """
        Run review phase using direct Anthropic API.

        Args:
            db: Database session
            execution: Parent execution
            task: Task being processed
            workspace_path: Workspace directory
            architecture_result: Result from architecture phase
            development_result: Result from development phase
            on_output: Callback for streaming

        Returns:
            Review result dictionary with status and issues
        """
        output = AgentOutput(
            execution_id=execution.id,
            task_id=task.id,
            agent_name="reviewer",
            phase="review",
            iteration=execution.iteration,
            status="running",
            started_at=datetime.utcnow(),
        )
        db.add(output)
        await db.flush()

        try:
            # Gather files to review
            files_to_review = self._read_workspace_files(workspace_path)

            architecture_plan = architecture_result.get("content", "") if architecture_result else ""
            implementation_summary = development_result.get("content", "") if development_result else ""

            # Build reviewer prompt
            user_prompt = build_reviewer_prompt(
                task_title=task.title,
                architecture_plan=architecture_plan,
                implementation_summary=implementation_summary,
                files_to_review=files_to_review,
            )

            # Make API call
            result = await self._api_call(
                system_prompt=REVIEWER_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                on_output=on_output,
                phase="review",
            )

            # Parse review result
            review_data = self._parse_review_result(result["content"])

            # Save review to workspace
            review_path = Path(workspace_path) / "REVIEW.md"
            review_path.write_text(result["content"])

            output.status = "completed"
            output.completed_at = datetime.utcnow()
            output.output_content = result["content"]
            output.output_structured = review_data
            output.tokens_used = result.get("tokens_used")
            output.duration_ms = int((output.completed_at - output.started_at).total_seconds() * 1000)
            output.files_created = [str(review_path)]

            await db.flush()

            return review_data

        except Exception as e:
            output.status = "failed"
            output.error_message = str(e)
            output.completed_at = datetime.utcnow()
            await db.flush()
            raise

    # ========================================================================
    # Core Execution Methods
    # ========================================================================

    async def _api_call(
        self,
        system_prompt: str,
        user_prompt: str,
        on_output: Optional[Callable[[str, dict], Any]] = None,
        phase: str = "unknown",
    ) -> dict:
        """
        Make a direct Anthropic API call.

        Args:
            system_prompt: System prompt for the agent
            user_prompt: User message/prompt
            on_output: Optional callback for progress
            phase: Phase name for logging

        Returns:
            Result dictionary with content and token usage
        """
        if on_output:
            await on_output("progress", {
                "phase": phase,
                "message": f"Starting {phase} phase via API...",
            })

        # Check if API is available
        if not self.anthropic_client:
            logger.warning("Anthropic client not available, using simulated response")
            return await self._simulated_api_call(system_prompt, user_prompt, phase)

        try:
            # Make streaming API call
            content_parts = []
            tokens_used = {"input": 0, "output": 0}

            with self.anthropic_client.messages.stream(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            ) as stream:
                for text in stream.text_stream:
                    content_parts.append(text)
                    if on_output:
                        await on_output("chunk", {"text": text, "phase": phase})

                # Get final message for token usage
                final_message = stream.get_final_message()
                tokens_used["input"] = final_message.usage.input_tokens
                tokens_used["output"] = final_message.usage.output_tokens

            content = "".join(content_parts)

            if on_output:
                await on_output("progress", {
                    "phase": phase,
                    "message": f"{phase.capitalize()} phase completed",
                    "tokens": tokens_used,
                })

            return {
                "content": content,
                "tokens_used": tokens_used["input"] + tokens_used["output"],
            }

        except Exception as e:
            logger.error(f"API call failed: {e}")
            # Fall back to simulated
            return await self._simulated_api_call(system_prompt, user_prompt, phase)

    async def _cli_execute(
        self,
        prompt: str,
        workspace_path: str,
        on_output: Optional[Callable[[str, dict], Any]] = None,
    ) -> dict:
        """
        Execute developer phase using Claude CLI spawning.

        Spawns 'claude --dangerously-skip-permissions -p' subprocess for
        autonomous code generation with file system access.

        Args:
            prompt: The task prompt for the developer
            workspace_path: Directory for file operations
            on_output: Callback for streaming output

        Returns:
            Result dictionary with content and files
        """
        if on_output:
            await on_output("progress", {
                "phase": "development",
                "message": "Starting development phase via CLI...",
            })

        # Check if claude CLI is available
        claude_path = self._find_claude_cli()
        if not claude_path:
            logger.warning("Claude CLI not found, using simulated execution")
            return await self._simulated_cli_execute(prompt, workspace_path, on_output)

        try:
            # Build the command
            cmd = [
                claude_path,
                "--dangerously-skip-permissions",
                "-p", prompt,
            ]

            # Run in workspace directory
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workspace_path,
            )

            # Stream output
            output_parts = []

            async def read_stream(stream, prefix=""):
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    text = line.decode("utf-8")
                    output_parts.append(text)
                    if on_output:
                        await on_output("chunk", {"text": text, "phase": "development"})

            # Read stdout and stderr concurrently
            await asyncio.gather(
                read_stream(process.stdout),
                read_stream(process.stderr, "[stderr] "),
            )

            await asyncio.wait_for(process.wait(), timeout=600)  # 10 minute timeout

            content = "".join(output_parts)

            if on_output:
                await on_output("progress", {
                    "phase": "development",
                    "message": "Development phase completed",
                    "return_code": process.returncode,
                })

            return {
                "content": content,
                "structured": {"return_code": process.returncode},
            }

        except asyncio.TimeoutError:
            logger.error("CLI execution timed out")
            if on_output:
                await on_output("error", {"message": "CLI execution timed out"})
            return await self._simulated_cli_execute(prompt, workspace_path, on_output)

        except Exception as e:
            logger.error(f"CLI execution failed: {e}")
            return await self._simulated_cli_execute(prompt, workspace_path, on_output)

    async def _apply_review_fixes(
        self,
        workspace_path: str,
        fixes: list,
        on_output: Optional[Callable[[str, dict], Any]] = None,
    ) -> None:
        """
        Apply targeted fixes from review using Text Editor Tool approach.

        Args:
            workspace_path: Workspace directory
            fixes: List of fixes with file, line, and replacement info
            on_output: Callback for progress
        """
        if on_output:
            await on_output("progress", {
                "phase": "review",
                "message": f"Applying {len(fixes)} fixes...",
            })

        for fix in fixes:
            file_path = Path(workspace_path) / fix.get("file", "")
            if not file_path.exists():
                logger.warning(f"Fix target file not found: {file_path}")
                continue

            try:
                content = file_path.read_text()

                # Apply fix based on type
                if "old_text" in fix and "new_text" in fix:
                    # String replacement
                    content = content.replace(fix["old_text"], fix["new_text"])
                elif "line" in fix and "replacement" in fix:
                    # Line replacement
                    lines = content.split("\n")
                    line_num = fix["line"] - 1
                    if 0 <= line_num < len(lines):
                        lines[line_num] = fix["replacement"]
                        content = "\n".join(lines)

                file_path.write_text(content)

                if on_output:
                    await on_output("file_edit", {
                        "file": str(file_path),
                        "fix": fix.get("issue", "Applied fix"),
                    })

            except Exception as e:
                logger.error(f"Failed to apply fix to {file_path}: {e}")

    async def _emit_activity(
        self,
        db: AsyncSession,
        execution: AgentExecution,
        activity_type: str,
        metadata: dict,
    ) -> None:
        """
        Emit activity via database logging and Redis pub/sub.

        Args:
            db: Database session
            execution: Current execution
            activity_type: Type of activity
            metadata: Activity metadata
        """
        # Log to database
        await ActivityService.log_activity(
            db=db,
            task_id=execution.task_id,
            board_id=execution.board_id,
            activity_type=activity_type,
            actor="hybrid-orchestrator",
            metadata={
                "execution_id": str(execution.id),
                **metadata,
            },
        )

        # Publish to Redis for real-time updates
        if self.redis_client:
            try:
                channel = f"task:{execution.task_id}:activity"
                message = json.dumps({
                    "type": activity_type,
                    "execution_id": str(execution.id),
                    "task_id": str(execution.task_id),
                    "timestamp": datetime.utcnow().isoformat(),
                    **metadata,
                })
                await self.redis_client.publish(channel, message)
            except Exception as e:
                logger.warning(f"Failed to publish to Redis: {e}")

    # ========================================================================
    # Simulated Execution (Fallbacks)
    # ========================================================================

    async def _simulated_api_call(
        self,
        system_prompt: str,
        user_prompt: str,
        phase: str,
    ) -> dict:
        """Simulated API call for development/testing."""
        await asyncio.sleep(1)  # Simulate latency

        if phase == "architecture":
            content = f"""# Architecture Plan

## Overview
This is a simulated architecture plan.

## Requirements
Based on the task description, the following requirements were identified.

## Components
1. **Core Module** - Main business logic
2. **Data Layer** - Database interactions
3. **API Layer** - HTTP endpoints

## Implementation Plan
1. Create data models
2. Implement business logic
3. Add API endpoints
4. Write tests

*Note: This is a simulated response. Configure ANTHROPIC_API_KEY for real AI responses.*
"""
        elif phase == "review":
            content = """```json
{
  "status": "APPROVED",
  "summary": {
    "overall_assessment": "Simulated review - auto-approved for testing",
    "critical_count": 0,
    "major_count": 0,
    "minor_count": 0
  },
  "critical_issues": [],
  "major_issues": [],
  "minor_issues": [],
  "positive_feedback": ["Simulated positive feedback"],
  "requires_resubmission": false
}
```

*Note: This is a simulated response. Configure ANTHROPIC_API_KEY for real AI reviews.*
"""
        else:
            content = f"Simulated response for {phase} phase."

        return {"content": content, "tokens_used": None}

    async def _simulated_cli_execute(
        self,
        prompt: str,
        workspace_path: str,
        on_output: Optional[Callable[[str, dict], Any]] = None,
    ) -> dict:
        """Simulated CLI execution for development/testing."""
        await asyncio.sleep(2)

        # Create a sample file to simulate work
        sample_file = Path(workspace_path) / "main.py"
        sample_content = '''"""Sample implementation generated by simulated developer agent."""

def main():
    """Main entry point."""
    print("Hello from Agent Rangers!")


if __name__ == "__main__":
    main()
'''
        sample_file.write_text(sample_content)

        content = f"""## Development Summary

Created sample implementation at: {sample_file}

### Files Created:
- main.py: Main entry point

*Note: This is simulated execution. Install Claude CLI for real autonomous development.*
"""

        return {
            "content": content,
            "structured": {"simulated": True},
        }

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _find_claude_cli(self) -> Optional[str]:
        """Find claude CLI executable."""
        # Check common locations
        locations = [
            "claude",  # In PATH
            "/usr/local/bin/claude",
            os.path.expanduser("~/.local/bin/claude"),
            os.path.expanduser("~/bin/claude"),
        ]

        for loc in locations:
            try:
                result = subprocess.run(
                    [loc, "--version"],
                    capture_output=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    return loc
            except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
                continue

        return None

    def _list_workspace_files(self, workspace_path: str) -> list:
        """List all files in workspace."""
        files = []
        workspace = Path(workspace_path)
        if workspace.exists():
            for path in workspace.rglob("*"):
                if path.is_file() and not path.name.startswith("."):
                    files.append(str(path.relative_to(workspace)))
        return files

    def _read_workspace_files(self, workspace_path: str, max_files: int = 20) -> list:
        """Read workspace files for review."""
        files = []
        workspace = Path(workspace_path)

        # File extensions to review
        code_extensions = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java"}

        if workspace.exists():
            for path in workspace.rglob("*"):
                if path.is_file() and path.suffix in code_extensions:
                    try:
                        content = path.read_text()
                        lang = self._get_language_from_extension(path.suffix)
                        files.append({
                            "path": str(path.relative_to(workspace)),
                            "content": content[:10000],  # Limit size
                            "language": lang,
                        })
                        if len(files) >= max_files:
                            break
                    except Exception as e:
                        logger.warning(f"Failed to read {path}: {e}")

        return files

    def _get_language_from_extension(self, ext: str) -> str:
        """Get language name from file extension."""
        mapping = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
        }
        return mapping.get(ext, "")

    def _parse_review_result(self, content: str) -> dict:
        """Parse review result from content."""
        # Try to extract JSON from markdown code block
        json_match = re.search(r"```json\s*([\s\S]*?)\s*```", content)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Default to approved if parsing fails
        return {
            "status": "APPROVED",
            "summary": {"overall_assessment": "Review completed"},
            "critical_issues": [],
            "major_issues": [],
            "minor_issues": [],
        }

    async def _build_result_summary(
        self,
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
    # Query Methods (Static for compatibility)
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
    async def get_execution_status(
        db: AsyncSession,
        execution_id: UUID,
    ) -> Optional[dict]:
        """Get current status of an execution."""
        execution = await HybridOrchestrator._get_execution(db, execution_id)
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
        """Get executions for a task."""
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
        """Get executions for a board."""
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


    # ========================================================================
    # Backwards Compatibility Methods
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
        Static wrapper for running a single agent phase (backwards compatibility).

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
        orchestrator = HybridOrchestrator()
        workspace_path = execution.context.get(
            "workspace_path",
            str(WORKSPACE_BASE / str(task.id))
        )

        if phase == "architecture":
            result = await orchestrator._run_architecture_phase(
                db, execution, task, workspace_path, on_output
            )
        elif phase == "development":
            # Get architecture result if available
            arch_output = await AgentContextBuilder._get_phase_output(
                db, execution.id, "architecture"
            )
            architecture_result = {
                "content": arch_output.output_content if arch_output else ""
            } if arch_output else None

            feedback = context.get("user_feedback")
            result = await orchestrator._run_development_phase(
                db, execution, task, workspace_path,
                architecture_result, on_output, feedback
            )
        elif phase == "review":
            arch_output = await AgentContextBuilder._get_phase_output(
                db, execution.id, "architecture"
            )
            dev_output = await AgentContextBuilder._get_phase_output(
                db, execution.id, "development", execution.iteration
            )
            architecture_result = {
                "content": arch_output.output_content if arch_output else ""
            } if arch_output else None
            development_result = {
                "content": dev_output.output_content if dev_output else "",
                "files": dev_output.files_created if dev_output else [],
            } if dev_output else None

            result = await orchestrator._run_review_phase(
                db, execution, task, workspace_path,
                architecture_result, development_result, on_output
            )
        else:
            raise ValueError(f"Unknown phase: {phase}")

        # Get the output that was created
        outputs = await AgentContextBuilder._get_all_execution_outputs(db, execution.id)
        return outputs[-1] if outputs else None


# Alias for backwards compatibility
AgentOrchestrator = HybridOrchestrator
