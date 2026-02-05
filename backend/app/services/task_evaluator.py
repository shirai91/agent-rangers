"""Task evaluator service for Agent Rangers.

Evaluates tasks to determine which repository they relate to using LLM analysis.
Also detects the appropriate git branch to work on.
"""

import json
import logging
import re
import subprocess
from datetime import datetime, timezone
from typing import Optional

from app.config import settings
from app.providers import ProviderFactory, Message, Role
from app.services.file_storage import file_storage
from app.services.repository_scanner import repository_scanner

logger = logging.getLogger(__name__)


class TaskEvaluatorService:
    """
    Service for evaluating tasks and matching them to repositories.

    Uses an LLM to analyze task descriptions and determine which repository
    the task is most likely related to based on available context.
    """

    def __init__(self) -> None:
        """Initialize the task evaluator service."""
        self._provider = None

    def _get_repo_branches(self, repo_path: str) -> list[dict]:
        """
        Get list of branches for a repository with their last commit info.
        
        Args:
            repo_path: Path to the git repository.
            
        Returns:
            List of branch info dicts: [{"name": "main", "last_commit": "2026-02-05T10:00:00", "is_current": True}, ...]
        """
        try:
            # Get all branches with last commit date
            result = subprocess.run(
                ["git", "for-each-ref", "--sort=-committerdate", 
                 "--format=%(refname:short)|%(committerdate:iso8601)|%(HEAD)", 
                 "refs/heads/"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            
            if result.returncode != 0:
                logger.warning(f"Failed to get branches for {repo_path}: {result.stderr}")
                return []
            
            branches = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("|")
                if len(parts) >= 2:
                    branches.append({
                        "name": parts[0],
                        "last_commit": parts[1] if len(parts) > 1 else None,
                        "is_current": parts[2] == "*" if len(parts) > 2 else False,
                    })
            
            return branches
        except Exception as e:
            logger.warning(f"Error getting branches for {repo_path}: {e}")
            return []

    def _get_default_branch(self, repo_path: str) -> str:
        """
        Determine the default branch (main or master, whichever has most recent commit).
        
        Args:
            repo_path: Path to the git repository.
            
        Returns:
            Branch name (defaults to "main" if unable to determine).
        """
        try:
            branches = self._get_repo_branches(repo_path)
            
            # Look for main or master
            main_branch = None
            master_branch = None
            
            for branch in branches:
                if branch["name"] == "main":
                    main_branch = branch
                elif branch["name"] == "master":
                    master_branch = branch
            
            # If both exist, return the one with most recent commit
            if main_branch and master_branch:
                # Branches are sorted by commit date (newest first), so check order
                for branch in branches:
                    if branch["name"] in ("main", "master"):
                        return branch["name"]
            
            # Return whichever exists
            if main_branch:
                return "main"
            if master_branch:
                return "master"
            
            # If neither main nor master, return the most recent branch
            if branches:
                return branches[0]["name"]
            
            return "main"  # Fallback
            
        except Exception as e:
            logger.warning(f"Error determining default branch for {repo_path}: {e}")
            return "main"

    def _detect_branch_from_text(self, text: str, available_branches: list[str]) -> Optional[str]:
        """
        Try to detect a branch name mentioned in the task text.
        
        Args:
            text: Task title and description combined.
            available_branches: List of available branch names.
            
        Returns:
            Detected branch name or None.
        """
        text_lower = text.lower()
        
        # Common patterns for branch references
        patterns = [
            r'branch[:\s]+["\']?([a-zA-Z0-9_\-/]+)["\']?',
            r'on\s+branch\s+["\']?([a-zA-Z0-9_\-/]+)["\']?',
            r'in\s+branch\s+["\']?([a-zA-Z0-9_\-/]+)["\']?',
            r'from\s+branch\s+["\']?([a-zA-Z0-9_\-/]+)["\']?',
            r'to\s+branch\s+["\']?([a-zA-Z0-9_\-/]+)["\']?',
            r'feature[/\-]([a-zA-Z0-9_\-]+)',
            r'bugfix[/\-]([a-zA-Z0-9_\-]+)',
            r'hotfix[/\-]([a-zA-Z0-9_\-]+)',
            r'release[/\-]([a-zA-Z0-9_\-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                detected = match.group(1)
                # Check if it's a full branch name in available branches
                if detected in available_branches:
                    return detected
                # Check for partial matches (e.g., "feature/login" when user says "login")
                for branch in available_branches:
                    if detected.lower() in branch.lower():
                        return branch
        
        # Direct mention of branch names
        for branch in available_branches:
            # Escape special regex characters in branch name
            escaped_branch = re.escape(branch)
            if re.search(rf'\b{escaped_branch}\b', text, re.IGNORECASE):
                return branch
        
        return None

    @property
    def provider(self):
        """Lazy-load the provider."""
        if self._provider is None:
            self._provider = ProviderFactory.create_for_role(
                'evaluator', settings.get_providers_config()
            )
        return self._provider

    async def evaluate_task(
        self,
        board_id: str,
        task_id: str,
        task_title: str,
        task_description: str,
    ) -> dict:
        """
        Evaluate a task and determine which repository it relates to.

        Loads repositories associated with the board, builds a prompt asking
        the LLM which repository the task relates to, and saves the result
        as info.json in the task outputs directory.

        Args:
            board_id: The UUID of the board as a string.
            task_id: The UUID of the task as a string.
            task_title: The title of the task.
            task_description: The description of the task.

        Returns:
            Dictionary containing the evaluation result with schema:
            {
                "task_id": "uuid",
                "evaluated_at": "ISO timestamp",
                "repository": {
                    "path": "/path/to/repo",
                    "name": "repo-name",
                    "confidence": 0.95,
                    "reasoning": "Task mentions X which relates to repo Y"
                } or null,
                "context": {
                    "relevant_files": [],
                    "technologies": []
                }
            }
        """
        # Load repositories for this board
        repositories = repository_scanner.load_repositories(board_id)

        # Build the evaluation result
        result = await self._evaluate_with_llm(
            task_id=task_id,
            task_title=task_title,
            task_description=task_description,
            repositories=repositories,
        )

        # Save result to info.json
        self._save_result(board_id, task_id, result)

        return result

    async def _evaluate_with_llm(
        self,
        task_id: str,
        task_title: str,
        task_description: str,
        repositories: list[dict],
    ) -> dict:
        """
        Use LLM to evaluate which repository the task relates to.

        Args:
            task_id: The UUID of the task.
            task_title: The title of the task.
            task_description: The description of the task.
            repositories: List of repository info dictionaries.

        Returns:
            Evaluation result dictionary.
        """
        evaluated_at = datetime.now(timezone.utc).isoformat()

        # Base result structure
        result = {
            "task_id": task_id,
            "evaluated_at": evaluated_at,
            "repository": None,
            "branch": None,
            "context": {
                "relevant_files": [],
                "technologies": [],
            },
        }

        # If no repositories, return early
        if not repositories:
            logger.info(f"No repositories found for task {task_id}")
            return result

        # Build prompt
        prompt = self._build_prompt(task_title, task_description, repositories)

        try:
            response = await self.provider.complete(
                [Message(role=Role.USER, content=prompt)]
            )

            # Extract response text
            response_text = response.content

            # Parse the response
            parsed = self._parse_response(response_text, repositories)
            if parsed:
                result["repository"] = parsed.get("repository")
                result["context"] = parsed.get("context", result["context"])
                
                # Determine branch after we know the repository
                if result["repository"] and result["repository"].get("path"):
                    repo_path = result["repository"]["path"]
                    branch_info = self._determine_branch(
                        repo_path=repo_path,
                        task_title=task_title,
                        task_description=task_description,
                        llm_suggested_branch=parsed.get("branch"),
                    )
                    result["branch"] = branch_info

        except Exception as e:
            logger.error(f"Failed to evaluate task {task_id}: {e}")

        return result

    def _determine_branch(
        self,
        repo_path: str,
        task_title: str,
        task_description: str,
        llm_suggested_branch: Optional[str] = None,
    ) -> dict:
        """
        Determine which branch to use for the task.
        
        Priority:
        1. Branch explicitly mentioned in task title/description
        2. Branch suggested by LLM
        3. Default branch (main/master with most recent commit)
        
        Args:
            repo_path: Path to the repository.
            task_title: Task title.
            task_description: Task description.
            llm_suggested_branch: Branch name suggested by LLM (if any).
            
        Returns:
            Branch info dict: {"name": "main", "source": "default", "available_branches": [...]}
        """
        # Get available branches
        branches = self._get_repo_branches(repo_path)
        available_branch_names = [b["name"] for b in branches]
        
        branch_info = {
            "name": None,
            "source": None,
            "available_branches": available_branch_names[:10],  # Limit for readability
        }
        
        # Combine task text for branch detection
        task_text = f"{task_title}\n{task_description or ''}"
        
        # 1. Check for explicit branch mention in task
        detected_branch = self._detect_branch_from_text(task_text, available_branch_names)
        if detected_branch:
            branch_info["name"] = detected_branch
            branch_info["source"] = "task_text"
            logger.info(f"Branch detected from task text: {detected_branch}")
            return branch_info
        
        # 2. Check LLM suggestion
        if llm_suggested_branch and llm_suggested_branch in available_branch_names:
            branch_info["name"] = llm_suggested_branch
            branch_info["source"] = "llm_suggestion"
            logger.info(f"Using LLM suggested branch: {llm_suggested_branch}")
            return branch_info
        
        # 3. Use default branch (main/master with most recent commit)
        default_branch = self._get_default_branch(repo_path)
        branch_info["name"] = default_branch
        branch_info["source"] = "default"
        logger.info(f"Using default branch: {default_branch}")
        
        return branch_info

    def _build_prompt(
        self,
        task_title: str,
        task_description: str,
        repositories: list[dict],
    ) -> str:
        """
        Build the prompt for repository matching.

        Args:
            task_title: The title of the task.
            task_description: The description of the task.
            repositories: List of repository info dictionaries.

        Returns:
            The prompt string.
        """
        # Format repository information
        repo_descriptions = []
        for i, repo in enumerate(repositories, 1):
            desc = f"{i}. **{repo['name']}**\n"
            desc += f"   - Path: {repo['path']}\n"
            if repo.get("primary_language"):
                desc += f"   - Primary Language: {repo['primary_language']}\n"
            if repo.get("remote_url"):
                desc += f"   - Remote: {repo['remote_url']}\n"
            if repo.get("file_counts"):
                top_extensions = sorted(
                    repo["file_counts"].items(), key=lambda x: x[1], reverse=True
                )[:5]
                if top_extensions:
                    ext_str = ", ".join(f"{ext}({count})" for ext, count in top_extensions)
                    desc += f"   - Top file types: {ext_str}\n"
            repo_descriptions.append(desc)

        repos_text = "\n".join(repo_descriptions)

        prompt = f"""You are a task analyzer. Given a task and a list of repositories, determine which repository the task most likely relates to, and if a specific git branch is mentioned.

## Task
**Title:** {task_title}
**Description:** {task_description or "(no description)"}

## Available Repositories
{repos_text}

## Instructions
Analyze the task and determine:
1. Which repository the task most likely relates to
2. If a specific git branch is mentioned (look for patterns like "branch: X", "on branch X", "feature/X", "bugfix/X", etc.)

Consider:
- Keywords in the task title and description
- Technology/language mentioned vs repository's primary language
- Domain-specific terms that might match repository names
- Any branch names or patterns mentioned

Respond in JSON format:
```json
{{
    "repository": {{
        "name": "repo-name",
        "path": "/path/to/repo",
        "confidence": 0.0 to 1.0,
        "reasoning": "Brief explanation of why this repository matches"
    }},
    "branch": "branch-name-if-mentioned-or-null",
    "context": {{
        "relevant_files": ["list of potentially relevant file paths or patterns"],
        "technologies": ["list of technologies mentioned or inferred"]
    }}
}}
```

If no repository clearly matches, set "repository" to null.
If no branch is explicitly mentioned, set "branch" to null (the system will use the default branch).
Only output the JSON, no other text."""

        return prompt

    def _parse_response(
        self,
        response_text: str,
        repositories: list[dict],
    ) -> Optional[dict]:
        """
        Parse the LLM response to extract repository match.

        Args:
            response_text: The raw response text from the LLM.
            repositories: List of repository info dictionaries for validation.

        Returns:
            Parsed result dictionary or None if parsing fails.
        """
        try:
            # Extract JSON from response using multiple strategies
            text = response_text.strip()

            # Strategy 1: Try to extract JSON from markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
            if json_match:
                text = json_match.group(1)
            else:
                # Strategy 2: Try to find raw JSON object (handles nested braces)
                json_match = re.search(r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})', text, re.DOTALL)
                if json_match:
                    text = json_match.group(1)

            parsed = json.loads(text)

            # Validate repository if present
            if parsed.get("repository"):
                repo = parsed["repository"]
                # Verify the repository exists in our list
                valid_repo = None
                for r in repositories:
                    if r["name"] == repo.get("name") or r["path"] == repo.get("path"):
                        valid_repo = r
                        break

                if valid_repo:
                    # Ensure we have the correct path and name from our list
                    parsed["repository"]["path"] = valid_repo["path"]
                    parsed["repository"]["name"] = valid_repo["name"]
                    # Ensure confidence is a float between 0 and 1
                    confidence = parsed["repository"].get("confidence", 0.5)
                    parsed["repository"]["confidence"] = max(0.0, min(1.0, float(confidence)))
                else:
                    # Repository not found in our list, set to null
                    parsed["repository"] = None

            # Ensure context has the expected structure
            if "context" not in parsed:
                parsed["context"] = {"relevant_files": [], "technologies": []}
            else:
                if "relevant_files" not in parsed["context"]:
                    parsed["context"]["relevant_files"] = []
                if "technologies" not in parsed["context"]:
                    parsed["context"]["technologies"] = []

            # Ensure branch is a string or None
            if "branch" in parsed and parsed["branch"]:
                parsed["branch"] = str(parsed["branch"])
            else:
                parsed["branch"] = None

            return parsed

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Failed to parse LLM response: {e}")
            return None

    def _save_result(self, board_id: str, task_id: str, result: dict) -> None:
        """
        Save the evaluation result to info.json.

        Args:
            board_id: The UUID of the board as a string.
            task_id: The UUID of the task as a string.
            result: The evaluation result dictionary.
        """
        content = json.dumps(result, indent=2, ensure_ascii=False)
        file_storage.save_output(board_id, task_id, "info.json", content)
        logger.info(f"Saved evaluation result for task {task_id}")


# Global singleton instance
task_evaluator = TaskEvaluatorService()
