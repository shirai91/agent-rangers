"""File storage service for Agent Rangers.

Manages the ~/.agent-rangers/ directory structure for storing board configurations,
task outputs, and application-wide settings.
"""

import json
import threading
from pathlib import Path
from typing import Optional, Any


class FileStorageService:
    """
    Service for managing file storage in ~/.agent-rangers/ directory.

    Provides thread-safe file operations for storing and retrieving board data,
    task outputs, and application configuration.

    Directory structure:
        ~/.agent-rangers/
        ├── config.json
        ├── boards/
        │   └── {board_id}/
        │       ├── board.json
        │       ├── repositories.jsonl
        │       └── tasks/
        │           └── {task_id}/
        │               └── outputs/
        └── logs/
    """

    _instance: Optional["FileStorageService"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "FileStorageService":
        """Singleton pattern for thread-safe access."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize the file storage service."""
        if self._initialized:
            return

        self._base_dir = Path.home() / ".agent-rangers"
        self._file_lock = threading.Lock()
        self._initialized = True

    def initialize(self) -> None:
        """
        Initialize the directory structure on startup.

        Creates the base directory and subdirectories if they don't exist.
        Also creates a default config.json if it doesn't exist.
        """
        with self._file_lock:
            # Create base directory structure
            self._base_dir.mkdir(parents=True, exist_ok=True)
            (self._base_dir / "boards").mkdir(exist_ok=True)
            (self._base_dir / "logs").mkdir(exist_ok=True)

            # Create default config if it doesn't exist
            config_path = self._base_dir / "config.json"
            if not config_path.exists():
                default_config = {
                    "version": "1.0.0",
                    "default_working_directory": None,
                    "agent_defaults": {
                        "timeout_seconds": 300,
                        "max_retries": 3,
                    },
                }
                config_path.write_text(
                    json.dumps(default_config, indent=2), encoding="utf-8"
                )

    @property
    def base_dir(self) -> Path:
        """Get the base directory path."""
        return self._base_dir

    def get_board_dir(self, board_id: str) -> Path:
        """
        Get the directory path for a specific board.

        Creates the directory structure if it doesn't exist.

        Args:
            board_id: The UUID of the board as a string.

        Returns:
            Path to the board directory.
        """
        board_dir = self._base_dir / "boards" / board_id
        with self._file_lock:
            board_dir.mkdir(parents=True, exist_ok=True)
            (board_dir / "tasks").mkdir(exist_ok=True)
        return board_dir

    def get_task_outputs_dir(self, board_id: str, task_id: str) -> Path:
        """
        Get the outputs directory path for a specific task.

        Creates the directory structure if it doesn't exist.

        Args:
            board_id: The UUID of the board as a string.
            task_id: The UUID of the task as a string.

        Returns:
            Path to the task outputs directory.
        """
        outputs_dir = (
            self._base_dir / "boards" / board_id / "tasks" / task_id / "outputs"
        )
        with self._file_lock:
            outputs_dir.mkdir(parents=True, exist_ok=True)
        return outputs_dir

    def save_output(
        self, board_id: str, task_id: str, filename: str, content: str
    ) -> Path:
        """
        Save output content to a file in the task outputs directory.

        Args:
            board_id: The UUID of the board as a string.
            task_id: The UUID of the task as a string.
            filename: The name of the file to save.
            content: The content to write to the file.

        Returns:
            Path to the saved file.

        Raises:
            ValueError: If filename contains path separators or is invalid.
        """
        # Validate filename to prevent directory traversal
        if "/" in filename or "\\" in filename or ".." in filename:
            raise ValueError(
                f"Invalid filename: {filename}. "
                "Filename cannot contain path separators or '..'."
            )

        outputs_dir = self.get_task_outputs_dir(board_id, task_id)
        file_path = outputs_dir / filename

        with self._file_lock:
            file_path.write_text(content, encoding="utf-8")

        return file_path

    def load_output(
        self, board_id: str, task_id: str, filename: str
    ) -> Optional[str]:
        """
        Load output content from a file in the task outputs directory.

        Args:
            board_id: The UUID of the board as a string.
            task_id: The UUID of the task as a string.
            filename: The name of the file to load.

        Returns:
            The file content as a string, or None if the file doesn't exist.

        Raises:
            ValueError: If filename contains path separators or is invalid.
        """
        # Validate filename to prevent directory traversal
        if "/" in filename or "\\" in filename or ".." in filename:
            raise ValueError(
                f"Invalid filename: {filename}. "
                "Filename cannot contain path separators or '..'."
            )

        outputs_dir = self._base_dir / "boards" / board_id / "tasks" / task_id / "outputs"
        file_path = outputs_dir / filename

        with self._file_lock:
            if not file_path.exists():
                return None
            return file_path.read_text(encoding="utf-8")

    def get_config(self) -> dict[str, Any]:
        """
        Get the application configuration.

        Returns:
            The configuration dictionary.
        """
        config_path = self._base_dir / "config.json"

        with self._file_lock:
            if not config_path.exists():
                return {}
            content = config_path.read_text(encoding="utf-8")
            return json.loads(content)

    def save_config(self, config: dict[str, Any]) -> None:
        """
        Save the application configuration.

        Args:
            config: The configuration dictionary to save.
        """
        config_path = self._base_dir / "config.json"

        with self._file_lock:
            config_path.write_text(
                json.dumps(config, indent=2), encoding="utf-8"
            )

    def delete_task_outputs(self, board_id: str, task_id: str) -> bool:
        """
        Delete all outputs for a specific task.

        Args:
            board_id: The UUID of the board as a string.
            task_id: The UUID of the task as a string.

        Returns:
            True if the directory was deleted, False if it didn't exist.
        """
        import shutil

        outputs_dir = (
            self._base_dir / "boards" / board_id / "tasks" / task_id / "outputs"
        )

        with self._file_lock:
            if outputs_dir.exists():
                shutil.rmtree(outputs_dir)
                return True
            return False

    def list_task_outputs(self, board_id: str, task_id: str) -> list[str]:
        """
        List all output files for a specific task.

        Args:
            board_id: The UUID of the board as a string.
            task_id: The UUID of the task as a string.

        Returns:
            List of filenames in the outputs directory.
        """
        outputs_dir = (
            self._base_dir / "boards" / board_id / "tasks" / task_id / "outputs"
        )

        with self._file_lock:
            if not outputs_dir.exists():
                return []
            return [f.name for f in outputs_dir.iterdir() if f.is_file()]


# Global singleton instance
file_storage = FileStorageService()
