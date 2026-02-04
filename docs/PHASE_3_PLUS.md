# Phase 3+ Implementation Plan

## Overview

Phase 3+ introduces standardized file storage, repository awareness, and automatic task evaluation. This phase sits between the current Phase 3 (Agent Integration) and Phase 4 (Advanced Features).

---

## 1. Standardized App Directory Structure

### Directory Layout
```
~/.agent-rangers/
├── config.json                          # Global configuration
├── boards/
│   └── {board_id}/
│       ├── board.json                   # Board metadata (working_directory, etc.)
│       ├── repositories.jsonl           # Scanned repositories
│       └── tasks/
│           └── {task_id}/
│               └── outputs/
│                   ├── info.json        # Task evaluation result (repository, context)
│                   ├── architecture.md  # Planning phase output
│                   ├── review.md        # Review phase output
│                   └── code/            # Generated code artifacts
└── logs/                                # Application logs
```

### config.json Schema
```json
{
  "version": "1.0",
  "claude": {
    "model": "claude-sonnet-4-20250514",
    "maxTokens": 8192
  },
  "defaults": {
    "maxIterations": 3,
    "workflowType": "quick_development"
  }
}
```

### board.json Schema
```json
{
  "id": "uuid",
  "name": "Board Name",
  "working_directory": "/path/to/projects",
  "created_at": "2026-02-04T00:00:00Z",
  "updated_at": "2026-02-04T00:00:00Z"
}
```

### repositories.jsonl Schema (one JSON per line)
```jsonl
{"path": "/path/to/projects/repo1", "name": "repo1", "scanned_at": "2026-02-04T00:00:00Z"}
{"path": "/path/to/projects/repo2", "name": "repo2", "scanned_at": "2026-02-04T00:00:00Z"}
```

### info.json Schema (Task Evaluation Result)
```json
{
  "task_id": "uuid",
  "evaluated_at": "2026-02-04T00:00:00Z",
  "repository": {
    "path": "/path/to/projects/repo1",
    "name": "repo1",
    "confidence": 0.95,
    "reasoning": "Task mentions 'frontend' and 'React', repo1 is a React frontend project"
  },
  "context": {
    "relevant_files": ["src/components/", "src/hooks/"],
    "technologies": ["React", "TypeScript"],
    "suggested_approach": "Modify existing component structure"
  }
}
```

---

## 2. Implementation Tasks

### 2.1 Backend: File Storage Service

**File: `backend/app/services/file_storage.py`**

```python
class FileStorageService:
    """Manages ~/.agent-rangers directory structure."""
    
    def __init__(self):
        self.base_dir = Path.home() / ".agent-rangers"
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create base directory structure."""
        
    def get_board_dir(self, board_id: str) -> Path:
        """Get/create board directory."""
        
    def get_task_outputs_dir(self, board_id: str, task_id: str) -> Path:
        """Get/create task outputs directory."""
        
    def save_output(self, board_id: str, task_id: str, filename: str, content: str):
        """Save output file to task outputs directory."""
        
    def load_output(self, board_id: str, task_id: str, filename: str) -> str | None:
        """Load output file from task outputs directory."""
        
    def get_config(self) -> dict:
        """Load global config.json."""
        
    def save_config(self, config: dict):
        """Save global config.json."""
```

### 2.2 Backend: Repository Scanner Service

**File: `backend/app/services/repository_scanner.py`**

```python
class RepositoryScannerService:
    """Scans and manages repository information for boards."""
    
    def scan_working_directory(self, working_dir: str) -> list[dict]:
        """
        Scan working directory for git repositories.
        Returns list of {path, name, scanned_at}.
        """
        
    def save_repositories(self, board_id: str, repositories: list[dict]):
        """Save repositories to ~/.agent-rangers/boards/{board_id}/repositories.jsonl"""
        
    def load_repositories(self, board_id: str) -> list[dict]:
        """Load repositories from jsonl file."""
        
    def get_repository_info(self, repo_path: str) -> dict:
        """Get detailed info about a repository (languages, structure, etc.)"""
```

### 2.3 Backend: Task Evaluator Service

**File: `backend/app/services/task_evaluator.py`**

```python
class TaskEvaluatorService:
    """Evaluates tasks to determine relevant repository and context."""
    
    def __init__(self, llm_provider, file_storage, repo_scanner):
        self.llm = llm_provider
        self.storage = file_storage
        self.scanner = repo_scanner
    
    async def evaluate_task(self, board_id: str, task: Task) -> dict:
        """
        Evaluate a task to determine:
        - Which repository is relevant
        - What context/files might be involved
        - Suggested approach
        
        Saves result to info.json and returns it.
        """
        
    def _build_evaluation_prompt(self, task: Task, repositories: list[dict]) -> str:
        """Build prompt for LLM to evaluate task."""
        
    def _parse_evaluation_response(self, response: str) -> dict:
        """Parse LLM response into structured info.json format."""
```

### 2.4 Backend: Board Working Directory

**Database Migration: Add `working_directory` to Board model**

```python
# In Board model
working_directory: Mapped[str | None] = mapped_column(
    String(500),
    nullable=True,
    doc="Root directory containing repositories for this board"
)
```

**API Endpoints:**

```python
# PATCH /api/boards/{board_id}/working-directory
@router.patch("/{board_id}/working-directory")
async def set_working_directory(board_id: str, body: SetWorkingDirectoryRequest):
    """Set working directory and trigger repository scan."""
    
# GET /api/boards/{board_id}/repositories
@router.get("/{board_id}/repositories")
async def get_repositories(board_id: str):
    """Get scanned repositories for a board."""
    
# POST /api/boards/{board_id}/repositories/scan
@router.post("/{board_id}/repositories/scan")
async def scan_repositories(board_id: str):
    """Re-scan repositories in working directory."""
```

### 2.5 Backend: Evaluate Workflow

**New Workflow Type: `evaluate`**

```python
# Add to WorkflowType enum
class WorkflowType(str, Enum):
    DEVELOPMENT = "development"
    QUICK_DEVELOPMENT = "quick_development"
    ARCHITECTURE_ONLY = "architecture_only"
    EVALUATE = "evaluate"  # NEW
```

**Auto-trigger on Task Create/Update:**

```python
# In task creation/update endpoint
async def create_task(...):
    task = await task_service.create(...)
    
    # Auto-run evaluate workflow
    await workflow_service.start_workflow(
        task_id=task.id,
        workflow_type="evaluate",
        auto_triggered=True
    )
    
    return task
```

### 2.6 Backend: Workflow Execution Context

**Modify AgentRunner to use repository from info.json:**

```python
class AgentRunner:
    async def run_phase(self, execution: AgentExecution, phase: str):
        # Load info.json to get repository path
        info = self.storage.load_output(
            execution.board_id, 
            execution.task_id, 
            "info.json"
        )
        
        if info and info.get("repository", {}).get("path"):
            working_dir = info["repository"]["path"]
        else:
            working_dir = self._get_default_workspace(execution.task_id)
        
        # Spawn Claude CLI at the repository path
        await self._spawn_agent(
            working_dir=working_dir,
            phase=phase,
            context=self._build_context(execution, phase)
        )
```

### 2.7 Frontend: Board Settings

**Add Working Directory Setting:**

```tsx
// In BoardSettingsDialog or similar
<div>
  <Label>Working Directory</Label>
  <Input 
    value={workingDirectory}
    onChange={setWorkingDirectory}
    placeholder="/path/to/projects"
  />
  <Button onClick={handleScan}>Scan Repositories</Button>
</div>

// Show scanned repositories
<div>
  <h4>Repositories ({repositories.length})</h4>
  <ul>
    {repositories.map(repo => (
      <li key={repo.path}>{repo.name} - {repo.path}</li>
    ))}
  </ul>
</div>
```

### 2.8 Frontend: Task Info Display

**Show evaluation result in TaskCard/TaskDetails:**

```tsx
// Show which repository task is linked to
{task.info?.repository && (
  <Badge variant="outline">
    📁 {task.info.repository.name}
  </Badge>
)}
```

---

## 3. Implementation Order

### Step 1: File Storage Foundation
1. Create `FileStorageService`
2. Create `~/.agent-rangers` directory structure
3. Migrate existing workspace outputs to new structure
4. Update `AgentRunner` to use new output paths

### Step 2: Repository Scanning
1. Add `working_directory` to Board model (migration)
2. Create `RepositoryScannerService`
3. Add API endpoints for working directory and repositories
4. Frontend: Add board settings for working directory

### Step 3: Task Evaluation Workflow
1. Create `TaskEvaluatorService`
2. Add `evaluate` workflow type
3. Auto-trigger evaluate on task create/update
4. Store result in `info.json`

### Step 4: Workflow Integration
1. Modify `AgentRunner` to read `info.json`
2. Spawn Claude CLI in repository directory
3. Update existing workflows to use repository context

### Step 5: Frontend Polish
1. Show repository info in task cards
2. Allow manual re-evaluation
3. Show evaluation confidence/reasoning

---

## 4. Database Migration

```python
"""Add working_directory to boards

Revision ID: xxxx
"""

def upgrade():
    op.add_column('boards', sa.Column('working_directory', sa.String(500), nullable=True))

def downgrade():
    op.drop_column('boards', 'working_directory')
```

---

## 5. API Changes Summary

### New Endpoints
- `PATCH /api/boards/{board_id}/working-directory` - Set working directory
- `GET /api/boards/{board_id}/repositories` - List repositories
- `POST /api/boards/{board_id}/repositories/scan` - Trigger scan
- `GET /api/tasks/{task_id}/evaluation` - Get task evaluation
- `POST /api/tasks/{task_id}/evaluate` - Re-run evaluation

### Modified Endpoints
- `POST /api/boards/{board_id}/tasks` - Auto-triggers evaluate workflow
- `PATCH /api/tasks/{task_id}` - Auto-triggers evaluate workflow on title/description change

---

## 6. Testing Checklist

- [ ] FileStorageService creates proper directory structure
- [ ] Repository scanner finds git repos correctly
- [ ] Repositories.jsonl is written/read correctly
- [ ] Evaluate workflow runs on task create
- [ ] LLM correctly identifies relevant repository
- [ ] info.json is saved with proper structure
- [ ] AgentRunner spawns in correct repository
- [ ] Frontend displays repository info
- [ ] Working directory setting saves and triggers scan

---

## 7. Future Considerations

- **Multi-repo tasks**: Some tasks may span multiple repositories
- **Repository caching**: Cache repo metadata to speed up evaluation
- **File-level context**: info.json could include specific files to focus on
- **Learning from history**: Use past task→repo mappings to improve accuracy
