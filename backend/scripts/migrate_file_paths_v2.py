#!/usr/bin/env python3
"""
Migrate old agent_outputs to add absolute paths in git_changes.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, update
from app.database import AsyncSessionLocal
from app.models.agent_output import AgentOutput
from app.models.agent_execution import AgentExecution

FILE_STORAGE_BASE = Path.home() / ".agent-rangers"


def load_info_json(board_id: str, task_id: str) -> dict | None:
    info_path = FILE_STORAGE_BASE / "boards" / board_id / "tasks" / task_id / "outputs" / "info.json"
    if info_path.exists():
        try:
            return json.loads(info_path.read_text())
        except Exception:
            pass
    return None


async def migrate():
    async with AsyncSessionLocal() as db:
        # Get all development phase outputs
        result = await db.execute(
            select(AgentOutput).where(AgentOutput.phase == "development")
        )
        outputs = result.scalars().all()
        
        migrated = 0
        for output in outputs:
            structured = output.output_structured or {}
            git_changes = structured.get("git_changes") or {}
            
            # Get execution to find board_id
            exec_result = await db.execute(
                select(AgentExecution).where(AgentExecution.id == output.execution_id)
            )
            execution = exec_result.scalar_one_or_none()
            
            if not execution:
                print(f"Skipping {output.id} - no execution found")
                continue
            
            # Load info.json
            info_data = load_info_json(str(execution.board_id), str(output.task_id))
            if not info_data:
                print(f"Skipping {output.id} - no info.json")
                continue
            
            repo = info_data.get("repository")
            if isinstance(repo, dict):
                working_dir = repo.get("path")
            elif isinstance(repo, str):
                working_dir = repo
            else:
                print(f"Skipping {output.id} - no repository path in info.json")
                continue
            
            if not working_dir:
                print(f"Skipping {output.id} - empty working_dir")
                continue
            
            print(f"Processing {output.id} - working_dir: {working_dir}")
            
            # Update git_changes with absolute paths
            git_changes["working_directory"] = working_dir
            
            created = git_changes.get("created", [])
            modified = git_changes.get("modified", [])
            all_changed = git_changes.get("all_changed", [])
            
            if created:
                git_changes["created_absolute"] = [
                    os.path.join(working_dir, f) if not f.startswith("/") else f
                    for f in created
                ]
            
            if modified:
                git_changes["modified_absolute"] = [
                    os.path.join(working_dir, f) if not f.startswith("/") else f
                    for f in modified
                ]
            
            if all_changed:
                git_changes["all_changed"] = [
                    os.path.join(working_dir, f) if not f.startswith("/") else f
                    for f in all_changed
                ]
            
            # Update files_created
            new_files = []
            if output.files_created:
                for f in output.files_created:
                    if isinstance(f, dict):
                        f_path = f.get("path", str(f))
                    else:
                        f_path = str(f)
                    
                    if not f_path.startswith("/"):
                        new_files.append(os.path.join(working_dir, f_path))
                    else:
                        new_files.append(f_path)
            
            # Update the record
            structured["git_changes"] = git_changes
            output.output_structured = structured
            output.files_created = new_files if new_files else output.files_created
            
            # Force the update by flagging as modified
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(output, "output_structured")
            flag_modified(output, "files_created")
            
            print(f"  git_changes.working_directory = {git_changes.get('working_directory')}")
            print(f"  git_changes.modified_absolute = {git_changes.get('modified_absolute')}")
            print(f"  files_created = {output.files_created[:2] if output.files_created else None}")
            
            migrated += 1
        
        await db.commit()
        print(f"\nMigration complete. Migrated {migrated} outputs.")


if __name__ == "__main__":
    asyncio.run(migrate())
