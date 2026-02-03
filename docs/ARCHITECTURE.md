# Building an AI Multi-Agent Kanban Framework on Claude-Flow

**The bottom line:** You can build a powerful multi-agent development system combining claude-flow's 60+ specialized agents with a custom Trello-like dashboard. The recommended stack is **FastAPI + React + PostgreSQL + Redis**, leveraging claude-flow's hierarchical swarm topology for agent coordination and pgvector for shared knowledge. This architecture enables software architect, developer, and reviewer agents to collaborate on tasks flowing through user-defined workflow columns.

---

## High-level system architecture

The system comprises four integrated layers that connect your Kanban interface to claude-flow's agent orchestration engine.

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                                  │
│  React + shadcn/ui + @dnd-kit + Zustand                                    │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Kanban Board UI (drag-and-drop columns, task cards, agent status)   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────┬────────────────────────────────────────┘
                                    │ WebSocket + REST API
┌───────────────────────────────────▼────────────────────────────────────────┐
│                         ORCHESTRATION LAYER                                 │
│  FastAPI + Claude-Flow Integration                                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────────────────┐  │
│  │  Task Router    │  │  Agent Manager  │  │  Workflow Engine (XState)  │  │
│  │  (REST + WS)    │  │  (claude-flow)  │  │  (State Machine)           │  │
│  └────────┬────────┘  └────────┬────────┘  └────────────┬───────────────┘  │
│           │                    │                        │                   │
│  ┌────────▼────────────────────▼────────────────────────▼───────────────┐  │
│  │                    CLAUDE-FLOW SWARM                                  │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────┐  │  │
│  │  │ Architect  │  │ Developer  │  │ Reviewer   │  │ Queen          │  │  │
│  │  │ Agent      │  │ Agent      │  │ Agent      │  │ Coordinator    │  │  │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────┬────────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────────┐
│                         INTELLIGENCE LAYER                                  │
│  ┌──────────────────────┐  ┌──────────────────────┐                        │
│  │  Shared Memory       │  │  RAG Engine          │                        │
│  │  (Memory Blocks)     │  │  (pgvector search)   │                        │
│  └──────────────────────┘  └──────────────────────┘                        │
└───────────────────────────────────┬────────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────────┐
│                         DATA LAYER                                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │  PostgreSQL      │  │  Redis           │  │  File System             │  │
│  │  (Tasks, Boards, │  │  (Pub/Sub,       │  │  (Code, Docs,            │  │
│  │   Workflows,     │  │   Cache,         │  │   Agent Definitions)     │  │
│  │   Knowledge)     │  │   Sessions)      │  │                          │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────┘
```

### Core data flows

**Task creation flow:** User creates task → Backend validates → Task stored in PostgreSQL → WebSocket broadcasts to UI → Claude-flow spawns appropriate agent → Agent processes task → Results flow back through Redis pub/sub → UI updates in real-time.

**Agent collaboration flow:** When a task moves to "In Progress," the workflow engine triggers claude-flow's hierarchical swarm. The **Queen Coordinator** delegates to specialized agents: Architect designs the approach, Developer implements code, and Reviewer validates quality. Agents communicate via claude-flow's Direct Agent-to-Agent (DAA) messaging, sharing context through memory blocks stored in pgvector.

---

## Detailed tech stack recommendations

### Frontend stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **UI Framework** | React 19 + Vite 6 | Fast HMR, modern React features, excellent TypeScript support |
| **Component Library** | shadcn/ui + Tailwind CSS v4 | Copy-paste components you own, 331+ templates available, Radix primitives for accessibility |
| **State Management** | Zustand | ~3KB, hook-based, perfect for Kanban boards, Redux DevTools compatible |
| **Drag-and-Drop** | @dnd-kit/core + @dnd-kit/sortable | Actively maintained (unlike react-beautiful-dnd), accessible, 60fps performance |
| **Forms** | react-hook-form + zod | Type-safe validation, minimal re-renders |
| **Real-time** | Native WebSocket + Zustand middleware | Direct connection to FastAPI WebSocket endpoints |

### Backend stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Framework** | FastAPI 0.115+ | Native async, automatic OpenAPI docs, Pydantic validation, seamless Anthropic SDK integration |
| **Runtime** | Python 3.12+ | Direct access to AI/ML ecosystem, best claude-flow compatibility |
| **ASGI Server** | Uvicorn 0.30+ | High-performance async server, WebSocket support |
| **ORM** | SQLAlchemy 2.0 + asyncpg | Async PostgreSQL access, mature migration tooling (Alembic) |
| **AI Integration** | anthropic SDK + claude-flow | Native Python support for both Claude API and orchestration framework |

### Database and infrastructure

| Component | Choice | Configuration |
|-----------|--------|---------------|
| **Primary Database** | PostgreSQL 16 | With pgvector extension for embeddings |
| **Cache/Pub-Sub** | Redis 7 | Real-time updates, session storage, agent message queue |
| **Containerization** | Docker Compose | Single-command local deployment |
| **Embedding Model** | nomic-embed-text via Ollama | Self-hosted, handles code and docs well (768 dimensions) |

---

## Claude-flow integration architecture

Claude-flow provides the multi-agent orchestration backbone. Here's how to integrate it with your custom dashboard:

### Agent specialization strategy

Define three primary agent types using claude-flow's YAML format stored in `.claude/agents/`:

```yaml
# .claude/agents/software-architect.yml
---
name: software-architect
type: architect
color: "#6366f1"
description: Designs system architecture and technical approaches
capabilities:
  - microservices-design
  - api-design
  - architecture-review
  - technical-specifications
priority: high
memory_access: read-write
coordination_priority: high
neural_patterns:
  - enterprise-architecture
  - clean-architecture
hooks:
  pre: |
    echo "Loading project context for architecture task"
---
```

```yaml
# .claude/agents/software-developer.yml
---
name: software-developer
type: coder
color: "#22c55e"
description: Implements code following architecture specifications
capabilities:
  - python
  - typescript
  - testing
  - documentation
priority: medium
memory_access: read-write
---
```

```yaml
# .claude/agents/code-reviewer.yml
---
name: code-reviewer
type: reviewer
color: "#f59e0b"
description: Reviews code for quality, security, and architecture compliance
capabilities:
  - security-audit
  - code-quality
  - performance-analysis
  - best-practices
priority: medium
memory_access: read-only
---
```

### Swarm initialization pattern

For software development workflows, use **hierarchical topology** with a Queen Coordinator to prevent agent drift and ensure consistent output:

```python
# backend/app/services/agent_orchestrator.py
import subprocess
import json
from typing import Optional

class AgentOrchestrator:
    def __init__(self):
        self.swarm_initialized = False
    
    async def initialize_swarm(self, max_agents: int = 8):
        """Initialize claude-flow swarm for task processing."""
        result = subprocess.run([
            "npx", "claude-flow@v3alpha", "swarm", "init",
            "--topology", "hierarchical",
            "--max-agents", str(max_agents),
            "--strategy", "specialized"
        ], capture_output=True, text=True)
        self.swarm_initialized = True
        return json.loads(result.stdout) if result.returncode == 0 else None
    
    async def spawn_agent(self, agent_type: str, task_id: str, task_description: str):
        """Spawn a specialized agent for a specific task."""
        result = subprocess.run([
            "npx", "claude-flow@v3alpha", "agent", "spawn",
            "-t", agent_type,
            "--name", f"{agent_type}-{task_id[:8]}",
            "--task", task_description,
            "--memory-access", "read-write",
            "--priority", "high"
        ], capture_output=True, text=True)
        return json.loads(result.stdout) if result.returncode == 0 else None
    
    async def execute_development_workflow(self, task: dict):
        """Execute full architect → developer → reviewer workflow."""
        # 1. Architecture phase
        architect = await self.spawn_agent(
            "software-architect", 
            task["id"],
            f"Design architecture for: {task['title']}\nContext: {task['description']}"
        )
        
        # 2. Development phase (receives architect output via shared memory)
        developer = await self.spawn_agent(
            "software-developer",
            task["id"],
            f"Implement based on architecture design for: {task['title']}"
        )
        
        # 3. Review phase
        reviewer = await self.spawn_agent(
            "code-reviewer",
            task["id"],
            f"Review implementation for: {task['title']}"
        )
        
        return {"architect": architect, "developer": developer, "reviewer": reviewer}
```

### Agent communication via shared memory

Claude-flow's memory system integrates with your PostgreSQL/pgvector setup. Configure shared memory blocks for cross-agent context:

```python
# backend/app/services/shared_memory.py
from sqlalchemy import text
from typing import List, Dict

class SharedMemoryService:
    def __init__(self, db_session):
        self.db = db_session
    
    async def store_context(self, task_id: str, context_type: str, content: str, embedding: List[float]):
        """Store context that all agents can access."""
        await self.db.execute(text("""
            INSERT INTO knowledge_chunks (
                content, embedding, source_type, task_id, component, created_at
            ) VALUES (
                :content, :embedding, :context_type, :task_id, 'shared', NOW()
            )
        """), {
            "content": content,
            "embedding": embedding,
            "context_type": context_type,
            "task_id": task_id
        })
    
    async def retrieve_context(self, query_embedding: List[float], task_id: str, limit: int = 5) -> List[Dict]:
        """Retrieve relevant context for agent consumption."""
        result = await self.db.execute(text("""
            SELECT content, source_type, 1 - (embedding <=> :query_embedding) as similarity
            FROM knowledge_chunks
            WHERE task_id = :task_id
            ORDER BY embedding <=> :query_embedding
            LIMIT :limit
        """), {
            "query_embedding": query_embedding,
            "task_id": task_id,
            "limit": limit
        })
        return [dict(row) for row in result.fetchall()]
```

---

## Database schema outline

### Core tables for Kanban and workflow

```sql
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Boards table
CREATE TABLE boards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Columns (user-defined workflow stages)
CREATE TABLE columns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    board_id UUID REFERENCES boards(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    "order" FLOAT NOT NULL,           -- Fractional ordering for drag-drop
    color VARCHAR(7),                 -- Hex color code
    wip_limit INTEGER,                -- Work-in-progress limit
    triggers_agents BOOLEAN DEFAULT FALSE,  -- Whether this column activates AI agents
    agent_workflow JSONB,             -- XState machine config for agent orchestration
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(board_id, name)
);

-- Tasks table
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    board_id UUID REFERENCES boards(id) ON DELETE CASCADE,
    column_id UUID REFERENCES columns(id) ON DELETE SET NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    "order" FLOAT NOT NULL,           -- Position within column
    priority INTEGER DEFAULT 0,       -- 0=none, 1=low, 2=medium, 3=high, 4=urgent
    labels JSONB DEFAULT '[]',
    agent_status JSONB DEFAULT '{}',  -- Current agent processing status
    version INTEGER DEFAULT 1,        -- Optimistic locking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Workflow definitions (XState machine configs stored as JSON)
CREATE TABLE workflow_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    board_id UUID REFERENCES boards(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    definition JSONB NOT NULL,        -- Full XState machine configuration
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Allowed transitions between columns
CREATE TABLE workflow_transitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    board_id UUID REFERENCES boards(id) ON DELETE CASCADE,
    from_column_id UUID REFERENCES columns(id) ON DELETE CASCADE,
    to_column_id UUID REFERENCES columns(id) ON DELETE CASCADE,
    event_name VARCHAR(100),          -- XState event that triggers this transition
    requires_approval BOOLEAN DEFAULT FALSE,
    UNIQUE(board_id, from_column_id, to_column_id)
);

-- Agent execution history
CREATE TABLE agent_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    agent_type VARCHAR(50) NOT NULL,  -- 'architect', 'developer', 'reviewer'
    agent_id VARCHAR(100),            -- claude-flow agent ID
    status VARCHAR(50) NOT NULL,      -- 'pending', 'running', 'completed', 'failed'
    input_context JSONB,
    output_result JSONB,
    tokens_used INTEGER,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Task activity log (audit trail)
CREATE TABLE task_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL,
    from_column_id UUID REFERENCES columns(id),
    to_column_id UUID REFERENCES columns(id),
    agent_id VARCHAR(100),
    changes JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Knowledge base schema (pgvector)

```sql
-- Shared knowledge chunks for RAG
CREATE TABLE knowledge_chunks (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(768),            -- nomic-embed-text dimensions
    source_type VARCHAR(50) NOT NULL, -- 'code', 'doc', 'decision', 'agent_output'
    source_path TEXT,
    task_id UUID REFERENCES tasks(id),
    component VARCHAR(100),
    tags TEXT[],
    version VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- HNSW index for fast similarity search
CREATE INDEX ON knowledge_chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON knowledge_chunks(source_type, task_id);
CREATE INDEX ON knowledge_chunks USING GIN(tags);
```

---

## Implementation phases and roadmap

### Phase 1: Foundation (Weeks 1-2)

**Goal:** Basic Kanban board with PostgreSQL persistence and real-time updates.

**Deliverables:**
- Docker Compose setup with PostgreSQL, Redis, FastAPI, React
- Database schema creation and migrations (Alembic)
- Basic CRUD API for boards, columns, tasks
- React Kanban UI with @dnd-kit drag-and-drop
- WebSocket connection for real-time task updates
- Zustand store for client-side state

**Key milestones:**
1. `docker compose up` brings up entire stack
2. Create board → add columns → create tasks → drag between columns
3. Changes persist to database and sync across browser tabs

### Phase 2: Workflow engine (Weeks 3-4)

**Goal:** User-definable workflows with XState state machines.

**Deliverables:**
- XState integration for workflow definition
- UI for creating/editing workflow columns and transitions
- Server-side transition validation
- Workflow definition storage in PostgreSQL (JSONB)
- Transition history logging

**Key milestones:**
1. User creates custom workflow (e.g., Backlog → Todo → In Progress → Review → Done)
2. Invalid transitions blocked (can't skip Review to Done)
3. Full audit trail of task movements

### Phase 3: Claude-flow integration (Weeks 5-7)

**Goal:** AI agents process tasks through the workflow.

**Deliverables:**
- Claude-flow installation and swarm initialization
- Custom agent definitions (architect, developer, reviewer)
- Task-to-agent triggering system
- Agent status display in task cards
- Agent execution history tracking

**Key milestones:**
1. Moving task to "In Progress" spawns architect agent
2. Agent output visible in real-time on task card
3. Sequential workflow: architect → developer → reviewer

### Phase 4: Knowledge sharing (Weeks 8-9)

**Goal:** Agents share context through vector-based knowledge base.

**Deliverables:**
- pgvector setup and embedding pipeline
- Ollama + nomic-embed-text for local embeddings
- RAG retrieval service for agent context
- Project file indexing (code, docs)
- Shared memory blocks between agents

**Key milestones:**
1. Index project codebase into pgvector
2. Agents retrieve relevant context before execution
3. Agent outputs stored as searchable knowledge

### Phase 5: Polish and optimization (Weeks 10-12)

**Goal:** Production-ready system with monitoring and refinements.

**Deliverables:**
- Agent performance monitoring dashboard
- Token usage tracking and cost estimates
- Error handling and retry logic
- Conflict resolution for concurrent updates
- UI/UX improvements based on usage

---

## Key challenges and solutions

### Challenge 1: Agent context drift in long workflows

**Problem:** When multiple agents collaborate, later agents may lose context from earlier phases, leading to inconsistent outputs.

**Solution:** Implement **hierarchical topology with Queen Coordinator** in claude-flow. The Queen maintains global task context and ensures each agent receives summarized context from previous phases:

```python
async def build_agent_context(task_id: str, current_phase: str) -> str:
    # Retrieve all previous phase outputs
    previous_outputs = await db.fetch_all("""
        SELECT agent_type, output_result 
        FROM agent_executions 
        WHERE task_id = $1 AND status = 'completed'
        ORDER BY completed_at
    """, task_id)
    
    # Summarize for context window efficiency
    context_summary = "\n".join([
        f"[{exec['agent_type']} output]: {summarize(exec['output_result'])}"
        for exec in previous_outputs
    ])
    
    return context_summary
```

### Challenge 2: Real-time sync with optimistic updates

**Problem:** User drags task, expects instant feedback, but server might reject the move or another tab might have conflicting state.

**Solution:** Version-based optimistic locking with automatic conflict resolution:

```typescript
// Frontend: Optimistic update pattern
const moveTask = async (taskId: string, toColumn: string) => {
  const task = store.getTask(taskId);
  const originalColumn = task.columnId;
  const originalVersion = task.version;
  
  // 1. Optimistically update UI immediately
  store.moveTask(taskId, toColumn);
  
  try {
    // 2. Persist with version check
    const result = await api.moveTask(taskId, toColumn, originalVersion);
    store.updateVersion(taskId, result.version);
  } catch (error) {
    if (error.code === 'VERSION_CONFLICT') {
      // 3. Rollback and apply server state
      store.applyServerState(error.serverState);
      toast.error('Task was modified elsewhere. Refreshed.');
    }
  }
};
```

### Challenge 3: Managing claude-flow agent lifecycle

**Problem:** Claude-flow agents are spawned externally; need to track their status and integrate with your database.

**Solution:** Wrapper service that manages agent lifecycle and syncs status via polling or MCP tools:

```python
class AgentLifecycleManager:
    async def spawn_and_track(self, task_id: str, agent_type: str):
        # Create execution record
        execution = await db.execute("""
            INSERT INTO agent_executions (task_id, agent_type, status)
            VALUES ($1, $2, 'pending') RETURNING id
        """, task_id, agent_type)
        
        # Spawn claude-flow agent
        agent = await self.orchestrator.spawn_agent(agent_type, task_id, task.description)
        
        # Update with agent ID
        await db.execute("""
            UPDATE agent_executions SET agent_id = $1, status = 'running', started_at = NOW()
            WHERE id = $2
        """, agent['agentId'], execution['id'])
        
        # Publish status update via Redis
        await redis.publish(f"board:{task.board_id}:updates", json.dumps({
            "type": "AGENT_STARTED",
            "payload": {"taskId": task_id, "agentType": agent_type}
        }))
        
        return execution['id']
```

### Challenge 4: Efficient knowledge retrieval at scale

**Problem:** As the knowledge base grows, RAG queries may slow down or return irrelevant results.

**Solution:** Implement tiered retrieval with metadata filtering and re-ranking:

```python
async def retrieve_context(query: str, task_id: str, limit: int = 10) -> List[Dict]:
    query_embedding = await embed(query)
    
    # Stage 1: Broad vector search with metadata filter
    candidates = await db.fetch_all("""
        SELECT id, content, source_type, 
               1 - (embedding <=> $1) as similarity
        FROM knowledge_chunks
        WHERE task_id = $2 OR source_type = 'project_docs'
        ORDER BY embedding <=> $1
        LIMIT $3
    """, query_embedding, task_id, limit * 3)  # Over-fetch for re-ranking
    
    # Stage 2: Re-rank by relevance to current task context
    task_context = await get_task_context(task_id)
    reranked = rerank_by_relevance(candidates, task_context, query)
    
    return reranked[:limit]
```

### Challenge 5: Single-user simplification opportunities

**Problem:** Full Redis pub/sub may be overkill for single-user self-hosted setup.

**Solution:** Use PostgreSQL LISTEN/NOTIFY as a lighter alternative that eliminates Redis dependency for real-time:

```sql
-- Trigger for task changes
CREATE OR REPLACE FUNCTION notify_task_change()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify('task_changes', json_build_object(
        'operation', TG_OP,
        'task_id', COALESCE(NEW.id, OLD.id),
        'board_id', COALESCE(NEW.board_id, OLD.board_id),
        'column_id', COALESCE(NEW.column_id, OLD.column_id)
    )::text);
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER task_notify_trigger
AFTER INSERT OR UPDATE OR DELETE ON tasks
FOR EACH ROW EXECUTE FUNCTION notify_task_change();
```

However, **keep Redis** for: agent message queuing, caching LLM responses, and session state—these use cases justify its inclusion even for single-user.

---

## Conclusion

This framework combines claude-flow's powerful agent orchestration with a custom Kanban interface to create a unique AI-assisted development workflow. The **hierarchical swarm topology** ensures your architect, developer, and reviewer agents collaborate coherently, while **pgvector-powered RAG** maintains project context across agent executions.

The key architectural decisions—FastAPI for its native Python AI ecosystem, @dnd-kit for maintainable drag-and-drop, XState for serializable workflows, and fractional ordering for efficient task positioning—create a solid foundation for iterative enhancement.

Start with Phase 1's basic Kanban board to validate the UI/UX, then progressively add workflow rules and agent integration. The modular architecture allows you to swap components (e.g., different embedding models, additional agent types) as requirements evolve. Most importantly, the self-hosted nature means you maintain full control over your data and can deeply customize agent behaviors for your specific development workflow.