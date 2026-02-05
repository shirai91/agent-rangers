"""Task evaluator service for Agent Rangers.

Evaluates tasks to determine which repository they relate to using LLM analysis.
"""

import json
import logging
import re
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

        except Exception as e:
            logger.error(f"Failed to evaluate task {task_id}: {e}")

        return result

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

        prompt = f"""You are a task analyzer. Given a task and a list of repositories, determine which repository the task most likely relates to.

## Task
**Title:** {task_title}
**Description:** {task_description or "(no description)"}

## Available Repositories
{repos_text}

## Instructions
Analyze the task and determine which repository it most likely relates to. Consider:
- Keywords in the task title and description
- Technology/language mentioned vs repository's primary language
- Domain-specific terms that might match repository names

Respond in JSON format:
```json
{{
    "repository": {{
        "name": "repo-name",
        "path": "/path/to/repo",
        "confidence": 0.0 to 1.0,
        "reasoning": "Brief explanation of why this repository matches"
    }},
    "context": {{
        "relevant_files": ["list of potentially relevant file paths or patterns"],
        "technologies": ["list of technologies mentioned or inferred"]
    }}
}}
```

If no repository clearly matches, set "repository" to null.
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
