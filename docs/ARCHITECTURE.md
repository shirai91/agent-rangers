# AI Multi-Agent Kanban Framework
## Technical Architecture v2.0 - Hybrid Approach

**Version:** 2.0
**Last Updated:** February 2026
**Author:** Tùng Phạm

---

## Executive Summary

This document outlines the architecture for building an AI-powered software development framework featuring a Trello-like Kanban dashboard with multiple specialized agents (Software Architect, Developer, Code Reviewer) that collaborate to complete development tasks.

**Key Architecture Decision:** We've adopted a **Hybrid Approach** combining:
- **Direct Anthropic API** for planning, analysis, and review phases
- **Claude Agent SDK (CLI spawning)** for autonomous code generation requiring file manipulation
- **Anthropic Text Editor Tool** for targeted code modifications

This approach provides the best balance of control, performance, and capability **without external framework dependencies**.

---

## Table of Contents
1. [High-Level System Architecture](#high-level-system-architecture)
2. [Technology Stack](#technology-stack)
3. [Hybrid Agent Orchestration](#hybrid-agent-orchestration)
4. [Agent Definitions & Workflows](#agent-definitions--workflows)
5. [Activity Logging & Real-Time Updates](#activity-logging--real-time-updates)
6. [Database Schema](#database-schema)
7. [Implementation Roadmap](#implementation-roadmap)
8. [Key Challenges & Solutions](#key-challenges--solutions)

---

## High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER                                │
│                  React 19 + Vite + shadcn/ui + @dnd-kit + Zustand          │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │                         Kanban Board UI                                │ │
│ │  ├── Drag-and-drop columns & cards                                     │ │
│ │  ├── Agent status indicators (per task)                                │ │
│ │  ├── Real-time activity log panel                                      │ │
│ │  └── Workflow definition editor                                        │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │ WebSocket + REST API
┌────────────────────────────────▼────────────────────────────────────────────┐
│                          ORCHESTRATION LAYER                                │
│                          FastAPI + Python 3.12+                             │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │                     Hybrid Agent Orchestrator                          │ │
│ │  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────────┐   │ │
│ │  │  Task Router    │ │    Workflow     │ │   Activity Logger       │   │ │
│ │  │  (FastAPI)      │ │    Engine       │ │   (Redis Pub/Sub)       │   │ │
│ │  └────────┬────────┘ └────────┬────────┘ └────────────┬────────────┘   │ │
│ │           │                   │                       │                │ │
│ │  ┌────────▼────────────────────▼────────────────────────▼────────────┐ │ │
│ │  │                    AGENT EXECUTION LAYER                          │ │ │
│ │  │                                                                   │ │ │
│ │  │  ┌─────────────────────────────────────────────────────────────┐ │ │ │
│ │  │  │              Direct Anthropic API                           │ │ │ │
│ │  │  │  • Architect Agent (planning, design docs)                  │ │ │ │
│ │  │  │  • Reviewer Agent (analysis, recommendations)               │ │ │ │
│ │  │  │  • Text Editor Tool (targeted file modifications)           │ │ │ │
│ │  │  └─────────────────────────────────────────────────────────────┘ │ │ │
│ │  │                                                                   │ │ │
│ │  │  ┌─────────────────────────────────────────────────────────────┐ │ │ │
│ │  │  │              Claude Agent SDK (CLI Spawning)                │ │ │ │
│ │  │  │  • Developer Agent (autonomous file creation/editing)       │ │ │ │
│ │  │  │  • Full filesystem access within workspace                  │ │ │ │
│ │  │  │  • Bash execution for testing/building                      │ │ │ │
│ │  │  └─────────────────────────────────────────────────────────────┘ │ │ │
│ │  └───────────────────────────────────────────────────────────────────┘ │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────────────┐
│                          INTELLIGENCE LAYER                                 │
│  ┌────────────────────────┐  ┌────────────────────────────────────────────┐ │
│  │ Shared Knowledge Base  │  │         Context Management                 │ │
│  │ (pgvector embeddings)  │  │         (Cross-agent memory)               │ │
│  └────────────────────────┘  └────────────────────────────────────────────┘ │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────────────┐
│                             DATA LAYER                                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────────────────┐ │
│  │  PostgreSQL 16   │  │     Redis 7      │  │   Workspace Filesystem     │ │
│  │  + pgvector      │  │   • Pub/Sub      │  │   /workspaces/{task_id}/   │ │
│  │  • Tasks, Boards │  │   • Cache        │  │   • Source files           │ │
│  │  • Workflows     │  │   • Sessions     │  │   • Build artifacts        │ │
│  │  • Knowledge     │  │   • Activity     │  │   • Agent outputs          │ │
│  │  • Activity Logs │  │     streams      │  │                            │ │
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
| **AI Integration** | anthropic + claude-agent-sdk | Native Claude API + CLI spawning |

### Infrastructure
| Component | Choice | Configuration |
|-----------|--------|---------------|
| **Database** | PostgreSQL 16 | With pgvector extension |
| **Cache/Pub-Sub** | Redis 7 | Real-time updates, activity streams |
| **Embeddings** | Ollama + nomic-embed-text | Self-hosted, 768 dimensions |
| **Containerization** | Docker Compose | Single-command deployment |

---

## Hybrid Agent Orchestration

### Why Hybrid?

| Approach | Pros | Cons | Best For |
|----------|------|------|----------|
| **Direct API** | Fast, low overhead, full control | Must implement file handlers | Planning, analysis, review |
| **CLI Spawning** | Built-in tools, autonomous execution | Process overhead, less control | Code generation, testing |
| **Text Editor Tool** | API-based file editing, sandboxed | You implement handlers | Targeted modifications |

### HybridOrchestrator Service

The core orchestration service (`backend/app/services/hybrid_orchestrator.py`) combines three execution modes:

1. **Direct Anthropic API** - Used for Architect and initial Review phases
2. **Claude Agent SDK** - Used for Developer phase (autonomous file operations)
3. **Text Editor Tool** - Used for applying critical fixes from review

```python
# backend/app/services/hybrid_orchestrator.py

from anthropic import Anthropic
from claude_agent_sdk import Agent

class HybridOrchestrator:
    """Hybrid agent orchestration without external frameworks."""

    def __init__(self):
        self.client = Anthropic()

    async def execute_workflow(self, task_id: str, description: str, workspace: str):
        """Execute full architect → developer → reviewer workflow."""

        # Phase 1: Architecture (Direct API)
        arch_result = await self._api_call(
            role="architect",
            system_prompt=ARCHITECT_PROMPT,
            prompt=f"Design architecture for: {description}"
        )
        await self._save_output(workspace, "ARCHITECTURE.md", arch_result)

        # Phase 2: Development (CLI Spawning)
        await self._cli_execute(
            task_id=task_id,
            workspace=workspace,
            prompt=f"Implement based on architecture:\n{arch_result}",
            role="developer"
        )

        # Phase 3: Review (Direct API + Text Editor)
        review_result = await self._api_call(
            role="reviewer",
            system_prompt=REVIEWER_PROMPT,
            prompt=f"Review the implementation in {workspace}"
        )
        await self._apply_review_fixes(task_id, workspace, review_result)

        return {"status": "complete", "workspace": workspace}
```

---

## Agent Definitions & Workflows

### Agent Types

| Agent | Execution Mode | Primary Tools | Use Case |
|-------|----------------|---------------|----------|
| **Software Architect** | Direct API | None (text output) | Planning, design documents |
| **Software Developer** | CLI Spawning | Read, Write, Edit, Bash | Code implementation |
| **Code Reviewer** | Direct API + Text Editor | Text Editor Tool | Code review, fixes |

### Workflow Sequence

```
Task Starts
    │
    ▼
┌─────────────────────────────────────┐
│  PHASE 1: Architecture              │
│  ────────────────────────────────   │
│  Mode: Direct Anthropic API         │
│  Agent: Software Architect          │
│  Output: ARCHITECTURE.md            │
│  Time: ~30 seconds                  │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  PHASE 2: Development               │
│  ────────────────────────────────   │
│  Mode: Claude Agent SDK (CLI)       │
│  Agent: Software Developer          │
│  Output: Source files, tests        │
│  Time: 2-10 minutes                 │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  PHASE 3: Review                    │
│  ────────────────────────────────   │
│  Mode: Direct API + Text Editor     │
│  Agent: Code Reviewer               │
│  Output: REVIEW.md + fixes          │
│  Time: ~1 minute                    │
└─────────────────────────────────────┘
    │
    ▼
Task Complete
```

---

## Activity Logging & Real-Time Updates

### Activity Types

| Type | Phase | Description |
|------|-------|-------------|
| `phase_start` | All | Agent begins working on phase |
| `phase_complete` | All | Agent finishes phase |
| `file_created` | Arch/Dev | New file created |
| `file_edit` | Review | File modified by text editor |
| `tool_call` | Dev | CLI agent uses a tool |
| `tool_result` | Dev | Tool execution result |
| `agent_message` | All | Agent thinking/progress |
| `workflow_complete` | Final | All phases done |

### Real-Time Streaming

Activities are streamed via:
1. **Redis Pub/Sub** - Internal event distribution
2. **WebSocket** - Frontend receives updates
3. **SSE (optional)** - Alternative streaming method

---

## Database Schema

### Core Tables (Phase 1-2)

- `boards` - Kanban boards
- `columns` - Workflow columns
- `tasks` - Task items
- `workflow_definitions` - State machine configs
- `workflow_transitions` - Allowed column transitions
- `task_activities` - Audit log

### Agent Tables (Phase 3)

- `agent_executions` - Execution records
- `agent_outputs` - Streaming output storage

### Knowledge Tables (Phase 4)

- `knowledge_chunks` - Vector embeddings

---

## Implementation Roadmap

| Phase | Focus | Status |
|-------|-------|--------|
| **Phase 1** | Core Kanban Foundation | ✅ Complete |
| **Phase 2** | Workflow Engine | ✅ Complete |
| **Phase 3** | Hybrid Agent Integration | ✅ Complete |
| **Phase 3.1** | Architecture Phase Improvements | ✅ Complete |
| **Phase 3+** | Repository Awareness & Auto-Evaluation | 🔄 In Progress (Backend ✅, Frontend 🔄) |
| **Phase 4** | Knowledge Base (RAG) | 🔲 Not Started |
| **Phase 5** | Polish & Optimization | 🔲 Not Started |

---

## Key Challenges & Solutions

### Challenge 1: Agent Context Drift

**Problem:** Later agents may lose context from earlier phases.

**Solution:** Each phase output is saved to workspace. Subsequent agents read previous outputs. Context is summarized when approaching token limits.

### Challenge 2: Real-time UI Updates

**Problem:** Users need to see agent progress in real-time.

**Solution:** Activity events emitted via Redis pub/sub, forwarded to frontend via WebSocket. Each activity includes timestamp and structured data.

### Challenge 3: CLI Process Management

**Problem:** CLI-spawned agents run as subprocesses, harder to control.

**Solution:** Use Claude Agent SDK with proper options:
- Set `permission_mode="acceptEdits"` for autonomous operation
- Parse message stream for activity logging
- Implement timeout handling

### Challenge 4: Workspace Isolation

**Problem:** Each task needs isolated filesystem for agent work.

**Solution:** Create `/workspaces/{task_id}/` directory per task. All file operations sandboxed to this path. Cleanup on task deletion.

---

*Document Owner: Agent Rangers Team*
*Review Cycle: Each architecture change*
