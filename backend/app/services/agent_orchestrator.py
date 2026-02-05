"""Hybrid Agent Orchestrator for managing Claude agent execution.

This module implements a hybrid approach combining:
- Provider Abstraction Layer for flexible AI backend selection
- Direct API calls for planning (architect) and review phases
- Claude CLI spawning for autonomous development work

Supported providers:
- OAuth (Claude Code CLI) - Uses Max subscription, FREE!
- API (Anthropic) - Pay-as-you-go
- Local (Ollama) - Completely free, self-hosted

The orchestrator manages the full architect → developer → reviewer pipeline
with support for feedback loops and real-time streaming.
"""

import asyncio
import json
import logging
import os
import re
import shlex
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
from app.models.board import Board
from app.models.agent_execution import AgentExecution
from app.models.agent_output import AgentOutput
from app.services.agent_context_builder import AgentContextBuilder
from app.services.activity_service import ActivityService
from app.services.file_storage import file_storage
from app.api.websocket import manager as ws_manager
from app.services.prompts import (
    ARCHITECT_SYSTEM_PROMPT,
    DEVELOPER_SYSTEM_PROMPT,
    REVIEWER_SYSTEM_PROMPT,
    build_architect_prompt,
    build_developer_prompt,
    build_reviewer_prompt,
)
from app.providers import ProviderFactory, Message, Role

logger = logging.getLogger(__name__)

# Workspace base directory for agent file operations
WORKSPACE_BASE = Path(os.environ.get("WORKSPACE_BASE", "/tmp/workspaces"))


class HybridOrchestrator:
    """
    Hybrid agent orchestrator combining Provider Abstraction Layer with CLI execution.

    Execution Modes:
    - Architecture Phase: Provider (OAuth/API/Local)
    - Development Phase: Claude CLI with file tools (autonomous)
    - Review Phase: Provider (OAuth/API/Local)
    
    Provider Types:
    - oauth (claude-code): Uses Claude Max subscription - FREE!
    - api (anthropic): Pay-as-you-go API
    - local (ollama): Self-hosted, completely free
    """

    def __init__(self):
        """Initialize the hybrid orchestrator with provider support."""
        self._providers = {}
        self._redis_client = None
        self._providers_config = settings.get_providers_config()
        
        logger.info(f"Orchestrator initialized with provider mode: {settings.AI_PROVIDER_MODE}")

    def _get_provider(self, role: str = "default"):
        """Get or create a provider for the given role."""
        if role not in self._providers:
            self._providers[role] = ProviderFactory.create_for_role(
                role, self._providers_config
            )
            logger.info(f"Created provider for {role}: {self._providers[role]}")
        return self._providers[role]

    def _has_oauth_credentials(self) -> bool:
        """Check if OAuth credentials exist in Claude CLI config."""
        return settings._has_oauth()

    def _should_use_cli_for_all_phases(self) -> bool:
        """Determine if CLI should be used for all phases."""
        # Check if using OAuth provider mode
        provider_mode = settings.AI_PROVIDER_MODE.lower()
        
        if provider_mode == "oauth":
            return True
        elif provider_mode == "api":
            return False
        elif provider_mode == "local":
            return False
        else:  # auto
            # Use CLI if OAuth is available (it's free with Max!)
            if self._has_oauth_credentials():
                logger.info("OAuth credentials found - using Claude CLI for all phases (FREE with Max!)")
                return True
            return False

    @property
    def anthropic_client(self):
        """Lazy-load Anthropic client (API key auth only)."""
        if self._anthropic_client is None:
            try:
                from anthropic import Anthropic
                
                api_key = settings.ANTHROPIC_API_KEY
                
                if api_key:
                    logger.info("Using Anthropic API key authentication")
                    self._anthropic_client = Anthropic(api_key=api_key)
                else:
                    # No API key - check if we should use CLI instead
                    if self._has_oauth_credentials():
                        logger.info(
                            "No API key set but OAuth credentials found. "
                            "Will use Claude CLI for API calls."
                        )
                    else:
                        logger.warning(
                            "No Anthropic API key set and no OAuth credentials. "
                            "API calls will use simulated responses."
                        )
                    
            except ImportError:
                logger.warning("anthropic package not installed")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")
                
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

        # Broadcast execution started via WebSocket
        asyncio.create_task(
            ws_manager.broadcast(
                str(execution.board_id),
                {
                    "type": "execution_started",
                    "payload": {
                        "execution_id": str(execution.id),
                        "task_id": str(execution.task_id),
                        "board_id": str(execution.board_id),
                        "status": execution.status,
                        "workflow_type": execution.workflow_type,
                        "current_phase": execution.current_phase,
                    },
                },
            )
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
        
        # Load repository info from info.json and determine effective working directory
        effective_repo_path = await self._get_effective_working_directory(
            db, task, execution, workspace_path
        )
        
        # Add repository path to execution context for all phases
        if effective_repo_path != workspace_path:
            execution.context["repository_path"] = effective_repo_path
            logger.info(f"Using repository path: {effective_repo_path}")

        try:
            architecture_result = None
            development_result = None

            # Check if a previous plan should be loaded
            plan_execution_id = execution.context.get("plan_execution_id")
            if plan_execution_id and "architecture" not in phases:
                # Load plan from previous execution
                architecture_result = await self._load_plan_from_execution(
                    db, plan_execution_id
                )
                if architecture_result:
                    logger.info(f"Loaded plan from execution {plan_execution_id}")
                else:
                    logger.warning(f"Could not load plan from execution {plan_execution_id}")

            for phase in phases:
                execution.current_phase = phase
                if task:
                    task.agent_status = phase
                await db.flush()

                # Broadcast execution updated via WebSocket (phase changed)
                asyncio.create_task(
                    ws_manager.broadcast(
                        str(execution.board_id),
                        {
                            "type": "execution_updated",
                            "payload": {
                                "execution_id": str(execution.id),
                                "task_id": str(execution.task_id),
                                "board_id": str(execution.board_id),
                                "status": execution.status,
                                "current_phase": execution.current_phase,
                                "iteration": execution.iteration,
                            },
                        },
                    )
                )

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

            # Broadcast execution completed via WebSocket
            asyncio.create_task(
                ws_manager.broadcast(
                    str(execution.board_id),
                    {
                        "type": "execution_completed",
                        "payload": {
                            "execution_id": str(execution.id),
                            "task_id": str(execution.task_id),
                            "board_id": str(execution.board_id),
                            "status": execution.status,
                            "current_phase": execution.current_phase,
                            "iteration": execution.iteration,
                            "result_summary": execution.result_summary,
                        },
                    },
                )
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

            # Broadcast execution failed via WebSocket
            asyncio.create_task(
                ws_manager.broadcast(
                    str(execution.board_id),
                    {
                        "type": "execution_completed",
                        "payload": {
                            "execution_id": str(execution.id),
                            "task_id": str(execution.task_id),
                            "board_id": str(execution.board_id),
                            "status": execution.status,
                            "current_phase": execution.current_phase,
                            "error_message": execution.error_message,
                        },
                    },
                )
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
        Run architecture phase using Claude CLI for codebase exploration.

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
            agent_name="planner",
            phase="architecture",
            iteration=execution.iteration,
            status="running",
            started_at=datetime.utcnow(),
        )
        db.add(output)
        await db.flush()

        try:
            # Determine effective working directory
            effective_cwd = await self._get_effective_working_directory(
                db, task, execution, workspace_path
            )

            # Build architecture prompt for CLI exploration
            arch_prompt = self._build_cli_architect_prompt(
                task_title=task.title,
                task_description=task.description or "",
                context=execution.context,
            )

            if on_output:
                await on_output("progress", {
                    "phase": "architecture",
                    "message": "Starting architecture phase via Claude CLI...",
                })

            # Execute Claude CLI in the PROJECT directory (so it can explore files)
            # but we'll save the output to WORKSPACE (to not pollute the project)
            arch_content = await self._run_claude_cli_simple(
                prompt=arch_prompt,
                workspace_path=effective_cwd,  # Run in project dir to explore codebase
                on_output=on_output,
            )

            # Save architecture to WORKSPACE (not project dir)
            # This prevents dumping temp files into the actual repository
            short_summary = self._generate_short_filename(task.title)
            arch_path = Path(workspace_path) / f"plan-{short_summary}.md"
            arch_path.write_text(arch_content)

            output.status = "completed"
            output.completed_at = datetime.utcnow()
            output.output_content = arch_content
            output.output_structured = {
                "architecture_saved": str(arch_path),
                "project_explored": effective_cwd,
            }
            output.duration_ms = int((output.completed_at - output.started_at).total_seconds() * 1000)
            output.files_created = [str(arch_path)]

            await db.flush()

            if on_output:
                await on_output("progress", {
                    "phase": "architecture",
                    "message": "Architecture phase completed",
                })

            return {
                "content": arch_content,
                "path": str(arch_path),
            }

        except Exception as e:
            logger.error(f"Architecture phase failed: {e}")
            output.status = "failed"
            output.error_message = str(e)
            output.completed_at = datetime.utcnow()
            await db.flush()
            raise

    async def _run_claude_cli_simple(
        self,
        prompt: str,
        workspace_path: str,
        on_output: Optional[Callable[[str, dict], Any]] = None,
        timeout: int = 300,
    ) -> str:
        """
        Run Claude CLI using simple subprocess (no PTY).
        
        Uses 'script' command to provide a pseudo-terminal which Claude CLI requires.
        
        Args:
            prompt: The prompt to send to Claude
            workspace_path: Working directory
            on_output: Optional progress callback
            timeout: Timeout in seconds
            
        Returns:
            The CLI output content
        """
        claude_path = self._find_claude_cli()
        if not claude_path:
            raise RuntimeError("Claude CLI not found")

        logger.info(f"Running Claude CLI in {workspace_path}")

        # Use 'script' to provide PTY - this is more reliable than os.fork/pty
        # script -q -c 'command' /dev/null runs command with PTY and discards typescript
        cmd = [
            "script", "-q", "-c",
            f"{claude_path} --dangerously-skip-permissions -p {shlex.quote(prompt)} --output-format text",
            "/dev/null"
        ]

        env = {
            **os.environ,
            "CLAUDE_CONFIG_DIR": settings.CLAUDE_CONFIG_DIR,
        }

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workspace_path,
                env=env,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='replace')
                logger.error(f"Claude CLI failed with code {process.returncode}: {error_msg}")
                raise RuntimeError(f"Claude CLI failed: {error_msg}")

            content = stdout.decode('utf-8', errors='replace')
            
            # Clean up ANSI escape codes and control characters
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            content = ansi_escape.sub('', content)
            content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', content)

            logger.info(f"Claude CLI completed, output length: {len(content)}")
            return content.strip()

        except asyncio.TimeoutError:
            logger.error(f"Claude CLI timed out after {timeout}s")
            raise RuntimeError(f"Claude CLI timed out after {timeout}s")
    
    def _generate_short_filename(self, title: str, max_length: int = 30) -> str:
        """
        Generate a short filename-safe slug from a title.
        
        Args:
            title: The task title
            max_length: Maximum length of the slug
            
        Returns:
            A lowercase, hyphenated slug
        """
        import re
        # Convert to lowercase and replace spaces/special chars with hyphens
        slug = re.sub(r'[^a-zA-Z0-9]+', '-', title.lower())
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        # Truncate to max length, but don't cut in the middle of a word
        if len(slug) > max_length:
            slug = slug[:max_length].rsplit('-', 1)[0]
        return slug or 'untitled'

    def _build_cli_architect_prompt(
        self,
        task_title: str,
        task_description: str,
        context: dict = None,
    ) -> str:
        """
        Build a prompt for Claude CLI to explore codebase and create architecture.

        Args:
            task_title: Title of the task
            task_description: Full task description
            context: Optional additional context

        Returns:
            Formatted prompt for Claude CLI
        """
        prompt_parts = [
            "# Architecture Planning Task",
            "",
            f"## Task: {task_title}",
            "",
            "## Description",
            task_description or "No description provided.",
            "",
        ]

        if context:
            if context.get("repository_path"):
                prompt_parts.extend([
                    "## Repository",
                    f"Working in: `{context['repository_path']}`",
                    "",
                ])
            
            if context.get("technology_stack"):
                prompt_parts.extend([
                    "## Known Technologies",
                    f"{', '.join(context['technology_stack'])}",
                    "",
                ])

        prompt_parts.extend([
            "## Your Task",
            "",
            "1. **Explore the codebase** - Read relevant files to understand the project structure, patterns, and conventions",
            "2. **Analyze requirements** - Break down the task into clear, actionable requirements", 
            "3. **Create architecture plan** - Output a detailed plan that fits the existing codebase",
            "",
            "## Output Requirements",
            "",
            "**DO NOT create or modify any files.** Just output your architecture plan as text.",
            "",
            "Your output should include:",
            "- Overview of the solution approach",
            "- Requirements analysis (functional & non-functional)",
            "- Component design with clear responsibilities",
            "- Data model changes (if any)",
            "- Step-by-step implementation plan",
            "- Technical decisions and rationale",
            "",
            "**Important:** Base your architecture on the ACTUAL codebase structure you discover, not assumptions.",
            "Read existing code to understand patterns, naming conventions, and project organization.",
            "",
            "Start by exploring the project structure and key files, then output your plan.",
        ])

        return "\n".join(prompt_parts)

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

            # Determine effective working directory (info.json > board > default)
            effective_cwd = await self._get_effective_working_directory(
                db, task, execution, workspace_path
            )

            # Get branch info and checkout if needed
            branch_info = await self._get_task_branch(
                board_id=str(execution.board_id),
                task_id=str(task.id),
            )
            checkout_result = None
            if branch_info and branch_info.get("name"):
                branch_source = branch_info.get("source", "default")
                checkout_result = self._checkout_branch(
                    repo_path=effective_cwd, 
                    branch_name=branch_info["name"],
                    source=branch_source,
                    create_if_missing=(branch_source == "task_text"),  # Only create if explicitly mentioned
                )
                if checkout_result.get("success"):
                    if checkout_result.get("created"):
                        logger.info(f"Created and working on NEW branch: {branch_info['name']}")
                    else:
                        logger.info(f"Working on branch: {branch_info['name']} (source: {branch_source})")
                else:
                    logger.warning(f"Failed to checkout branch {branch_info['name']}, continuing on current branch")

            # Capture git state BEFORE development
            pre_git_state = self._capture_git_state(effective_cwd)
            logger.info(f"Pre-development git state: is_repo={pre_git_state.get('is_git_repo')}")

            # Build developer prompt
            user_prompt = build_developer_prompt(
                task_title=task.title,
                architecture_plan=architecture_plan,
                workspace_path=effective_cwd,
                iteration=execution.iteration,
                feedback=feedback,
            )

            # Execute using CLI with effective working directory and streaming support
            result = await self._cli_execute(
                prompt=user_prompt,
                workspace_path=effective_cwd,
                on_output=on_output,
                execution_id=execution.id,
                task_id=task.id,
                board_id=execution.board_id,
            )

            # Get ACTUAL files changed via git diff (comparing to pre-state)
            git_changes = self._get_git_changed_files(effective_cwd, pre_git_state)
            
            # Use git-tracked changes if available, otherwise fall back to listing files
            if git_changes.get("is_git_repo") and not git_changes.get("error"):
                # Convert relative paths to absolute paths for file viewing
                relative_files = git_changes.get("all_changed", [])
                files_created = [os.path.join(effective_cwd, f) for f in relative_files]
                
                # Also update git_changes with absolute paths for frontend
                git_changes["created_absolute"] = [os.path.join(effective_cwd, f) for f in git_changes.get("created", [])]
                git_changes["modified_absolute"] = [os.path.join(effective_cwd, f) for f in git_changes.get("modified", [])]
                git_changes["working_directory"] = effective_cwd
                
                logger.info(f"Git tracked changes: {len(files_created)} files - created: {len(git_changes.get('created', []))}, modified: {len(git_changes.get('modified', []))}")
                
                # Auto-commit changes after development completes
                commit_result = self._auto_commit_changes(
                    path=effective_cwd,
                    task_id=str(task.id),
                    task_title=task.title,
                    execution_id=str(execution.id),
                    git_changes=git_changes,
                )
                if commit_result.get("committed"):
                    logger.info(f"Auto-committed: {commit_result.get('commit_hash', 'unknown')}")
                    git_changes["commit"] = commit_result
                else:
                    logger.info(f"Auto-commit skipped: {commit_result.get('reason', 'unknown')}")
                    git_changes["commit"] = commit_result
            else:
                # Fall back to listing workspace files if not a git repo
                files_created = self._list_workspace_files(effective_cwd)
                logger.info(f"Non-git fallback: listing {len(files_created)} workspace files")

            output.status = "completed"
            output.completed_at = datetime.utcnow()
            output.output_content = result["content"]
            output.output_structured = {
                **(result.get("structured") or {}),
                "git_changes": git_changes,  # Store detailed git change info including commit
                "branch": {
                    "name": branch_info.get("name") if branch_info else None,
                    "source": branch_info.get("source") if branch_info else None,
                    "checkout_success": checkout_result.get("success") if checkout_result else None,
                    "created": checkout_result.get("created") if checkout_result else False,
                },
            }
            output.tokens_used = result.get("tokens_used")
            output.duration_ms = int((output.completed_at - output.started_at).total_seconds() * 1000)
            output.files_created = files_created

            await db.flush()

            return {
                "content": result["content"],
                "files": files_created,
                "git_changes": git_changes,
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
        Make an AI provider call using the Provider Abstraction Layer.

        Args:
            system_prompt: System prompt for the agent
            user_prompt: User message/prompt
            on_output: Optional callback for progress
            phase: Phase name for logging (also used to select provider)

        Returns:
            Result dictionary with content and token usage
        """
        # Map phase to provider role
        role_map = {
            "architecture": "planner",
            "development": "developer", 
            "review": "reviewer",
        }
        role = role_map.get(phase, "default")
        
        if on_output:
            await on_output("progress", {
                "phase": phase,
                "message": f"Starting {phase} phase...",
            })

        try:
            # Get provider for this role
            provider = self._get_provider(role)
            logger.info(f"Using provider {provider.provider_type} for {phase} phase")
            
            # Check provider health
            if not await provider.health_check():
                logger.warning(f"Provider {provider.provider_type} health check failed, using simulated")
                return await self._simulated_api_call(system_prompt, user_prompt, phase)
            
            # Make the call using provider abstraction
            messages = [Message(role=Role.USER, content=user_prompt)]
            
            if provider.supports_streaming:
                # Stream response
                content_parts = []
                tokens_used = {"input": 0, "output": 0}
                
                async for event in provider.stream(messages, system=system_prompt):
                    if event.type == "text_delta" and event.content:
                        content_parts.append(event.content)
                        if on_output:
                            await on_output("chunk", {"text": event.content, "phase": phase})
                    elif event.type == "input_tokens":
                        tokens_used["input"] = event.tokens or 0
                    elif event.type == "output_tokens":
                        tokens_used["output"] = event.tokens or 0
                    elif event.type == "error":
                        raise RuntimeError(event.error)
                
                content = "".join(content_parts)
            else:
                # Non-streaming call
                response = await provider.complete(messages, system=system_prompt)
                content = response.content
                tokens_used = {
                    "input": response.input_tokens or 0,
                    "output": response.output_tokens or 0,
                }

            if on_output:
                await on_output("progress", {
                    "phase": phase,
                    "message": f"{phase.capitalize()} phase completed",
                    "tokens": tokens_used,
                    "provider": provider.provider_type,
                })

            total_tokens = tokens_used["input"] + tokens_used["output"]
            return {
                "content": content,
                "tokens_used": total_tokens if total_tokens > 0 else None,
            }

        except Exception as e:
            logger.error(f"Provider call failed: {e}")
            return await self._simulated_api_call(system_prompt, user_prompt, phase)

    async def _cli_api_call(
        self,
        system_prompt: str,
        user_prompt: str,
        on_output: Optional[Callable[[str, dict], Any]] = None,
        phase: str = "unknown",
    ) -> dict:
        """
        Make API-like call using Claude CLI.
        
        Used when OAuth is available but no API key.
        """
        if on_output:
            await on_output("progress", {
                "phase": phase,
                "message": f"Starting {phase} phase via CLI (OAuth mode)...",
            })

        # Combine system and user prompts for CLI
        combined_prompt = f"{system_prompt}\n\n---\n\n{user_prompt}"
        
        try:
            # Use claude CLI with --print flag for non-interactive output
            process = await asyncio.create_subprocess_exec(
                "claude",
                "--dangerously-skip-permissions",
                "-p", combined_prompt,
                "--output-format", "text",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={
                    **os.environ,
                    "CLAUDE_CONFIG_DIR": settings.CLAUDE_CONFIG_DIR,
                },
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=180  # 3 minute timeout
            )

            if process.returncode != 0:
                logger.error(f"Claude CLI failed: {stderr.decode()}")
                return await self._simulated_api_call(system_prompt, user_prompt, phase)

            content = stdout.decode().strip()
            
            if on_output:
                await on_output("progress", {
                    "phase": phase,
                    "message": f"{phase.capitalize()} phase completed via CLI",
                })

            return {
                "content": content,
                "tokens_used": None,  # CLI doesn't report token usage
            }

        except asyncio.TimeoutError:
            logger.error("Claude CLI timed out")
            return await self._simulated_api_call(system_prompt, user_prompt, phase)
        except FileNotFoundError:
            logger.warning("Claude CLI not found")
            return await self._simulated_api_call(system_prompt, user_prompt, phase)
        except Exception as e:
            logger.error(f"CLI API call failed: {e}")
            return await self._simulated_api_call(system_prompt, user_prompt, phase)

    async def _cli_execute(
        self,
        prompt: str,
        workspace_path: str,
        on_output: Optional[Callable[[str, dict], Any]] = None,
        execution_id: Optional[UUID] = None,
        task_id: Optional[UUID] = None,
        board_id: Optional[UUID] = None,
    ) -> dict:
        """
        Execute developer phase using Claude CLI spawning with real-time streaming.

        Spawns 'claude --dangerously-skip-permissions -p' subprocess for
        autonomous code generation with file system access.

        Uses --output-format stream-json for structured streaming events
        that are broadcast via WebSocket in real-time.

        Args:
            prompt: The task prompt for the developer
            workspace_path: Directory for file operations
            on_output: Callback for streaming output
            execution_id: Execution UUID for WebSocket broadcasting
            task_id: Task UUID for WebSocket broadcasting
            board_id: Board UUID for WebSocket broadcasting

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
            # Build the command with stream-json output format
            # Note: --verbose is required when using -p with --output-format stream-json
            cmd = [
                claude_path,
                "--dangerously-skip-permissions",
                "--verbose",
                "-p", prompt,
                "--output-format", "stream-json",
            ]

            # Run with PTY for real-time streaming
            content, structured_events = await self._run_cli_with_streaming_pty(
                cmd=cmd,
                workspace_path=workspace_path,
                on_output=on_output,
                execution_id=execution_id,
                task_id=task_id,
                board_id=board_id,
            )

            if on_output:
                await on_output("progress", {
                    "phase": "development",
                    "message": "Development phase completed",
                })

            return {
                "content": content,
                "structured": {"events": structured_events},
            }

        except asyncio.TimeoutError:
            logger.error("CLI execution timed out")
            if on_output:
                await on_output("error", {"message": "CLI execution timed out"})
            return await self._simulated_cli_execute(prompt, workspace_path, on_output)

        except Exception as e:
            logger.error(f"CLI execution failed: {e}")
            return await self._simulated_cli_execute(prompt, workspace_path, on_output)

    def _detect_milestone(self, text: str) -> str:
        """
        Detect milestone from CLI output text using pattern matching.

        Args:
            text: Text buffer to analyze for milestone patterns

        Returns:
            Milestone string describing current activity
        """
        text_lower = text.lower()

        # Pattern-based milestone detection (order matters - most specific first)
        if 'read' in text_lower or 'reading' in text_lower:
            return 'Reading files...'
        elif 'write' in text_lower or 'writing' in text_lower or 'created' in text_lower:
            return 'Writing code...'
        elif 'edit' in text_lower or 'editing' in text_lower:
            return 'Editing files...'
        elif 'test' in text_lower:
            return 'Running tests...'
        elif 'install' in text_lower or 'npm' in text_lower or 'pip' in text_lower:
            return 'Installing dependencies...'
        elif 'think' in text_lower:
            return 'Thinking...'
        else:
            return 'Working...'

    async def _run_cli_with_streaming_pty(
        self,
        cmd: list,
        workspace_path: str,
        on_output: Optional[Callable[[str, dict], Any]] = None,
        execution_id: Optional[UUID] = None,
        task_id: Optional[UUID] = None,
        board_id: Optional[UUID] = None,
        timeout: int = 600,
    ) -> tuple[str, list]:
        """
        Run Claude CLI with PTY support and milestone-based progress updates.

        Parses stream-json output format and broadcasts milestone events via WebSocket
        instead of streaming every single event. Uses batched output processing with
        pattern-based milestone detection to prevent frontend hanging.

        Args:
            cmd: Command to execute
            workspace_path: Working directory
            on_output: Callback for streaming output
            execution_id: Execution UUID for WebSocket broadcasting
            task_id: Task UUID for WebSocket broadcasting
            board_id: Board UUID for WebSocket broadcasting
            timeout: Timeout in seconds

        Returns:
            Tuple of (content, structured_events)
        """
        import errno
        import pty
        import select
        import time

        env = {
            **os.environ,
            "CLAUDE_CONFIG_DIR": settings.CLAUDE_CONFIG_DIR,
        }

        output_chunks = []
        structured_events = []
        text_content_parts = []
        json_buffer = ""

        # Milestone tracking
        output_buffer = ""
        last_milestone_time = time.time()
        last_milestone = None
        milestone_interval = 2.5  # Send milestone updates every 2.5 seconds

        def parse_stream_json_line(line: str) -> Optional[dict]:
            """Parse a single line of stream-json output."""
            line = line.strip()
            if not line:
                return None
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                return None

        async def broadcast_milestone(milestone: str):
            """Broadcast milestone update via WebSocket."""
            if board_id:
                payload = {
                    "execution_id": str(execution_id) if execution_id else None,
                    "task_id": str(task_id) if task_id else None,
                    "milestone": milestone,
                    "timestamp": datetime.utcnow().isoformat(),
                }
                asyncio.create_task(
                    ws_manager.broadcast(
                        str(board_id),
                        {
                            "type": "execution_milestone",
                            "payload": payload,
                        },
                    )
                )

        def process_pty_output(data: bytes):
            """Process PTY output and extract stream-json events."""
            nonlocal json_buffer, text_content_parts

            # Decode and clean the output
            text = data.decode('utf-8', errors='replace')

            # Remove ANSI escape codes
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            clean_text = ansi_escape.sub('', text)

            # Remove control characters but keep newlines
            clean_text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', clean_text)

            # Buffer and process line by line
            json_buffer += clean_text
            lines = json_buffer.split('\n')
            json_buffer = lines[-1]  # Keep incomplete line in buffer

            for line in lines[:-1]:  # Process complete lines
                event = parse_stream_json_line(line)
                if event:
                    structured_events.append(event)

                    # Extract text content for final output
                    event_type = event.get("type", "unknown")
                    if event_type == "assistant" and "message" in event:
                        msg = event["message"]
                        if isinstance(msg, dict):
                            for block in msg.get("content", []):
                                if block.get("type") == "text":
                                    content_text = block.get("text", "")
                                    text_content_parts.append(content_text)
                    elif event_type == "content_block_delta":
                        delta = event.get("delta", {})
                        if delta.get("type") == "text_delta":
                            content_text = delta.get("text", "")
                            text_content_parts.append(content_text)
                    elif event_type == "result":
                        content_text = event.get("result", "")
                        if content_text:
                            text_content_parts.append(content_text)

        logger.info(f"Running CLI with streaming PTY: {cmd[0]}...")

        loop = asyncio.get_event_loop()

        def run_pty_sync():
            """Synchronous PTY execution in thread pool."""
            nonlocal output_buffer, last_milestone_time, last_milestone

            master_fd, slave_fd = pty.openpty()

            pid = os.fork()

            if pid == 0:
                # Child process
                os.close(master_fd)
                os.setsid()
                os.dup2(slave_fd, 0)
                os.dup2(slave_fd, 1)
                os.dup2(slave_fd, 2)
                if slave_fd > 2:
                    os.close(slave_fd)
                os.chdir(workspace_path)
                os.execvpe(cmd[0], cmd, env)
            else:
                # Parent process
                os.close(slave_fd)

                start_time = time.time()
                milestone_updates = []

                try:
                    while True:
                        elapsed = time.time() - start_time
                        if elapsed > timeout:
                            os.kill(pid, 9)
                            raise asyncio.TimeoutError(f"PTY timeout after {timeout}s")

                        try:
                            r, _, _ = select.select([master_fd], [], [], 0.1)
                            if master_fd in r:
                                try:
                                    data = os.read(master_fd, 4096)
                                    if not data:
                                        break
                                    output_chunks.append(data)

                                    # Add to buffer for milestone detection
                                    decoded = data.decode('utf-8', errors='replace')
                                    output_buffer += decoded

                                    # Check if enough time has passed to send milestone update
                                    current_time = time.time()
                                    if current_time - last_milestone_time >= milestone_interval:
                                        # Detect milestone from buffer
                                        detected_milestone = self._detect_milestone(output_buffer)

                                        # Only send if milestone changed
                                        if detected_milestone != last_milestone:
                                            milestone_updates.append(detected_milestone)
                                            last_milestone = detected_milestone

                                        last_milestone_time = current_time
                                        # Clear buffer after processing
                                        output_buffer = ""

                                except OSError as e:
                                    if e.errno == errno.EIO:
                                        break
                                    raise
                        except select.error:
                            break

                finally:
                    os.close(master_fd)
                    try:
                        os.waitpid(pid, 0)
                    except ChildProcessError:
                        pass

                return milestone_updates

        # Run PTY in executor
        milestone_updates = await loop.run_in_executor(None, run_pty_sync)

        # Broadcast milestone updates
        for milestone in milestone_updates:
            await broadcast_milestone(milestone)

        # Process all chunks to extract structured events
        for chunk in output_chunks:
            process_pty_output(chunk)

        # Process any remaining buffer
        if json_buffer.strip():
            event = parse_stream_json_line(json_buffer)
            if event:
                structured_events.append(event)

        # Combine all text content
        full_content = "".join(text_content_parts)

        # If no structured text content, fall back to raw output
        if not full_content:
            raw_output = b''.join(output_chunks).decode('utf-8', errors='replace')
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            full_content = ansi_escape.sub('', raw_output)
            full_content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', full_content)

        return full_content.strip(), structured_events

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

    async def _load_plan_from_execution(
        self,
        db: AsyncSession,
        plan_execution_id: str,
    ) -> Optional[dict]:
        """
        Load a plan from a previous architecture_only execution.

        Args:
            db: Database session
            plan_execution_id: UUID of the previous execution

        Returns:
            Architecture result dict with 'content' key, or None if not found
        """
        from uuid import UUID as PyUUID
        
        try:
            exec_uuid = PyUUID(plan_execution_id)
        except ValueError:
            logger.error(f"Invalid plan_execution_id: {plan_execution_id}")
            return None

        # Get the execution
        result = await db.execute(
            select(AgentExecution).where(AgentExecution.id == exec_uuid)
        )
        execution = result.scalar_one_or_none()

        if not execution:
            logger.error(f"Plan execution {plan_execution_id} not found")
            return None

        if execution.workflow_type != "architecture_only":
            logger.warning(f"Execution {plan_execution_id} is not architecture_only")
            # Still try to load the plan

        if execution.status != "completed":
            logger.warning(f"Execution {plan_execution_id} is not completed (status: {execution.status})")

        # Get the architecture output
        result = await db.execute(
            select(AgentOutput).where(
                AgentOutput.execution_id == exec_uuid,
                AgentOutput.phase == "architecture",
            )
        )
        output = result.scalar_one_or_none()

        if not output or not output.output_content:
            logger.error(f"No architecture output found for execution {plan_execution_id}")
            return None

        return {
            "content": output.output_content,
            "source_execution_id": plan_execution_id,
        }

    async def _get_effective_working_directory(
        self,
        db: AsyncSession,
        task: Task,
        execution: AgentExecution,
        default_workspace: str,
    ) -> str:
        """
        Determine the effective working directory for agent execution.

        Priority order:
        1. Repository path from task's info.json (if exists)
        2. Board's working_directory (if set)
        3. Default workspace path

        Args:
            db: Database session
            task: Task being processed
            execution: Current execution
            default_workspace: Default workspace path to fall back to

        Returns:
            The effective working directory path
        """
        # 1. Try to load info.json for the task
        try:
            info_content = file_storage.load_output(
                board_id=str(execution.board_id),
                task_id=str(task.id),
                filename="info.json",
            )
            if info_content:
                info_data = json.loads(info_content)
                # Handle both formats: repository as string or as object with path
                repository = info_data.get("repository")
                if isinstance(repository, dict):
                    repository_path = repository.get("path")
                else:
                    repository_path = repository
                    
                if repository_path:
                    repo_path = Path(repository_path)
                    if repo_path.exists() and repo_path.is_dir():
                        logger.info(
                            f"Using repository path from info.json: {repository_path}"
                        )
                        return str(repo_path)
                    else:
                        logger.warning(
                            f"Repository path from info.json does not exist: {repository_path}"
                        )
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse info.json for task {task.id}: {e}")
        except Exception as e:
            logger.warning(f"Error loading info.json for task {task.id}: {e}")

        # 2. Try board's working_directory
        board = await db.get(Board, execution.board_id)
        if board and board.working_directory:
            board_dir = Path(board.working_directory)
            if board_dir.exists() and board_dir.is_dir():
                logger.info(
                    f"Using board working_directory: {board.working_directory}"
                )
                return str(board_dir)
            else:
                logger.warning(
                    f"Board working_directory does not exist: {board.working_directory}"
                )

        # 3. Fall back to default workspace
        logger.info(f"Using default workspace: {default_workspace}")
        return default_workspace

    async def _get_task_branch(
        self,
        board_id: str,
        task_id: str,
    ) -> Optional[dict]:
        """
        Get the branch info from task's info.json.
        
        Args:
            board_id: Board ID
            task_id: Task ID
            
        Returns:
            Branch info dict or None: {"name": "main", "source": "default", ...}
        """
        try:
            info_content = file_storage.load_output(
                board_id=board_id,
                task_id=task_id,
                filename="info.json",
            )
            if info_content:
                info_data = json.loads(info_content)
                return info_data.get("branch")
        except Exception as e:
            logger.warning(f"Error loading branch info for task {task_id}: {e}")
        return None

    def _get_default_branch_name(self, repo_path: str) -> str:
        """
        Get the default branch name (main or master) for a repository.
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            Default branch name ("main" or "master")
        """
        try:
            # Check if main exists
            result = subprocess.run(
                ["git", "rev-parse", "--verify", "main"],
                cwd=repo_path,
                capture_output=True,
                timeout=5,
            )
            if result.returncode == 0:
                return "main"
            
            # Check if master exists
            result = subprocess.run(
                ["git", "rev-parse", "--verify", "master"],
                cwd=repo_path,
                capture_output=True,
                timeout=5,
            )
            if result.returncode == 0:
                return "master"
            
            return "main"  # Default fallback
        except Exception:
            return "main"

    def _checkout_branch(
        self, 
        repo_path: str, 
        branch_name: str, 
        source: str = "default",
        create_if_missing: bool = False,
    ) -> dict:
        """
        Checkout a specific branch in the repository.
        
        Args:
            repo_path: Path to the repository
            branch_name: Branch name to checkout
            source: Source of branch detection ("task_text", "llm_suggestion", "default")
            create_if_missing: If True and source is "task_text", create branch if it doesn't exist
            
        Returns:
            Result dict: {"success": True/False, "previous_branch": "...", "created": True/False, "error": "..."}
        """
        result = {
            "success": False,
            "branch": branch_name,
            "previous_branch": None,
            "created": False,
            "error": None,
        }
        
        try:
            # Get current branch first
            current_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if current_result.returncode == 0:
                result["previous_branch"] = current_result.stdout.strip()
                
                # If already on the target branch, no need to checkout
                if result["previous_branch"] == branch_name:
                    result["success"] = True
                    logger.info(f"Already on branch {branch_name}")
                    return result
            
            # Fetch latest from remote (ignore errors if offline)
            subprocess.run(
                ["git", "fetch", "--quiet"],
                cwd=repo_path,
                capture_output=True,
                timeout=30,
            )
            
            # Try to checkout the branch
            checkout_result = subprocess.run(
                ["git", "checkout", branch_name],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            if checkout_result.returncode == 0:
                result["success"] = True
                logger.info(f"Checked out branch {branch_name} in {repo_path}")
            else:
                # Branch might not exist locally, try to checkout from remote
                checkout_result = subprocess.run(
                    ["git", "checkout", "-b", branch_name, f"origin/{branch_name}"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if checkout_result.returncode == 0:
                    result["success"] = True
                    logger.info(f"Checked out remote branch {branch_name} in {repo_path}")
                else:
                    # Branch doesn't exist locally or remotely
                    # Create it if source is "task_text" (explicit user request)
                    if source == "task_text" and create_if_missing:
                        default_branch = self._get_default_branch_name(repo_path)
                        logger.info(f"Branch {branch_name} doesn't exist, creating from {default_branch}")
                        
                        # First checkout the default branch
                        subprocess.run(
                            ["git", "checkout", default_branch],
                            cwd=repo_path,
                            capture_output=True,
                            timeout=30,
                        )
                        
                        # Create new branch from default
                        create_result = subprocess.run(
                            ["git", "checkout", "-b", branch_name],
                            cwd=repo_path,
                            capture_output=True,
                            text=True,
                            timeout=30,
                        )
                        
                        if create_result.returncode == 0:
                            result["success"] = True
                            result["created"] = True
                            logger.info(f"Created and checked out new branch {branch_name} from {default_branch}")
                        else:
                            result["error"] = create_result.stderr.strip()
                            logger.warning(f"Failed to create branch {branch_name}: {result['error']}")
                    else:
                        result["error"] = f"Branch {branch_name} doesn't exist"
                        logger.warning(f"Branch {branch_name} doesn't exist and won't be created (source: {source})")
                    
        except subprocess.TimeoutExpired:
            result["error"] = "Git operation timed out"
            logger.warning(f"Git checkout timed out for branch {branch_name}")
        except Exception as e:
            result["error"] = str(e)
            logger.warning(f"Error checking out branch {branch_name}: {e}")
            
        return result

    def _list_workspace_files(self, workspace_path: str, max_files: int = 100) -> list:
        """List files in workspace (limited to prevent huge responses)."""
        files = []
        workspace = Path(workspace_path)
        if workspace.exists():
            for path in workspace.rglob("*"):
                if path.is_file() and not path.name.startswith("."):
                    files.append(str(path.relative_to(workspace)))
                    if len(files) >= max_files:
                        break  # Limit to prevent scanning huge directories
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

    def _is_git_repo(self, path: str) -> bool:
        """Check if the path is inside a git repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception as e:
            logger.debug(f"Git check failed for {path}: {e}")
            return False

    def _capture_git_state(self, path: str) -> dict:
        """
        Capture git state before agent execution.
        
        Returns:
            dict with 'is_git_repo', 'head_commit', 'staged_files', 'modified_files'
        """
        if not self._is_git_repo(path):
            return {"is_git_repo": False}
        
        try:
            # Get current HEAD commit
            head_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=5,
            )
            head_commit = head_result.stdout.strip() if head_result.returncode == 0 else None
            
            # Get list of modified files (unstaged)
            modified_result = subprocess.run(
                ["git", "diff", "--name-only"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            modified_files = modified_result.stdout.strip().split("\n") if modified_result.stdout.strip() else []
            
            # Get list of staged files
            staged_result = subprocess.run(
                ["git", "diff", "--name-only", "--cached"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            staged_files = staged_result.stdout.strip().split("\n") if staged_result.stdout.strip() else []
            
            # Get untracked files
            untracked_result = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            untracked_files = untracked_result.stdout.strip().split("\n") if untracked_result.stdout.strip() else []
            
            return {
                "is_git_repo": True,
                "head_commit": head_commit,
                "staged_files": staged_files,
                "modified_files": modified_files,
                "untracked_files": untracked_files,
            }
        except Exception as e:
            logger.warning(f"Failed to capture git state for {path}: {e}")
            return {"is_git_repo": True, "error": str(e)}

    def _get_git_changed_files(self, path: str, pre_state: dict) -> dict:
        """
        Get files changed by comparing current state to pre-execution state.
        
        Args:
            path: Working directory path
            pre_state: State captured before execution via _capture_git_state()
            
        Returns:
            dict with 'created', 'modified', 'deleted' file lists
        """
        if not pre_state.get("is_git_repo"):
            # Fall back to listing workspace files if not a git repo
            return {
                "created": self._list_workspace_files(path),
                "modified": [],
                "deleted": [],
                "is_git_repo": False,
            }
        
        try:
            # Get current modified files (unstaged)
            modified_result = subprocess.run(
                ["git", "diff", "--name-only"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            current_modified = set(modified_result.stdout.strip().split("\n")) if modified_result.stdout.strip() else set()
            
            # Get current staged files
            staged_result = subprocess.run(
                ["git", "diff", "--name-only", "--cached"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            current_staged = set(staged_result.stdout.strip().split("\n")) if staged_result.stdout.strip() else set()
            
            # Get current untracked files
            untracked_result = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            current_untracked = set(untracked_result.stdout.strip().split("\n")) if untracked_result.stdout.strip() else set()
            
            # Calculate changes
            pre_modified = set(pre_state.get("modified_files", []))
            pre_staged = set(pre_state.get("staged_files", []))
            pre_untracked = set(pre_state.get("untracked_files", []))
            
            # New files = untracked now but weren't before
            created = list(current_untracked - pre_untracked)
            
            # Modified files = modified/staged now but weren't before (excluding newly created)
            all_current_changes = current_modified | current_staged
            all_pre_changes = pre_modified | pre_staged
            modified = list((all_current_changes - all_pre_changes) - current_untracked)
            
            # Get detailed diff stats for modified files
            diff_stats = []
            if modified or created:
                # Get diff stats for all changed files
                stats_result = subprocess.run(
                    ["git", "diff", "--stat", "--no-color"],
                    cwd=path,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if stats_result.returncode == 0:
                    diff_stats = stats_result.stdout.strip().split("\n")
            
            return {
                "created": sorted(created),
                "modified": sorted(modified),
                "deleted": [],  # Would need to track this differently
                "all_changed": sorted(set(created + modified)),
                "diff_stats": diff_stats,
                "is_git_repo": True,
            }
        except Exception as e:
            logger.warning(f"Failed to get git changes for {path}: {e}")
            return {
                "created": self._list_workspace_files(path),
                "modified": [],
                "deleted": [],
                "is_git_repo": True,
                "error": str(e),
            }

    def _auto_commit_changes(
        self, 
        path: str, 
        task_id: str, 
        task_title: str, 
        execution_id: str,
        git_changes: dict,
    ) -> dict:
        """
        Auto-commit changes made by the developer agent.
        
        Args:
            path: Working directory path
            task_id: Task ID for commit message
            task_title: Task title for commit message
            execution_id: Execution ID for reference
            git_changes: Git changes dict from _get_git_changed_files()
            
        Returns:
            dict with commit info or error
        """
        if not git_changes.get("is_git_repo"):
            return {"committed": False, "reason": "not a git repository"}
        
        all_changed = git_changes.get("all_changed", [])
        if not all_changed:
            return {"committed": False, "reason": "no files changed"}
        
        try:
            # Stage all changed files
            for file in all_changed:
                stage_result = subprocess.run(
                    ["git", "add", file],
                    cwd=path,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if stage_result.returncode != 0:
                    logger.warning(f"Failed to stage {file}: {stage_result.stderr}")
            
            # Create commit message
            short_task_id = str(task_id)[:8]
            # Sanitize task title for commit message
            safe_title = task_title.replace('"', "'").replace('\n', ' ')[:50]
            commit_message = f"[Agent Rangers] {safe_title}\n\nTask: {task_id}\nExecution: {execution_id}\n\nFiles changed:\n"
            
            created = git_changes.get("created", [])
            modified = git_changes.get("modified", [])
            
            if created:
                commit_message += f"\nCreated ({len(created)}):\n"
                for f in created[:10]:  # Limit to 10 files in message
                    commit_message += f"  + {f}\n"
                if len(created) > 10:
                    commit_message += f"  ... and {len(created) - 10} more\n"
            
            if modified:
                commit_message += f"\nModified ({len(modified)}):\n"
                for f in modified[:10]:
                    commit_message += f"  ~ {f}\n"
                if len(modified) > 10:
                    commit_message += f"  ... and {len(modified) - 10} more\n"
            
            # Commit
            commit_result = subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            if commit_result.returncode != 0:
                # Check if it's just "nothing to commit"
                if "nothing to commit" in commit_result.stdout or "nothing to commit" in commit_result.stderr:
                    return {"committed": False, "reason": "nothing to commit"}
                logger.warning(f"Git commit failed: {commit_result.stderr}")
                return {"committed": False, "reason": commit_result.stderr}
            
            # Get the commit hash
            hash_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=5,
            )
            commit_hash = hash_result.stdout.strip() if hash_result.returncode == 0 else None
            
            logger.info(f"Auto-committed changes for task {short_task_id}: {commit_hash}")
            
            return {
                "committed": True,
                "commit_hash": commit_hash,
                "files_committed": len(all_changed),
                "message": commit_message.split('\n')[0],  # First line only
            }
            
        except Exception as e:
            logger.error(f"Auto-commit failed for task {task_id}: {e}")
            return {"committed": False, "reason": str(e)}

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
        from sqlalchemy.orm import noload, selectinload, load_only
        from app.models.agent_output import AgentOutput
        
        result = await db.execute(
            select(AgentExecution)
            .options(
                noload(AgentExecution.task),
                noload(AgentExecution.board),
                # Load outputs but prevent their nested relationships from loading
                selectinload(AgentExecution.outputs).options(
                    noload(AgentOutput.execution),
                    noload(AgentOutput.task),
                ),
            )
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
        from sqlalchemy.orm import noload
        
        query = (
            select(AgentExecution)
            .options(
                noload(AgentExecution.task),
                noload(AgentExecution.board),
                noload(AgentExecution.outputs),
            )
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
