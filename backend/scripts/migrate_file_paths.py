#!/usr/bin/env python3
"""
Migrate old agent_outputs to add working_directory for file path resolution.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.agent_output import AgentOutput
from app.models.agent_execution import AgentExecution

# File storage base directory
FILE_STORAGE_BASE = Path.home() / ".agent-rangers"


def load_info_json(board_id: str, task_id: str) -> dict | None:
    """Load info.json for a task."""
    info_path = FILE_STORAGE_BASE / "boards" / board_id / "tasks" / task_id / "outputs" / "info.json"
    if info_path.exists():
        try:
            return json.loads(info_path.read_text())
        except Exception:
            pass
    return None


async def migrate():
    """Migrate old agent_outputs to add working_directory."""
    async with AsyncSessionLocal() as db:
        # Get all development phase outputs
        result = await db.execute(
            select(AgentOutput).where(AgentOutput.phase == "development")
        )
        outputs = result.scalars().all()
        
        migrated = 0
        for output in outputs:
            # Skip if already has working_directory
            structured = output.output_structured or {}
            git_changes = structured.get("git_changes", {})
            
            if git_changes.get("working_directory"):
                print(f"Skipping {output.id} - already has working_directory")
                continue
            
            # Try to get working directory from:
            # 1. Execution context
            # 2. Task's info.json
            
            working_dir = None
            
            # Get execution
            exec_result = await db.execute(
                select(AgentExecution).where(AgentExecution.id == output.execution_id)
            )
            execution = exec_result.scalar_one_or_none()
            
            if execution:
                # Check execution context
                context = execution.context or {}
                if context.get("workspace_path"):
                    # This is the temp workspace, not the actual repo
                    pass
                
                # Try to load info.json for the task
                try:
                    info_data = load_info_json(
                        board_id=str(execution.board_id),
                        task_id=str(output.task_id),
                    )
                    if info_data:
                        repo = info_data.get("repository")
                        if isinstance(repo, dict) and repo.get("path"):
                            working_dir = repo["path"]
                        elif isinstance(repo, str):
                            working_dir = repo
                except Exception as e:
                    print(f"Error loading info.json for {output.id}: {e}")
            
            if not working_dir:
                print(f"Skipping {output.id} - could not determine working_directory")
                continue
            
            # Update the output
            if not structured:
                structured = {}
            if not git_changes:
                git_changes = {}
            
            git_changes["working_directory"] = working_dir
            
            # Also convert files_created to absolute paths if they're relative
            if output.files_created:
                new_files = []
                for f in output.files_created:
                    # Handle both string and dict formats
                    if isinstance(f, dict):
                        f_path = f.get("path", str(f))
                    else:
                        f_path = str(f)
                    
                    if not f_path.startswith("/"):
                        new_files.append(os.path.join(working_dir, f_path))
                    else:
                        new_files.append(f_path)
                output.files_created = new_files
            
            structured["git_changes"] = git_changes
            output.output_structured = structured
            
            print(f"Migrated {output.id} - working_directory: {working_dir}")
            migrated += 1
        
        await db.commit()
        print(f"\nMigration complete. Migrated {migrated} outputs.")


if __name__ == "__main__":
    asyncio.run(migrate())
