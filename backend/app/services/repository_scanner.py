"""Repository scanner service for Agent Rangers.

Scans working directories to find Git repositories and extract metadata.
"""

import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Optional

from app.services.file_storage import file_storage


# Language detection by file extension
EXTENSION_TO_LANGUAGE: dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".jsx": "JavaScript",
    ".java": "Java",
    ".kt": "Kotlin",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".cpp": "C++",
    ".c": "C",
    ".h": "C",
    ".hpp": "C++",
    ".swift": "Swift",
    ".scala": "Scala",
    ".clj": "Clojure",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".erl": "Erlang",
    ".hs": "Haskell",
    ".lua": "Lua",
    ".r": "R",
    ".R": "R",
    ".jl": "Julia",
    ".dart": "Dart",
    ".vue": "Vue",
    ".svelte": "Svelte",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "Sass",
    ".less": "Less",
    ".sql": "SQL",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".ps1": "PowerShell",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".json": "JSON",
    ".xml": "XML",
    ".md": "Markdown",
    ".rst": "reStructuredText",
}

# Directories to skip when scanning
SKIP_DIRECTORIES: set[str] = {
    "node_modules",
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    ".env",
    "env",
    ".tox",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
    "target",
    ".idea",
    ".vscode",
    ".cache",
    "vendor",
    "packages",
}


class RepositoryScannerService:
    """
    Service for scanning directories to find Git repositories.

    Provides methods to:
    - Recursively scan a directory for Git repositories
    - Extract repository metadata (name, path, remote, language)
    - Persist and load repository lists for boards
    """

    MAX_SCAN_DEPTH = 3

    def scan_working_directory(self, path: str) -> list[dict]:
        """
        Recursively find all Git repositories under the given path.

        Detects repositories by the presence of .git directories.
        Limits depth to 3 levels to avoid scanning too deep.

        Args:
            path: The root directory path to scan.

        Returns:
            List of repository info dictionaries with keys:
            - name: Repository name (directory name)
            - path: Absolute path to the repository
            - remote_url: Remote origin URL if exists, None otherwise
            - primary_language: Detected primary language
            - file_counts: Dict of file counts by extension
        """
        root_path = Path(path).resolve()

        if not root_path.exists():
            return []

        if not root_path.is_dir():
            return []

        repositories: list[dict] = []
        self._scan_recursive(root_path, root_path, 0, repositories)

        return repositories

    def _scan_recursive(
        self,
        current_path: Path,
        root_path: Path,
        depth: int,
        repositories: list[dict],
    ) -> None:
        """
        Recursively scan directories for Git repositories.

        Args:
            current_path: Current directory being scanned.
            root_path: Original root path for relative path calculation.
            depth: Current recursion depth.
            repositories: List to append found repositories to.
        """
        if depth > self.MAX_SCAN_DEPTH:
            return

        # Check if current directory is a git repository
        git_dir = current_path / ".git"
        if git_dir.exists() and git_dir.is_dir():
            repo_info = self.get_repository_info(str(current_path))
            repositories.append(repo_info)
            # Don't scan inside a git repository for nested repos
            return

        # Scan subdirectories
        try:
            for entry in current_path.iterdir():
                if entry.is_dir() and entry.name not in SKIP_DIRECTORIES:
                    self._scan_recursive(entry, root_path, depth + 1, repositories)
        except PermissionError:
            # Skip directories we can't access
            pass

    def get_repository_info(self, repo_path: str) -> dict:
        """
        Get repository metadata.

        Args:
            repo_path: Path to the Git repository.

        Returns:
            Dictionary with repository metadata:
            - name: Repository name (directory name)
            - path: Absolute path to the repository
            - remote_url: Remote origin URL if exists, None otherwise
            - primary_language: Detected primary language based on file extensions
            - file_counts: Dict mapping extensions to file counts
        """
        path = Path(repo_path).resolve()

        # Get repository name
        name = path.name

        # Get remote origin URL
        remote_url = self._get_remote_origin(path)

        # Count files by extension
        file_counts = self._count_files_by_extension(path)

        # Detect primary language
        primary_language = self._detect_primary_language(file_counts)

        return {
            "name": name,
            "path": str(path),
            "remote_url": remote_url,
            "primary_language": primary_language,
            "file_counts": file_counts,
        }

    def _get_remote_origin(self, repo_path: Path) -> Optional[str]:
        """
        Get the remote origin URL for a Git repository.

        Args:
            repo_path: Path to the Git repository.

        Returns:
            Remote origin URL string, or None if not found.
        """
        try:
            result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        return None

    def _count_files_by_extension(self, repo_path: Path) -> dict[str, int]:
        """
        Count files by their extension in a repository.

        Skips common non-source directories.

        Args:
            repo_path: Path to the Git repository.

        Returns:
            Dictionary mapping file extensions to counts.
        """
        extension_counts: Counter[str] = Counter()

        def scan_dir(dir_path: Path, depth: int = 0) -> None:
            if depth > 5:  # Limit depth for file counting
                return

            try:
                for entry in dir_path.iterdir():
                    if entry.name in SKIP_DIRECTORIES:
                        continue

                    if entry.is_file():
                        ext = entry.suffix.lower()
                        if ext:
                            extension_counts[ext] += 1
                    elif entry.is_dir():
                        scan_dir(entry, depth + 1)
            except PermissionError:
                pass

        scan_dir(repo_path)
        return dict(extension_counts)

    def _detect_primary_language(self, file_counts: dict[str, int]) -> Optional[str]:
        """
        Detect the primary programming language based on file extension counts.

        Args:
            file_counts: Dictionary mapping extensions to counts.

        Returns:
            Primary language name, or None if not detected.
        """
        language_counts: Counter[str] = Counter()

        for ext, count in file_counts.items():
            language = EXTENSION_TO_LANGUAGE.get(ext)
            if language:
                language_counts[language] += count

        if not language_counts:
            return None

        # Return the most common language
        return language_counts.most_common(1)[0][0]

    def save_repositories(self, board_id: str, repos: list[dict]) -> None:
        """
        Save repository list to the board's storage.

        Writes to ~/.agent-rangers/boards/{board_id}/repositories.jsonl

        Args:
            board_id: The UUID of the board as a string.
            repos: List of repository info dictionaries.
        """
        board_dir = file_storage.get_board_dir(board_id)
        repos_file = board_dir / "repositories.jsonl"

        lines = [json.dumps(repo, ensure_ascii=False) for repo in repos]
        content = "\n".join(lines)

        if content:
            content += "\n"

        repos_file.write_text(content, encoding="utf-8")

    def load_repositories(self, board_id: str) -> list[dict]:
        """
        Load repository list from the board's storage.

        Reads from ~/.agent-rangers/boards/{board_id}/repositories.jsonl

        Args:
            board_id: The UUID of the board as a string.

        Returns:
            List of repository info dictionaries, or empty list if file doesn't exist.
        """
        board_dir = file_storage.base_dir / "boards" / board_id
        repos_file = board_dir / "repositories.jsonl"

        if not repos_file.exists():
            return []

        content = repos_file.read_text(encoding="utf-8")
        repos: list[dict] = []

        for line in content.strip().split("\n"):
            if line:
                try:
                    repos.append(json.loads(line))
                except json.JSONDecodeError:
                    # Skip malformed lines
                    continue

        return repos


# Global singleton instance
repository_scanner = RepositoryScannerService()
