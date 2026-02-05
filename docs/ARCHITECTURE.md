# AI Multi-Agent Kanban Framework
## Technical Architecture v3.0

**Version:** 3.0
**Last Updated:** February 2026
**Author:** Tùng Phạm

---

## Executive Summary

This document outlines the architecture for building an AI-powered software development framework featuring a Trello-like Kanban dashboard with multiple specialized agents (Software Architect, Developer, Code Reviewer) that collaborate to complete development tasks.

**Key Architecture Decisions:**

1. **Provider Abstraction Layer (PAL)** - Flexible AI backend selection supporting:
   - OAuth (Claude Code CLI) - Uses Claude Max subscription (FREE!)
   - API (Anthropic) - Pay-as-you-go
   - Local (Ollama) - Completely free, self-hosted

2. **AgentOrchestrator + AgentWorkflowService** - Two-tier orchestration:
   - `AgentOrchestrator` handles low-level agent execution
   - `AgentWorkflowService` manages workflow-level operations

3. **Repository Awareness System** - Intelligent task-to-repository matching:
   - `RepositoryScannerService` discovers Git repositories
   - `TaskEvaluatorService` uses LLM to match tasks to repos

4. **File Storage Layer** - Persistent storage at `~/.agent-rangers/`

---

## Table of Contents
1. [High-Level System Architecture](#high-level-system-architecture)
2. [Technology Stack](#technology-stack)
3. [Provider Abstraction Layer](#provider-abstraction-layer)
4. [Agent Orchestration](#agent-orchestration)
5. [Repository Awareness System](#repository-awareness-system)
6. [Agent Definitions & Workflows](#agent-definitions--workflows)
7. [Activity Logging & Real-Time Updates](#activity-logging--real-time-updates)
8. [File Storage Structure](#file-storage-structure)
9. [Database Schema](#database-schema)
10. [Frontend Architecture](#frontend-architecture)
11. [Implementation Roadmap](#implementation-roadmap)
12. [Key Challenges & Solutions](#key-challenges--solutions)

---

## High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER                                │
│                  React 19 + Vite + shadcn/ui + @dnd-kit + Zustand          │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │                         Kanban Board UI                                │ │
│ │  ├── Drag-and-drop columns & cards (@dnd-kit)                         │ │
│ │  ├── Agent status indicators (AgentStatusBadge, AgentStatusIndicator) │ │
│ │  ├── Real-time activity log panel (ActivityFeed)                      │ │
│ │  ├── Streaming output viewer (StreamingOutput, AgentOutputViewer)     │ │
│ │  ├── Board settings with working directory (BoardSettingsDialog)      │ │
│ │  └── Agent control panel (AgentControlPanel)                          │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │ WebSocket + REST API
┌────────────────────────────────▼────────────────────────────────────────────┐
│                          ORCHESTRATION LAYER                                │
│                          FastAPI + Python 3.12+                             │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │                     Agent Orchestration                               │ │
│ │  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────────┐  │ │
│ │  │ AgentWorkflow   │ │ Agent           │ │   Activity Logger       │  │ │
│ │  │ Service         │ │ Orchestrator    │ │   (Redis Pub/Sub)       │  │ │
│ │  └────────┬────────┘ └────────┬────────┘ └────────────┬────────────┘  │ │
│ │           │                   │                       │               │ │
│ │  ┌────────▼───────────────────▼───────────────────────▼────────────┐  │ │
│ │  │                 PROVIDER ABSTRACTION LAYER                      │  │ │
│ │  │  ┌────────────────────────────────────────────────────────────┐ │  │ │
│ │  │  │  ProviderFactory → BaseProvider implementations            │ │  │ │
│ │  │  │  ├── ClaudeOAuthProvider (claude-code CLI, Max sub)        │ │  │ │
│ │  │  │  ├── AnthropicAPIProvider (direct API, pay-as-you-go)      │ │  │ │
│ │  │  │  └── OllamaProvider (local, self-hosted)                   │ │  │ │
│ │  │  └────────────────────────────────────────────────────────────┘ │  │ │
│ │  │                                                                  │  │ │
│ │  │  ┌────────────────────────────────────────────────────────────┐ │  │ │
│ │  │  │  Repository Awareness System                               │ │  │ │
│ │  │  │  ├── RepositoryScannerService (discovers Git repos)        │ │  │ │
│ │  │  │  └── TaskEvaluatorService (LLM-based repo matching)        │ │  │ │
│ │  │  └────────────────────────────────────────────────────────────┘ │  │ │
│ │  └──────────────────────────────────────────────────────────────────┘ │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────────────┐
│                             DATA LAYER                                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────────────────┐ │
│  │  PostgreSQL 16   │  │     Redis 7      │  │   File Storage             │ │
│  │  + pgvector      │  │   • Pub/Sub      │  │   ~/.agent-rangers/        │ │
│  │  • Tasks, Boards │  │   • Cache        │  │   • Board configs          │ │
│  │  • Workflows     │  │   • Sessions     │  │   • Repository lists       │ │
│  │  • Executions    │  │   • Activity     │  │   • Task outputs           │ │
│  │  • Agent Outputs │  │     streams      │  │   • Evaluation results     │ │
│  └──────────────────┘  └──────────────────┘  └────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Frontend
| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Framework** | React 19 + Vite 6 | Fast HMR, modern React features, TypeScript |
| **UI Components** | shadcn/ui + Tailwind CSS v4 | Copy-paste components, Radix primitives |
| **State Management** | Zustand | ~3KB, hook-based, Redux DevTools compatible |
| **Drag-and-Drop** | @dnd-kit/core + @dnd-kit/sortable | Actively maintained, accessible, 60fps |
| **Forms** | react-hook-form + zod | Type-safe validation |
| **Real-time** | Native WebSocket + Zustand middleware | Direct FastAPI WebSocket connection |

### Backend
| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Framework** | FastAPI 0.115+ | Native async, OpenAPI docs, Pydantic |
| **Runtime** | Python 3.12+ | Best AI/ML ecosystem compatibility |
| **ASGI Server** | Uvicorn 0.30+ | High-performance async, WebSocket support |
| **ORM** | SQLAlchemy 2.0 + asyncpg | Async PostgreSQL, Alembic migrations |
| **AI Integration** | Provider Abstraction Layer | Flexible backend selection |

### Infrastructure
| Component | Choice | Configuration |
|-----------|--------|---------------|
| **Database** | PostgreSQL 16 | With pgvector extension |
| **Cache/Pub-Sub** | Redis 7 | Real-time updates, activity streams |
| **Embeddings** | Ollama + nomic-embed-text | Self-hosted, 768 dimensions (optional) |
| **Containerization** | Docker Compose | Single-command deployment |

---

## Provider Abstraction Layer

### Overview

The Provider Abstraction Layer (PAL) enables flexible AI backend selection without code changes:

```
                    ProviderFactory
                         │
           ┌─────────────┼─────────────┐
           │             │             │
           ▼             ▼             ▼
    ClaudeOAuth    AnthropicAPI    Ollama
    Provider        Provider       Provider
         │             │             │
         └─────────────┼─────────────┘
                       │
                  BaseProvider
                  (abstract)
```

### Provider Types

| Provider | Type Key | Cost | Best For |
|----------|----------|------|----------|
| **ClaudeOAuthProvider** | `claude-code` | FREE (Max sub) | All phases with CLI tooling |
| **AnthropicAPIProvider** | `anthropic` | Pay-as-you-go | Direct API access |
| **OllamaProvider** | `ollama` | FREE | Local development, offline use |

### Configuration

Providers are configured via environment variables or JSON config:

```python
# Environment-based configuration
AI_PROVIDER_MODE: str = "auto"  # oauth, api, local, auto
ANTHROPIC_API_KEY: str = ""
ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
OLLAMA_URL: str = "http://localhost:11434"
OLLAMA_MODEL: str = "qwen2.5-coder:32b"

# JSON configuration (advanced)
AI_PROVIDERS_CONFIG = {
    "architect": {"type": "claude-code", "model": "claude-sonnet-4-20250514"},
    "developer": {"type": "claude-code", "model": "claude-sonnet-4-20250514", "allowed_tools": ["Read", "Write", "Edit", "Bash"]},
    "reviewer": {"type": "ollama", "model": "qwen2.5-coder:32b"}
}
```

### BaseProvider Interface

```python
class BaseProvider(ABC):
    """Abstract base class for all AI providers."""

    @property
    @abstractmethod
    def provider_type(self) -> str: ...

    @property
    @abstractmethod
    def supports_streaming(self) -> bool: ...

    @abstractmethod
    async def complete(
        self,
        messages: List[Message],
        system: Optional[str] = None,
        **kwargs,
    ) -> CompletionResponse: ...

    @abstractmethod
    async def stream(
        self,
        messages: List[Message],
        system: Optional[str] = None,
        **kwargs,
    ) -> AsyncIterator[StreamEvent]: ...
```

---

## Agent Orchestration

### Two-Tier Architecture

The system uses a two-tier orchestration architecture:

```
┌───────────────────────────────────────────────────────────────┐
│                   AgentWorkflowService                        │
│  Higher-level workflow orchestration                          │
│  ├── Phase-specific execution (architecture, dev, review)     │
│  ├── Feedback loop handling                                   │
│  ├── Workflow status tracking                                 │
│  └── Workflow recommendations                                 │
└────────────────────────────┬──────────────────────────────────┘
                             │
                             ▼
┌───────────────────────────────────────────────────────────────┐
│                   AgentOrchestrator                           │
│  Low-level agent execution                                    │
│  ├── Execution lifecycle (create, start, complete, fail)      │
│  ├── Phase execution (_run_agent_phase)                       │
│  ├── CLI spawning for developer agent                         │
│  ├── Provider integration                                     │
│  └── Real-time streaming via WebSocket                        │
└───────────────────────────────────────────────────────────────┘
```

### Workflow Types

| Workflow Type | Phases | Use Case |
|---------------|--------|----------|
| `development` | Architecture → Development → Review | Full implementation workflow |
| `quick_development` | Development → Review | Skip architecture, quick fixes |
| `architecture_only` | Architecture | Planning phase only |
| `review_only` | Review | Standalone code review |

### AgentOrchestrator Key Methods

```python
class AgentOrchestrator:
    # Execution lifecycle
    async def create_execution(db, task_id, board_id, workflow_type, context) -> AgentExecution
    async def start_execution(db, execution_id) -> AgentExecution
    async def get_execution_status(db, execution_id) -> dict

    # Phase execution
    async def _run_agent_phase(db, execution, task, phase, context) -> AgentOutput

    # CLI spawning (for developer phase)
    async def _execute_developer_cli(execution_id, task, context) -> AgentOutput
```

### AgentWorkflowService Key Methods

```python
class AgentWorkflowService:
    # Phase-specific execution
    async def start_architecture_phase(db, task_id, context) -> AgentExecution
    async def start_development_phase(db, task_id, context) -> AgentExecution
    async def start_review_phase(db, task_id, context) -> AgentExecution

    # Feedback handling
    async def handle_review_feedback(db, execution_id, approved, feedback_notes) -> AgentExecution

    # Workflow intelligence
    async def get_recommended_workflow(db, task) -> dict
    async def get_workflow_status(db, execution_id) -> dict
```

---

## Repository Awareness System

### Overview

The Repository Awareness System enables intelligent task-to-repository matching:

```
┌──────────────────────────────────────────────────────────────────┐
│                   Repository Awareness Flow                      │
│                                                                  │
│  Board Working Directory                                         │
│         │                                                        │
│         ▼                                                        │
│  RepositoryScannerService                                        │
│  • Recursively finds .git directories (max depth: 3)             │
│  • Extracts metadata (name, remote, language, file counts)       │
│  • Saves to ~/.agent-rangers/boards/{id}/repositories.jsonl      │
│         │                                                        │
│         ▼                                                        │
│  TaskEvaluatorService                                            │
│  • Uses LLM to analyze task vs repositories                      │
│  • Detects branch from task text or uses default (main/master)   │
│  • Saves result to ~/.agent-rangers/boards/{id}/tasks/{id}/info.json │
│         │                                                        │
│         ▼                                                        │
│  Agent Context                                                   │
│  • Repository path injected into developer context               │
│  • Branch checkout handled automatically                         │
│  • Git integration (auto-commit, branch detection)               │
└──────────────────────────────────────────────────────────────────┘
```

### RepositoryScannerService

```python
class RepositoryScannerService:
    MAX_SCAN_DEPTH = 3

    def scan_working_directory(self, path: str) -> list[dict]:
        """Recursively find all Git repositories under the given path."""

    def get_repository_info(self, repo_path: str) -> dict:
        """Get repository metadata (name, path, remote, language, file counts)."""

    def save_repositories(self, board_id: str, repos: list[dict]) -> None:
        """Save repository list to ~/.agent-rangers/boards/{board_id}/repositories.jsonl"""

    def load_repositories(self, board_id: str) -> list[dict]:
        """Load repository list from storage."""
```

### TaskEvaluatorService

```python
class TaskEvaluatorService:
    async def evaluate_task(
        self,
        board_id: str,
        task_id: str,
        task_title: str,
        task_description: str,
    ) -> dict:
        """
        Evaluate which repository and branch a task relates to.

        Returns:
            {
                "task_id": "uuid",
                "evaluated_at": "ISO timestamp",
                "repository": {
                    "path": "/path/to/repo",
                    "name": "repo-name",
                    "confidence": 0.95,
                    "reasoning": "Task mentions X which relates to repo Y"
                } or null,
                "branch": {
                    "name": "feature/login",
                    "source": "task_text" | "llm_suggestion" | "default",
                    "available_branches": [...]
                },
                "context": {
                    "relevant_files": [],
                    "technologies": []
                }
            }
        """
```

### Branch Detection Priority

1. **Explicit mention** in task title/description (patterns: `branch: X`, `on branch X`, `feature/X`)
2. **LLM suggestion** from task analysis
3. **Default branch** (main/master with most recent commit)

---

## Agent Definitions & Workflows

### Agent Types

| Agent | Provider Mode | Primary Tools | Use Case |
|-------|---------------|---------------|----------|
| **Software Architect** | API/OAuth | Text output | Planning, design documents |
| **Software Developer** | CLI Spawning | Read, Write, Edit, Bash, Git | Code implementation |
| **Code Reviewer** | API/OAuth | Text output | Code review, recommendations |
| **Task Evaluator** | API/OAuth | Text output | Repository matching |

### Workflow Sequence

```
Task Starts
    │
    ▼
┌─────────────────────────────────────┐
│  PHASE 1: Architecture              │
│  ────────────────────────────────   │
│  Provider: API/OAuth                │
│  Agent: Software Architect          │
│  Output: ARCHITECTURE.md            │
│  Features: Repository context       │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  PHASE 2: Development               │
│  ────────────────────────────────   │
│  Provider: Claude CLI               │
│  Agent: Software Developer          │
│  Output: Source files, tests        │
│  Features:                          │
│  • Repository awareness             │
│  • Auto branch checkout             │
│  • Auto git commit                  │
│  • File change tracking             │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  PHASE 3: Review                    │
│  ────────────────────────────────   │
│  Provider: API/OAuth                │
│  Agent: Code Reviewer               │
│  Output: REVIEW.md + recommendations│
└─────────────────────────────────────┘
    │
    ▼
Task Complete (or Feedback Loop)
```

### Git Integration Features

- **Auto-commit**: Changes automatically committed after developer agent completes
- **Branch detection**: Automatically detects and checks out the appropriate branch
- **Branch auto-creation**: Creates branch if explicitly mentioned but doesn't exist
- **File change tracking**: Tracks which files were created/modified during execution

---

## Activity Logging & Real-Time Updates

### Activity Types

| Type | Phase | Description |
|------|-------|-------------|
| `workflow_phase_started` | All | Agent begins working on phase |
| `workflow_phase_completed` | All | Agent finishes phase |
| `workflow_approved` | Review | User approves the implementation |
| `workflow_feedback_iteration` | Review | User requests changes |
| `file_created` | Arch/Dev | New file created |
| `file_edit` | Review | File modified |
| `tool_call` | Dev | CLI agent uses a tool |
| `tool_result` | Dev | Tool execution result |
| `agent_message` | All | Agent thinking/progress |
| `execution_milestone` | All | Major progress milestone |

### Real-Time Streaming

```
┌────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│ Agent Process  │ ──► │  Redis Pub/Sub  │ ──► │    WebSocket     │
│ (stdout/events)│     │  (channel per   │     │  Manager         │
└────────────────┘     │   board)        │     │  (broadcasts to  │
                       └─────────────────┘     │   connected      │
                                               │   clients)       │
                                               └──────────────────┘
```

WebSocket Events:
- `execution_started` - New execution begins
- `execution_updated` - Execution status/phase changes
- `execution_completed` - Execution finishes (success or failure)
- `execution_milestone` - Major progress update (e.g., "Analyzing codebase...")

---

## File Storage Structure

```
~/.agent-rangers/
├── config.json                           # Application configuration
├── boards/
│   └── {board_id}/
│       ├── board.json                    # Board-specific settings
│       ├── repositories.jsonl            # Discovered repositories
│       └── tasks/
│           └── {task_id}/
│               └── outputs/
│                   ├── info.json         # Task evaluation result
│                   ├── ARCHITECTURE.md   # Architect output
│                   ├── REVIEW.md         # Reviewer output
│                   └── ...               # Other artifacts
└── logs/                                 # Application logs
```

### FileStorageService

```python
class FileStorageService:
    """Singleton service for file storage at ~/.agent-rangers/"""

    @property
    def base_dir(self) -> Path

    def get_board_dir(self, board_id: str) -> Path
    def get_task_outputs_dir(self, board_id: str, task_id: str) -> Path
    def save_output(self, board_id, task_id, filename, content) -> Path
    def load_output(self, board_id, task_id, filename) -> Optional[str]
    def list_task_outputs(self, board_id, task_id) -> list[str]
    def delete_task_outputs(self, board_id, task_id) -> bool
```

---

## Database Schema

### Core Tables

```
┌──────────────────────────────────────────────────────────────────┐
│                          boards                                  │
├──────────────────────────────────────────────────────────────────┤
│ id              UUID PK                                          │
│ name            VARCHAR(255) NOT NULL                            │
│ description     TEXT                                             │
│ working_directory VARCHAR(1024)    ← NEW: For repo scanning     │
│ settings        JSONB DEFAULT '{}'                               │
│ created_at      TIMESTAMP                                        │
│ updated_at      TIMESTAMP                                        │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                          columns                                 │
├──────────────────────────────────────────────────────────────────┤
│ id              UUID PK                                          │
│ board_id        UUID FK → boards.id                              │
│ name            VARCHAR(255) NOT NULL                            │
│ order           INTEGER NOT NULL                                 │
│ color           VARCHAR(50)                                      │
│ wip_limit       INTEGER                                          │
│ triggers_agents BOOLEAN DEFAULT false                            │
│ agent_workflow_type VARCHAR(50)                                  │
│ is_start_column BOOLEAN DEFAULT false                            │
│ is_end_column   BOOLEAN DEFAULT false                            │
│ created_at      TIMESTAMP                                        │
│ updated_at      TIMESTAMP                                        │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                           tasks                                  │
├──────────────────────────────────────────────────────────────────┤
│ id              UUID PK                                          │
│ board_id        UUID FK → boards.id                              │
│ column_id       UUID FK → columns.id                             │
│ title           VARCHAR(500) NOT NULL                            │
│ description     TEXT                                             │
│ order           FLOAT NOT NULL                                   │
│ priority        INTEGER DEFAULT 0                                │
│ labels          JSONB DEFAULT '[]'                               │
│ version         INTEGER DEFAULT 1 (optimistic locking)           │
│ agent_status    VARCHAR(50)                                      │
│ current_execution_id UUID FK → agent_executions.id               │
│ agent_metadata  JSONB DEFAULT '{}'                               │
│ created_at      TIMESTAMP                                        │
│ updated_at      TIMESTAMP                                        │
└──────────────────────────────────────────────────────────────────┘
```

### Workflow Tables

```
┌──────────────────────────────────────────────────────────────────┐
│                    workflow_definitions                          │
├──────────────────────────────────────────────────────────────────┤
│ id              UUID PK                                          │
│ board_id        UUID FK → boards.id                              │
│ name            VARCHAR(255) NOT NULL                            │
│ description     TEXT                                             │
│ is_active       BOOLEAN DEFAULT false                            │
│ settings        JSONB DEFAULT '{}'                               │
│ created_at      TIMESTAMP                                        │
│ updated_at      TIMESTAMP                                        │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                    workflow_transitions                          │
├──────────────────────────────────────────────────────────────────┤
│ id              UUID PK                                          │
│ workflow_id     UUID FK → workflow_definitions.id                │
│ from_column_id  UUID FK → columns.id                             │
│ to_column_id    UUID FK → columns.id                             │
│ name            VARCHAR(255)                                     │
│ is_enabled      BOOLEAN DEFAULT true                             │
│ conditions      JSONB DEFAULT '{}'                               │
│ created_at      TIMESTAMP                                        │
│ updated_at      TIMESTAMP                                        │
└──────────────────────────────────────────────────────────────────┘
```

### Agent Tables

```
┌──────────────────────────────────────────────────────────────────┐
│                     agent_executions                             │
├──────────────────────────────────────────────────────────────────┤
│ id              UUID PK                                          │
│ task_id         UUID FK → tasks.id                               │
│ board_id        UUID FK → boards.id                              │
│ workflow_type   VARCHAR(50) NOT NULL                             │
│ status          VARCHAR(50) DEFAULT 'pending'                    │
│ current_phase   VARCHAR(50)                                      │
│ iteration       INTEGER DEFAULT 1                                │
│ max_iterations  INTEGER DEFAULT 3                                │
│ started_at      TIMESTAMP                                        │
│ completed_at    TIMESTAMP                                        │
│ error_message   TEXT                                             │
│ context         JSONB DEFAULT '{}'                               │
│ result_summary  JSONB                                            │
│ created_at      TIMESTAMP                                        │
│ updated_at      TIMESTAMP                                        │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                      agent_outputs                               │
├──────────────────────────────────────────────────────────────────┤
│ id              UUID PK                                          │
│ execution_id    UUID FK → agent_executions.id                    │
│ task_id         UUID FK → tasks.id                               │
│ agent_name      VARCHAR(100) NOT NULL                            │
│ phase           VARCHAR(50) NOT NULL                             │
│ iteration       INTEGER NOT NULL                                 │
│ status          VARCHAR(50) NOT NULL                             │
│ input_context   JSONB NOT NULL                                   │
│ output_content  TEXT                                             │
│ output_structured JSONB                                          │
│ files_created   JSONB DEFAULT '[]'                               │
│ tokens_used     INTEGER                                          │
│ duration_ms     INTEGER                                          │
│ error_message   TEXT                                             │
│ started_at      TIMESTAMP                                        │
│ completed_at    TIMESTAMP                                        │
│ created_at      TIMESTAMP                                        │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                      task_activities                             │
├──────────────────────────────────────────────────────────────────┤
│ id              UUID PK                                          │
│ task_id         UUID FK → tasks.id                               │
│ board_id        UUID FK → boards.id                              │
│ activity_type   VARCHAR(50) NOT NULL                             │
│ actor           VARCHAR(255) NOT NULL                            │
│ from_column_id  UUID FK → columns.id                             │
│ to_column_id    UUID FK → columns.id                             │
│ old_value       JSONB                                            │
│ new_value       JSONB                                            │
│ metadata        JSONB DEFAULT '{}'                               │
│ created_at      TIMESTAMP                                        │
└──────────────────────────────────────────────────────────────────┘
```

---

## Frontend Architecture

### State Management (Zustand)

```typescript
interface BoardState {
  // Core state
  boards: Board[];
  currentBoard: Board | null;
  columns: Column[];
  tasks: Task[];
  loading: boolean;
  error: string | null;

  // Workflow state
  activeWorkflow: WorkflowDefinition | null;
  allowedTransitions: AllowedTransitionsMap;
  workflowLoading: boolean;

  // Activity state
  activities: TaskActivity[];
  activitiesLoading: boolean;

  // Agent execution state
  executions: AgentExecution[];
  currentExecution: AgentExecution | null;
  executionLoading: boolean;
  executionMilestones: Record<string, string>;

  // Actions (CRUD, workflow, WebSocket handlers)
  // ...
}
```

### Component Hierarchy

```
App.tsx
└── Board.tsx
    ├── Column.tsx
    │   └── TaskCard.tsx
    │       └── AgentStatusBadge.tsx
    ├── ActivityFeed.tsx
    ├── AgentControlPanel.tsx
    │   ├── AgentExecutionPanel.tsx
    │   ├── AgentOutputViewer.tsx
    │   ├── StreamingOutput.tsx
    │   └── ExecutionDetails.tsx
    ├── CreateBoardDialog.tsx
    ├── CreateColumnDialog.tsx
    ├── CreateTaskDialog.tsx
    ├── BoardSettingsDialog.tsx (working directory config)
    ├── ColumnSettingsDialog.tsx (agent triggers)
    └── WorkflowEditor.tsx
```

### Key Frontend Types

```typescript
// Board with working directory
interface Board {
  id: string;
  name: string;
  description: string | null;
  working_directory?: string;  // For repository scanning
  created_at: string;
  updated_at: string;
}

// Column with agent triggers
interface Column {
  triggers_agents: boolean;
  agent_workflow_type?: string;
  is_start_column: boolean;
  is_end_column: boolean;
  // ...
}

// Task with agent status
interface Task {
  agent_status?: string;
  current_execution_id?: string;
  agent_metadata?: Record<string, unknown>;
  // ...
}

// Workflow types
type WorkflowType = 'development' | 'quick_development' | 'architecture_only';
```

---

## Implementation Roadmap

| Phase | Focus | Status |
|-------|-------|--------|
| **Phase 1** | Core Kanban Foundation | ✅ Complete |
| **Phase 2** | Workflow Engine | ✅ Complete |
| **Phase 3** | Agent Integration | ✅ Complete |
| **Phase 3.1** | Architecture Phase Improvements | ✅ Complete |
| **Phase 3.2** | Provider Abstraction Layer | ✅ Complete |
| **Phase 3.3** | Repository Awareness & Auto-Evaluation | ✅ Complete |
| **Phase 3.4** | Git Integration (auto-commit, branch detection) | ✅ Complete |
| **Phase 4** | Knowledge Base (RAG) | 🔲 Not Started |
| **Phase 5** | Polish & Optimization | 🔲 Not Started |

---

## Key Challenges & Solutions

### Challenge 1: Multi-Provider Support

**Problem:** Different AI backends (OAuth, API, Local) have different capabilities and interfaces.

**Solution:** Provider Abstraction Layer with common `BaseProvider` interface. Each provider implements `complete()` and `stream()` methods. `ProviderFactory` handles instantiation based on configuration.

### Challenge 2: Repository-Task Matching

**Problem:** Tasks need to know which repository they relate to for accurate development.

**Solution:** Two-stage repository awareness:
1. `RepositoryScannerService` discovers repositories under working directory
2. `TaskEvaluatorService` uses LLM to match tasks to repositories with confidence scores

### Challenge 3: Branch Management

**Problem:** Tasks may reference specific branches, or work should happen on the default branch.

**Solution:** Branch detection priority:
1. Explicit mention in task text
2. LLM-suggested branch
3. Default branch (main/master with most recent commit)

Auto-creation of branches when explicitly mentioned but not existing.

### Challenge 4: Agent Context Drift

**Problem:** Later agents may lose context from earlier phases.

**Solution:** Each phase output is saved to `~/.agent-rangers/`. `AgentContextBuilder` retrieves previous outputs and constructs context for subsequent phases.

### Challenge 5: Real-time UI Updates

**Problem:** Users need to see agent progress in real-time.

**Solution:** Multi-channel event system:
- Redis Pub/Sub for internal distribution
- WebSocket Manager for client broadcasts
- Execution milestones for progress indication

### Challenge 6: CLI Process Management

**Problem:** CLI-spawned agents run as subprocesses, harder to control.

**Solution:**
- Use Claude CLI with `--permission-mode acceptEdits`
- Parse `--output-format stream-json` for real-time events
- Implement timeout handling and graceful cancellation
- Track file changes for auto-commit

---

*Document Owner: Agent Rangers Team*
*Review Cycle: Each architecture change*
