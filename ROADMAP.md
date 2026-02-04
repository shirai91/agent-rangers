# Agent Rangers - Development Roadmap

## Project Overview
AI Multi-Agent Kanban Framework built on Claude-Flow. Enables software architect, developer, and reviewer agents to collaborate on tasks flowing through user-defined workflow columns.

**Repository:** `~/projects/personal/agent-rangers`  
**Stack:** FastAPI + React + PostgreSQL + Redis + Claude-Flow  
**Started:** 2026-02-03

---

## Phase 1: Foundation ✅ COMPLETE
**Timeline:** Weeks 1-2  
**Status:** Done (2026-02-03)  
**Estimated Hours:** 40h | **Actual:** ~2h (AI-assisted)

### 1.1 Infrastructure Setup ✅
- [x] Create project directory structure
- [x] Initialize git repository
- [x] Create `docker-compose.yml` with services:
  - [x] PostgreSQL 16 with health check
  - [x] Redis 7 with health check
  - [x] FastAPI backend with hot reload
  - [x] React frontend with Vite dev server
- [x] Configure volume mounts for persistence
- [x] Configure network for inter-service communication
- [x] Create `.env.example` files for both frontend and backend
- [x] Add `.gitignore` files

### 1.2 Backend - Database Layer ✅
- [x] Set up SQLAlchemy 2.0 async engine
- [x] Configure asyncpg for PostgreSQL connection
- [x] Create database session management
- [x] Set up Alembic for migrations
- [x] Create initial migration with tables:
  - [x] `boards` table (id, name, description, settings, timestamps)
  - [x] `columns` table (id, board_id, name, order, color, wip_limit, timestamps)
  - [x] `tasks` table (id, board_id, column_id, title, description, order, priority, labels, version, timestamps)
- [x] Add foreign key constraints and indexes
- [x] Implement UUID primary keys

### 1.3 Backend - Models & Schemas ✅
- [x] Create SQLAlchemy models:
  - [x] `Board` model with relationships
  - [x] `Column` model with board relationship
  - [x] `Task` model with board and column relationships
- [x] Create Pydantic schemas:
  - [x] `BoardCreate`, `BoardUpdate`, `BoardResponse`, `BoardListResponse`
  - [x] `ColumnCreate`, `ColumnUpdate`, `ColumnResponse`
  - [x] `TaskCreate`, `TaskUpdate`, `TaskMove`, `TaskResponse`
- [x] Add validation rules (string lengths, required fields)
- [x] Configure JSON serialization for JSONB fields

### 1.4 Backend - API Endpoints ✅
- [x] Create FastAPI application with lifespan management
- [x] Configure CORS middleware for frontend access
- [x] Implement health check endpoint (`GET /health`)
- [x] Implement Board endpoints:
  - [x] `GET /api/boards` - List all boards
  - [x] `POST /api/boards` - Create board
  - [x] `GET /api/boards/{id}` - Get board with columns
  - [x] `PUT /api/boards/{id}` - Update board
  - [x] `DELETE /api/boards/{id}` - Delete board
- [x] Implement Column endpoints:
  - [x] `GET /api/boards/{id}/columns` - List columns for board
  - [x] `POST /api/boards/{id}/columns` - Create column
  - [x] `PUT /api/columns/{id}` - Update column
  - [x] `DELETE /api/columns/{id}` - Delete column
- [x] Implement Task endpoints:
  - [x] `GET /api/boards/{id}/tasks` - List tasks for board
  - [x] `POST /api/boards/{id}/tasks` - Create task
  - [x] `GET /api/tasks/{id}` - Get task details
  - [x] `PUT /api/tasks/{id}` - Update task
  - [x] `PUT /api/tasks/{id}/move` - Move task with optimistic locking
  - [x] `DELETE /api/tasks/{id}` - Delete task
- [x] Add proper HTTP status codes (201 for create, 204 for delete)
- [x] Implement optimistic locking with version field

### 1.5 Backend - WebSocket ✅
- [x] Create WebSocket connection manager
- [x] Implement board-specific rooms (subscribe by board_id)
- [x] Broadcast task updates to connected clients
- [x] Handle connection/disconnection gracefully
- [x] Configure Redis pub/sub for multi-instance support

### 1.6 Backend - Services ✅
- [x] Create `BoardService` with CRUD operations
- [x] Implement fractional ordering for drag-drop
- [x] Add transaction management for complex operations
- [x] Implement error handling with proper HTTP exceptions

### 1.7 Frontend - Project Setup ✅
- [x] Initialize Vite + React + TypeScript project
- [x] Configure Tailwind CSS
- [x] Set up path aliases (`@/` for src)
- [x] Create shadcn/ui configuration
- [x] Install and configure dependencies:
  - [x] `@dnd-kit/core` and `@dnd-kit/sortable`
  - [x] `zustand` for state management
  - [x] `lucide-react` for icons
  - [x] `class-variance-authority` for component variants

### 1.8 Frontend - UI Components ✅
- [x] Create shadcn/ui base components:
  - [x] Button, Card, Dialog, Input, Label
  - [x] DropdownMenu, Badge, Skeleton
  - [x] Slot (for composition)
- [x] Create Kanban components:
  - [x] `Board` - Main kanban board with columns
  - [x] `Column` - Droppable column container
  - [x] `TaskCard` - Draggable task card
  - [x] `CreateBoardDialog` - Modal for creating boards
  - [x] `CreateColumnDialog` - Modal for creating columns
  - [x] `CreateTaskDialog` - Modal for creating tasks
- [x] Implement drag-and-drop with @dnd-kit:
  - [x] `DndContext` provider setup
  - [x] `SortableContext` for columns and tasks
  - [x] Drag overlay for visual feedback
  - [x] Drop animation

### 1.9 Frontend - State Management ✅
- [x] Create Zustand store (`boardStore`):
  - [x] Board list state
  - [x] Current board state with columns and tasks
  - [x] Loading and error states
  - [x] Actions: fetchBoards, fetchBoard, createBoard, deleteBoard
  - [x] Actions: createColumn, updateColumn, deleteColumn
  - [x] Actions: createTask, updateTask, moveTask, deleteTask
  - [x] Optimistic updates with rollback on failure
- [x] Implement selectors for derived state

### 1.10 Frontend - API Client ✅
- [x] Create typed API client with fetch
- [x] Implement request timeout (30s)
- [x] Add proper error handling:
  - [x] `ApiError` class for HTTP errors
  - [x] `NetworkError` class for network failures
- [x] URL parameter encoding for security
- [x] Handle empty responses (204 No Content)

### 1.11 Frontend - WebSocket Hook ✅
- [x] Create `useWebSocket` hook
- [x] Implement auto-reconnect with exponential backoff
- [x] Add connection state management
- [x] Handle incoming messages and update store
- [x] Cleanup on unmount

### 1.12 Frontend - Main App ✅
- [x] Create `App.tsx` with routing logic
- [x] Board list view (grid of board cards)
- [x] Board detail view (kanban columns)
- [x] Navigation between views
- [x] Loading states and error handling

### 1.13 Testing & Documentation ✅
- [x] Create `backend/test_api.py` with API tests
- [x] Create `backend/README.md` with setup instructions
- [x] Create `backend/QUICKSTART.md`
- [x] Create `frontend/README.md`
- [x] Create `docs/ARCHITECTURE.md`

---

## Phase 2: Workflow Engine ✅ COMPLETE
**Timeline:** Weeks 3-4  
**Status:** Done (2026-02-04)  
**Estimated Hours:** 60h | **Actual:** ~1h (AI-assisted)

### 2.1 Database Schema Updates
- [x] Create Alembic migration `002_workflow_engine.py`
- [x] Add `workflow_definitions` table:
  ```sql
  CREATE TABLE workflow_definitions (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      board_id UUID REFERENCES boards(id) ON DELETE CASCADE,
      name VARCHAR(255) NOT NULL,
      definition JSONB NOT NULL,  -- XState machine config
      is_active BOOLEAN DEFAULT TRUE,
      created_at TIMESTAMPTZ DEFAULT NOW(),
      updated_at TIMESTAMPTZ DEFAULT NOW()
  );
  ```
- [x] Add `workflow_transitions` table:
  ```sql
  CREATE TABLE workflow_transitions (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      board_id UUID REFERENCES boards(id) ON DELETE CASCADE,
      from_column_id UUID REFERENCES columns(id) ON DELETE CASCADE,
      to_column_id UUID REFERENCES columns(id) ON DELETE CASCADE,
      event_name VARCHAR(100),
      requires_approval BOOLEAN DEFAULT FALSE,
      auto_assign_agent BOOLEAN DEFAULT FALSE,
      agent_type VARCHAR(50),
      UNIQUE(board_id, from_column_id, to_column_id)
  );
  ```
- [x] Add `task_activities` table:
  ```sql
  CREATE TABLE task_activities (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
      action_type VARCHAR(50) NOT NULL,  -- created, updated, moved, deleted, agent_started, agent_completed
      actor_type VARCHAR(20) NOT NULL,   -- user, agent, system
      actor_id VARCHAR(100),
      from_column_id UUID REFERENCES columns(id),
      to_column_id UUID REFERENCES columns(id),
      changes JSONB,                      -- What changed
      metadata JSONB,                     -- Additional context
      created_at TIMESTAMPTZ DEFAULT NOW()
  );
  CREATE INDEX idx_task_activities_task_id ON task_activities(task_id);
  CREATE INDEX idx_task_activities_created_at ON task_activities(created_at DESC);
  ```
- [x] Add columns to `columns` table:
  ```sql
  ALTER TABLE columns ADD COLUMN triggers_agents BOOLEAN DEFAULT FALSE;
  ALTER TABLE columns ADD COLUMN agent_workflow JSONB;
  ALTER TABLE columns ADD COLUMN is_start_column BOOLEAN DEFAULT FALSE;
  ALTER TABLE columns ADD COLUMN is_end_column BOOLEAN DEFAULT FALSE;
  ```
- [x] Run migration and verify schema

### 2.2 Backend - Workflow Models
- [x] Create `WorkflowDefinition` SQLAlchemy model
  - [x] Define fields matching table schema
  - [x] Add relationship to Board
  - [x] Add JSON validation for definition field
- [x] Create `WorkflowTransition` SQLAlchemy model
  - [x] Define fields matching table schema
  - [x] Add relationships to Board, from_column, to_column
  - [x] Add unique constraint handling
- [x] Create `TaskActivity` SQLAlchemy model
  - [x] Define fields matching table schema
  - [x] Add relationship to Task
  - [x] Add enum for action_type and actor_type
- [x] Update `Column` model with new fields
- [x] Create Pydantic schemas:
  - [x] `WorkflowDefinitionCreate`, `WorkflowDefinitionUpdate`, `WorkflowDefinitionResponse`
  - [x] `WorkflowTransitionCreate`, `WorkflowTransitionUpdate`, `WorkflowTransitionResponse`
  - [x] `TaskActivityResponse`, `TaskActivityListResponse`

### 2.3 Backend - Workflow Service
- [x] Create `WorkflowService` class:
  - [x] `get_workflow(board_id)` - Get active workflow for board
  - [x] `create_workflow(board_id, definition)` - Create new workflow
  - [x] `update_workflow(workflow_id, definition)` - Update workflow
  - [x] `delete_workflow(workflow_id)` - Soft delete workflow
  - [x] `get_transitions(board_id)` - Get all allowed transitions
  - [x] `add_transition(board_id, from_col, to_col, config)` - Add transition rule
  - [x] `remove_transition(transition_id)` - Remove transition rule
  - [x] `validate_transition(task_id, from_col, to_col)` - Check if move is allowed
  - [x] `get_allowed_targets(column_id)` - Get columns task can move to

### 2.4 Backend - Activity Logging Service
- [x] Create `ActivityService` class:
  - [x] `log_activity(task_id, action, actor, changes)` - Record activity
  - [x] `get_task_activities(task_id, limit, offset)` - Get task history
  - [x] `get_board_activities(board_id, limit, offset)` - Get board history
  - [x] `get_recent_activities(board_id, since)` - Get activities since timestamp
- [x] Add activity logging to existing services:
  - [x] Log on task create
  - [x] Log on task update (with field diff)
  - [x] Log on task move (with from/to columns)
  - [x] Log on task delete

### 2.5 Backend - Workflow API Endpoints
- [x] Add Workflow Definition endpoints:
  - [x] `GET /api/boards/{id}/workflow` - Get board workflow
  - [x] `POST /api/boards/{id}/workflow` - Create/update workflow
  - [x] `DELETE /api/boards/{id}/workflow` - Delete workflow
- [x] Add Workflow Transition endpoints:
  - [x] `GET /api/boards/{id}/transitions` - List allowed transitions
  - [x] `POST /api/boards/{id}/transitions` - Add transition rule
  - [x] `DELETE /api/transitions/{id}` - Remove transition rule
  - [x] `GET /api/columns/{id}/allowed-targets` - Get valid move targets
- [x] Add Activity endpoints:
  - [x] `GET /api/tasks/{id}/activities` - Get task activity history
  - [x] `GET /api/boards/{id}/activities` - Get board activity feed
- [x] Update task move endpoint:
  - [x] Validate transition before move
  - [x] Return 403 if transition not allowed
  - [x] Include allowed_targets in error response

### 2.6 Backend - Transition Validation
- [x] Create `TransitionValidator` class:
  - [x] Check if transition exists in workflow_transitions
  - [x] Check if transition requires approval
  - [x] Check WIP limits on target column
  - [x] Return detailed validation result
- [x] Integrate validator into task move endpoint
- [x] Add bypass option for admin users (future)

### 2.7 Frontend - XState Integration
- [x] Install XState dependencies:
  ```bash
  npm install xstate @xstate/react
  ```
- [x] Create workflow machine factory:
  - [x] Generate XState machine from workflow definition
  - [x] Define states from columns
  - [x] Define transitions from workflow_transitions
  - [x] Add guards for validation
- [x] Create `useWorkflow` hook:
  - [x] Load workflow definition from API
  - [x] Create XState machine instance
  - [x] Expose current state and allowed transitions
  - [x] Handle transition events

### 2.8 Frontend - Workflow Types
- [x] Add TypeScript types:
  ```typescript
  interface WorkflowDefinition {
    id: string;
    boardId: string;
    name: string;
    definition: XStateMachineConfig;
    isActive: boolean;
    createdAt: string;
    updatedAt: string;
  }

  interface WorkflowTransition {
    id: string;
    boardId: string;
    fromColumnId: string;
    toColumnId: string;
    eventName?: string;
    requiresApproval: boolean;
    autoAssignAgent: boolean;
    agentType?: string;
  }

  interface TaskActivity {
    id: string;
    taskId: string;
    actionType: 'created' | 'updated' | 'moved' | 'deleted' | 'agent_started' | 'agent_completed';
    actorType: 'user' | 'agent' | 'system';
    actorId?: string;
    fromColumnId?: string;
    toColumnId?: string;
    changes?: Record<string, any>;
    metadata?: Record<string, any>;
    createdAt: string;
  }
  ```

### 2.9 Frontend - API Client Updates
- [x] Add workflow API methods:
  - [x] `getWorkflow(boardId)` - Fetch workflow definition
  - [x] `saveWorkflow(boardId, definition)` - Create/update workflow
  - [x] `deleteWorkflow(boardId)` - Delete workflow
  - [x] `getTransitions(boardId)` - Fetch transition rules
  - [x] `addTransition(boardId, transition)` - Add transition
  - [x] `removeTransition(transitionId)` - Remove transition
  - [x] `getAllowedTargets(columnId)` - Get valid move targets
  - [x] `getTaskActivities(taskId)` - Fetch task history
  - [x] `getBoardActivities(boardId)` - Fetch board feed

### 2.10 Frontend - Store Updates
- [x] Add workflow state to store:
  ```typescript
  interface BoardStore {
    // ... existing state
    workflow: WorkflowDefinition | null;
    transitions: WorkflowTransition[];
    allowedTargets: Record<string, string[]>; // columnId -> allowed target columnIds

    // Actions
    fetchWorkflow: (boardId: string) => Promise<void>;
    saveWorkflow: (boardId: string, definition: any) => Promise<void>;
    fetchTransitions: (boardId: string) => Promise<void>;
    addTransition: (transition: CreateTransitionInput) => Promise<void>;
    removeTransition: (transitionId: string) => Promise<void>;
  }
  ```
- [x] Update `moveTask` to check allowed targets
- [x] Add optimistic UI for valid/invalid drop zones

### 2.11 Frontend - Workflow Editor UI
- [x] Create `WorkflowEditor` component:
  - [x] Visual column arrangement
  - [x] Drag to create transitions (arrows between columns)
  - [x] Click to edit transition properties
  - [x] Toggle agent triggers per column
- [x] Create `TransitionArrow` component:
  - [x] SVG arrow between columns
  - [x] Highlight on hover
  - [x] Click to edit/delete
- [x] Create `TransitionEditor` dialog:
  - [x] From/To column display
  - [x] Requires approval toggle
  - [x] Auto-assign agent toggle
  - [x] Agent type selector
- [x] Create `ColumnSettings` dialog:
  - [x] Column name edit
  - [x] Color picker
  - [x] WIP limit setting
  - [x] Triggers agents toggle
  - [x] Start/End column flags

### 2.12 Frontend - Drop Zone Validation
- [x] Update `Board` component:
  - [x] Fetch allowed targets on load
  - [x] Pass allowed targets to columns
- [x] Update `Column` component:
  - [x] Check if drop is allowed
  - [x] Visual feedback for valid/invalid drop
  - [x] Green highlight for allowed
  - [x] Red highlight / disabled for not allowed
- [x] Update drag overlay:
  - [x] Show "not allowed" indicator when over invalid column

### 2.13 Frontend - Activity Feed
- [x] Create `ActivityFeed` component:
  - [x] List of activity items
  - [x] Infinite scroll / pagination
  - [x] Filter by action type
  - [x] Filter by date range
- [x] Create `ActivityItem` component:
  - [x] Icon based on action type
  - [x] Human-readable description
  - [x] Timestamp (relative)
  - [x] Actor info (user/agent)
  - [x] Expandable details
- [x] Create `TaskActivityPanel` component:
  - [x] Show in task detail view
  - [x] Compact activity list
  - [x] "View all" link to full feed

### 2.14 Frontend - Board Settings Page
- [x] Create `BoardSettings` page/modal:
  - [x] Board name and description edit
  - [x] Workflow editor tab
  - [x] Danger zone (delete board)
- [x] Add settings button to board header
- [x] Add route for board settings

### 2.15 Testing & Documentation
- [x] Write unit tests for WorkflowService
- [x] Write unit tests for TransitionValidator
- [x] Write integration tests for workflow API
- [x] Write E2E tests for workflow editor
- [x] Update API documentation
- [x] Update README with workflow features
- [x] Create workflow user guide

---

## Phase 3: Claude-Flow Integration ✅ COMPLETE
**Timeline:** Weeks 5-7
**Status:** Done (2026-02-04)
**Estimated Hours:** 80h

### 3.1 Claude-Flow Setup
- [x] Install claude-flow globally:
  ```bash
  npm install -g claude-flow@v3alpha
  ```
- [x] Verify installation: `claude-flow --version`
- [x] Create `.claude/` directory in project root
- [x] Initialize claude-flow config:
  ```bash
  claude-flow init
  ```
- [x] Test basic swarm initialization:
  ```bash
  claude-flow swarm init --topology hierarchical
  ```

### 3.2 Agent Definition Files
- [x] Create `.claude/agents/` directory
- [x] Create `software-architect.yml`:
  ```yaml
  name: software-architect
  type: architect
  color: "#6366f1"
  description: Designs system architecture and technical approaches
  capabilities:
    - microservices-design
    - api-design
    - architecture-review
    - technical-specifications
    - database-schema-design
    - system-integration
  priority: high
  memory_access: read-write
  coordination_priority: high
  context_window: 100000
  neural_patterns:
    - enterprise-architecture
    - clean-architecture
    - domain-driven-design
  hooks:
    pre: |
      echo "Loading project context for architecture task"
    post: |
      echo "Architecture phase complete"
  output_format: markdown
  ```
- [x] Create `software-developer.yml`:
  ```yaml
  name: software-developer
  type: coder
  color: "#22c55e"
  description: Implements code following architecture specifications
  capabilities:
    - python
    - typescript
    - react
    - fastapi
    - testing
    - documentation
    - refactoring
    - debugging
  priority: medium
  memory_access: read-write
  context_window: 100000
  tools:
    - file_read
    - file_write
    - shell_exec
    - git
  output_format: code
  ```
- [x] Create `code-reviewer.yml`:
  ```yaml
  name: code-reviewer
  type: reviewer
  color: "#f59e0b"
  description: Reviews code for quality, security, and architecture compliance
  capabilities:
    - security-audit
    - code-quality
    - performance-analysis
    - best-practices
    - test-coverage
    - documentation-review
  priority: medium
  memory_access: read-only
  context_window: 100000
  checklist:
    - security_vulnerabilities
    - code_style
    - error_handling
    - test_coverage
    - documentation
    - performance
  output_format: structured_review
  ```
- [x] Create `queen-coordinator.yml`:
  ```yaml
  name: queen-coordinator
  type: coordinator
  color: "#ec4899"
  description: Coordinates multi-agent workflows and maintains context
  capabilities:
    - task-delegation
    - context-management
    - conflict-resolution
    - progress-tracking
  priority: critical
  memory_access: read-write
  coordination_priority: highest
  ```

### 3.3 Database Schema Updates
- [x] Create Alembic migration `003_agent_execution.py`
- [x] Add `agent_executions` table:
  ```sql
  CREATE TABLE agent_executions (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
      agent_type VARCHAR(50) NOT NULL,
      agent_name VARCHAR(100),
      agent_id VARCHAR(100),  -- claude-flow agent ID
      status VARCHAR(50) NOT NULL DEFAULT 'pending',
      phase VARCHAR(50),  -- architecture, development, review
      input_context JSONB,
      output_result JSONB,
      error_message TEXT,
      tokens_used INTEGER,
      cost_estimate DECIMAL(10, 4),
      started_at TIMESTAMPTZ,
      completed_at TIMESTAMPTZ,
      created_at TIMESTAMPTZ DEFAULT NOW(),
      updated_at TIMESTAMPTZ DEFAULT NOW()
  );
  CREATE INDEX idx_agent_executions_task_id ON agent_executions(task_id);
  CREATE INDEX idx_agent_executions_status ON agent_executions(status);
  ```
- [x] Add `agent_outputs` table for streaming results:
  ```sql
  CREATE TABLE agent_outputs (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      execution_id UUID REFERENCES agent_executions(id) ON DELETE CASCADE,
      output_type VARCHAR(50) NOT NULL,  -- thought, code, file, message
      content TEXT NOT NULL,
      metadata JSONB,
      sequence_num INTEGER NOT NULL,
      created_at TIMESTAMPTZ DEFAULT NOW()
  );
  CREATE INDEX idx_agent_outputs_execution_id ON agent_outputs(execution_id);
  ```
- [x] Update `tasks` table:
  ```sql
  ALTER TABLE tasks ADD COLUMN agent_status JSONB DEFAULT '{}';
  ALTER TABLE tasks ADD COLUMN current_agent_execution_id UUID REFERENCES agent_executions(id);
  ```
- [x] Run migration

### 3.4 Backend - Agent Models
- [x] Create `AgentExecution` SQLAlchemy model
- [x] Create `AgentOutput` SQLAlchemy model
- [x] Update `Task` model with agent fields
- [x] Create Pydantic schemas:
  - [x] `AgentExecutionCreate`, `AgentExecutionUpdate`, `AgentExecutionResponse`
  - [x] `AgentOutputResponse`
  - [x] `AgentStatusResponse`

### 3.5 Backend - Agent Orchestrator Service
- [x] Create `AgentOrchestrator` class:
  ```python
  class AgentOrchestrator:
      async def initialize_swarm(self, max_agents: int = 8):
          """Initialize claude-flow swarm"""

      async def spawn_agent(self, agent_type: str, task_id: str, context: dict):
          """Spawn a specialized agent for a task"""

      async def execute_workflow(self, task: Task, workflow_type: str):
          """Execute full agent workflow (architect -> dev -> review)"""

      async def get_agent_status(self, execution_id: str):
          """Get current status of agent execution"""

      async def cancel_execution(self, execution_id: str):
          """Cancel running agent execution"""

      async def stream_output(self, execution_id: str):
          """Stream agent output in real-time"""
  ```
- [x] Implement subprocess management for claude-flow CLI
- [x] Implement output parsing and storage
- [x] Implement error handling and retry logic
- [x] Add timeout management

### 3.6 Backend - Agent Workflow Service
- [x] Create `AgentWorkflowService` class:
  ```python
  class AgentWorkflowService:
      async def start_architecture_phase(self, task: Task):
          """Start architect agent for task"""

      async def start_development_phase(self, task: Task, arch_output: dict):
          """Start developer agent with architect context"""

      async def start_review_phase(self, task: Task, dev_output: dict):
          """Start reviewer agent for code review"""

      async def handle_review_feedback(self, task: Task, feedback: dict):
          """Handle review feedback - may restart dev phase"""

      async def complete_workflow(self, task: Task):
          """Mark workflow as complete, update task"""
  ```
- [x] Implement phase transitions
- [x] Implement context passing between agents
- [x] Add webhook/callback support for async completion

### 3.7 Backend - Agent Context Builder
- [x] Create `AgentContextBuilder` class:
  ```python
  class AgentContextBuilder:
      async def build_context(self, task: Task, phase: str) -> dict:
          """Build context for agent based on phase"""

      async def get_previous_outputs(self, task_id: str) -> list:
          """Get outputs from previous phases"""

      async def get_project_context(self, task: Task) -> dict:
          """Get relevant project files and docs"""

      async def summarize_context(self, context: dict, max_tokens: int) -> dict:
          """Summarize context to fit token limit"""
  ```
- [x] Implement context retrieval from previous phases
- [x] Implement project file scanning
- [x] Implement context summarization

### 3.8 Backend - Agent API Endpoints
- [x] Add Agent Execution endpoints:
  - [x] `POST /api/tasks/{id}/agents/start` - Start agent workflow
  - [x] `GET /api/tasks/{id}/agents/status` - Get current agent status
  - [x] `POST /api/tasks/{id}/agents/cancel` - Cancel agent execution
  - [x] `GET /api/tasks/{id}/agents/executions` - List all executions
  - [x] `GET /api/agent-executions/{id}` - Get execution details
  - [x] `GET /api/agent-executions/{id}/outputs` - Get execution outputs
  - [x] `GET /api/agent-executions/{id}/stream` - SSE stream for real-time output
- [x] Add Agent Management endpoints:
  - [x] `GET /api/agents` - List available agent types
  - [x] `GET /api/agents/{type}` - Get agent configuration
  - [x] `POST /api/swarm/initialize` - Initialize agent swarm
  - [x] `GET /api/swarm/status` - Get swarm status

### 3.9 Backend - Agent Trigger Integration
- [x] Update task move endpoint:
  - [x] Check if target column has `triggers_agents=true`
  - [x] If yes, automatically start agent workflow
  - [x] Update task status to "agent_processing"
- [x] Create background task for agent execution
- [x] Implement webhook for agent completion
- [x] Update WebSocket to broadcast agent status changes

### 3.10 Frontend - Agent Types
- [x] Add TypeScript types:
  ```typescript
  interface AgentExecution {
    id: string;
    taskId: string;
    agentType: string;
    agentName: string;
    agentId?: string;
    status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
    phase: 'architecture' | 'development' | 'review';
    inputContext?: Record<string, any>;
    outputResult?: Record<string, any>;
    errorMessage?: string;
    tokensUsed?: number;
    costEstimate?: number;
    startedAt?: string;
    completedAt?: string;
    createdAt: string;
  }

  interface AgentOutput {
    id: string;
    executionId: string;
    outputType: 'thought' | 'code' | 'file' | 'message';
    content: string;
    metadata?: Record<string, any>;
    sequenceNum: number;
    createdAt: string;
  }

  interface AgentStatus {
    isRunning: boolean;
    currentPhase?: string;
    currentAgent?: string;
    progress?: number;
    lastOutput?: string;
  }
  ```

### 3.11 Frontend - API Client Updates
- [x] Add agent API methods:
  - [x] `startAgentWorkflow(taskId)` - Start agents for task
  - [x] `getAgentStatus(taskId)` - Get current status
  - [x] `cancelAgentExecution(taskId)` - Cancel execution
  - [x] `getAgentExecutions(taskId)` - List executions
  - [x] `getExecutionDetails(executionId)` - Get details
  - [x] `getExecutionOutputs(executionId)` - Get outputs
  - [x] `streamExecutionOutput(executionId)` - SSE stream

### 3.12 Frontend - Store Updates
- [x] Add agent state to store:
  ```typescript
  interface BoardStore {
    // ... existing state
    agentExecutions: Record<string, AgentExecution[]>; // taskId -> executions
    agentStatus: Record<string, AgentStatus>; // taskId -> status

    // Actions
    startAgentWorkflow: (taskId: string) => Promise<void>;
    cancelAgentExecution: (taskId: string) => Promise<void>;
    fetchAgentStatus: (taskId: string) => Promise<void>;
    updateAgentStatus: (taskId: string, status: AgentStatus) => void;
  }
  ```
- [x] Handle WebSocket updates for agent status
- [x] Implement polling fallback for status

### 3.13 Frontend - Agent Status Components
- [x] Create `AgentStatusBadge` component:
  - [x] Shows current agent phase
  - [x] Color coded by status
  - [x] Animated when running
- [x] Create `AgentStatusIndicator` component:
  - [x] Circular progress indicator
  - [x] Phase labels
  - [x] Time elapsed
- [x] Update `TaskCard` component:
  - [x] Show agent status badge
  - [x] Click to expand details

### 3.14 Frontend - Agent Execution Panel
- [x] Create `AgentExecutionPanel` component:
  - [x] Shows in task detail view
  - [x] List of all executions
  - [x] Current execution highlighted
- [x] Create `ExecutionDetails` component:
  - [x] Agent info (type, name)
  - [x] Status and timing
  - [x] Token usage and cost
  - [x] Output viewer
- [x] Create `AgentOutputViewer` component:
  - [x] Streaming output display
  - [x] Syntax highlighting for code
  - [x] Collapsible sections
  - [x] Copy to clipboard

### 3.15 Frontend - Agent Control UI
- [x] Create `AgentControlPanel` component:
  - [x] Start/Stop buttons
  - [x] Phase selector (manual override)
  - [x] Agent type selector
- [x] Add agent trigger button to task cards
- [x] Add agent status to column header (count of running)

### 3.16 Frontend - Real-time Updates
- [x] Implement SSE client for output streaming
- [x] Update WebSocket handler for agent events
- [x] Add notification for agent completion
- [x] Add error toast for agent failures

### 3.17 Testing & Documentation
- [x] Write unit tests for AgentOrchestrator
- [x] Write unit tests for AgentWorkflowService
- [x] Write integration tests for agent API
- [x] Write E2E tests for agent workflow
- [x] Create agent configuration guide
- [x] Create agent workflow documentation
- [x] Update README with agent features

---

## Phase 4: Knowledge Sharing (RAG) 🔲 NOT STARTED
**Timeline:** Weeks 8-9  
**Status:** Pending (requires Phase 3)  
**Estimated Hours:** 60h

### 4.1 pgvector Setup
- [ ] Add pgvector extension to PostgreSQL
- [ ] Create Alembic migration `004_knowledge_base.py`
- [ ] Add `knowledge_chunks` table:
  ```sql
  CREATE EXTENSION IF NOT EXISTS vector;
  
  CREATE TABLE knowledge_chunks (
      id SERIAL PRIMARY KEY,
      content TEXT NOT NULL,
      embedding vector(768),
      source_type VARCHAR(50) NOT NULL,
      source_path TEXT,
      task_id UUID REFERENCES tasks(id),
      board_id UUID REFERENCES boards(id),
      component VARCHAR(100),
      tags TEXT[],
      file_hash VARCHAR(64),
      version VARCHAR(50),
      chunk_index INTEGER,
      total_chunks INTEGER,
      created_at TIMESTAMPTZ DEFAULT NOW(),
      updated_at TIMESTAMPTZ DEFAULT NOW()
  );
  
  CREATE INDEX idx_knowledge_embedding ON knowledge_chunks 
    USING hnsw (embedding vector_cosine_ops);
  CREATE INDEX idx_knowledge_source ON knowledge_chunks(source_type, board_id);
  CREATE INDEX idx_knowledge_tags ON knowledge_chunks USING GIN(tags);
  ```
- [ ] Run migration and verify pgvector works

### 4.2 Embedding Service Setup
- [ ] Install Ollama locally
- [ ] Pull nomic-embed-text model:
  ```bash
  ollama pull nomic-embed-text
  ```
- [ ] Create `EmbeddingService` class:
  ```python
  class EmbeddingService:
      async def embed_text(self, text: str) -> List[float]:
          """Generate embedding for text"""
          
      async def embed_batch(self, texts: List[str]) -> List[List[float]]:
          """Generate embeddings for multiple texts"""
          
      async def get_model_info(self) -> dict:
          """Get embedding model information"""
  ```
- [ ] Test embedding generation

### 4.3 Document Chunking Service
- [ ] Create `ChunkingService` class:
  ```python
  class ChunkingService:
      async def chunk_text(self, text: str, max_tokens: int = 500) -> List[str]:
          """Split text into chunks"""
          
      async def chunk_code(self, code: str, language: str) -> List[str]:
          """Split code by functions/classes"""
          
      async def chunk_markdown(self, markdown: str) -> List[str]:
          """Split markdown by sections"""
  ```
- [ ] Implement semantic chunking (by paragraph/section)
- [ ] Implement code-aware chunking (by function/class)
- [ ] Add overlap between chunks

### 4.4 Knowledge Indexing Service
- [ ] Create `KnowledgeIndexer` class:
  ```python
  class KnowledgeIndexer:
      async def index_file(self, file_path: str, board_id: str):
          """Index a single file"""
          
      async def index_directory(self, dir_path: str, board_id: str):
          """Recursively index directory"""
          
      async def index_agent_output(self, execution_id: str):
          """Index agent output for future retrieval"""
          
      async def reindex_board(self, board_id: str):
          """Reindex all content for a board"""
          
      async def delete_stale(self, board_id: str):
          """Remove outdated chunks"""
  ```
- [ ] Implement file change detection (hash comparison)
- [ ] Add file type handlers (code, markdown, text)
- [ ] Implement incremental indexing

### 4.5 RAG Retrieval Service
- [ ] Create `RAGService` class:
  ```python
  class RAGService:
      async def search(self, query: str, board_id: str, limit: int = 10) -> List[dict]:
          """Search for relevant chunks"""
          
      async def search_with_filters(
          self, 
          query: str, 
          board_id: str,
          source_types: List[str] = None,
          tags: List[str] = None,
          limit: int = 10
      ) -> List[dict]:
          """Search with metadata filters"""
          
      async def get_context_for_task(self, task: Task, max_tokens: int) -> str:
          """Build context string for agent"""
          
      async def rerank_results(self, query: str, results: List[dict]) -> List[dict]:
          """Re-rank results by relevance"""
  ```
- [ ] Implement vector similarity search
- [ ] Implement hybrid search (vector + keyword)
- [ ] Implement re-ranking

### 4.6 Backend - Knowledge API
- [ ] Add Knowledge endpoints:
  - [ ] `POST /api/boards/{id}/knowledge/index` - Trigger indexing
  - [ ] `GET /api/boards/{id}/knowledge/status` - Get indexing status
  - [ ] `POST /api/boards/{id}/knowledge/search` - Search knowledge base
  - [ ] `DELETE /api/boards/{id}/knowledge` - Clear knowledge base
  - [ ] `GET /api/knowledge/chunks/{id}` - Get chunk details

### 4.7 Agent Context Integration
- [ ] Update `AgentContextBuilder`:
  - [ ] Query RAG for relevant context
  - [ ] Include code snippets in agent prompt
  - [ ] Include documentation in agent prompt
  - [ ] Limit context to token budget
- [ ] Auto-index agent outputs after completion
- [ ] Tag agent outputs for easy retrieval

### 4.8 Frontend - Knowledge UI
- [ ] Create `KnowledgePanel` component:
  - [ ] Show indexed files count
  - [ ] Show last index time
  - [ ] Trigger re-index button
- [ ] Create `KnowledgeSearch` component:
  - [ ] Search input
  - [ ] Results list with snippets
  - [ ] Click to view full content
- [ ] Add knowledge status to board settings

### 4.9 Testing & Documentation
- [ ] Write tests for EmbeddingService
- [ ] Write tests for RAGService
- [ ] Test with sample codebase
- [ ] Document knowledge base setup
- [ ] Document indexing process

---

## Phase 5: Polish & Optimization 🔲 NOT STARTED
**Timeline:** Weeks 10-12  
**Status:** Pending (requires Phase 4)  
**Estimated Hours:** 50h

### 5.1 Performance Monitoring Dashboard
- [ ] Create `MetricsDashboard` page:
  - [ ] Agent execution times (avg, p50, p95)
  - [ ] Token usage per agent type
  - [ ] Cost tracking (daily, weekly, monthly)
  - [ ] Success/failure rates
  - [ ] Active tasks and agents
- [ ] Add charts and visualizations
- [ ] Add date range filtering

### 5.2 Cost Tracking
- [ ] Implement token counting:
  - [ ] Count input tokens
  - [ ] Count output tokens
  - [ ] Track by agent type
- [ ] Implement cost calculation:
  - [ ] Define cost per token by model
  - [ ] Calculate per-execution cost
  - [ ] Aggregate by task/board/time
- [ ] Add cost estimates before execution
- [ ] Add spending alerts/limits

### 5.3 Error Handling & Retry
- [ ] Implement retry logic for agent failures:
  - [ ] Configurable retry count
  - [ ] Exponential backoff
  - [ ] Different strategies per error type
- [ ] Add circuit breaker for repeated failures
- [ ] Improve error messages for users
- [ ] Add error recovery suggestions

### 5.4 Concurrent Update Handling
- [ ] Implement proper optimistic locking UI:
  - [ ] Detect version conflicts
  - [ ] Show conflict resolution dialog
  - [ ] Allow merge or override
- [ ] Add real-time collaboration indicators:
  - [ ] Show who's viewing task
  - [ ] Show who's editing
  - [ ] Cursor presence (like Figma)

### 5.5 UI/UX Improvements
- [ ] Add keyboard shortcuts:
  - [ ] `N` - New task
  - [ ] `E` - Edit selected
  - [ ] `D` - Delete selected
  - [ ] Arrow keys - Navigate
  - [ ] `?` - Show shortcuts
- [ ] Add task quick actions menu
- [ ] Add bulk operations (multi-select)
- [ ] Improve mobile responsiveness
- [ ] Add dark mode support
- [ ] Add loading skeletons everywhere

### 5.6 Search & Filtering
- [ ] Add global search:
  - [ ] Search tasks by title/description
  - [ ] Search across boards
  - [ ] Keyboard shortcut (`/`)
- [ ] Add advanced filters:
  - [ ] By status
  - [ ] By priority
  - [ ] By assignee
  - [ ] By date range
  - [ ] By labels
- [ ] Save filter presets

### 5.7 Notifications
- [ ] Implement notification system:
  - [ ] In-app notifications
  - [ ] Browser notifications (optional)
  - [ ] Notification preferences
- [ ] Notify on:
  - [ ] Agent completion
  - [ ] Agent failure
  - [ ] Task assigned to you
  - [ ] Mentions in comments

### 5.8 Export & Import
- [ ] Export board data:
  - [ ] JSON format
  - [ ] CSV format
  - [ ] Markdown format
- [ ] Import board data:
  - [ ] From JSON
  - [ ] From Trello
  - [ ] From Jira (basic)

### 5.9 Final Testing
- [ ] Full E2E test suite
- [ ] Performance testing (load test)
- [ ] Security audit
- [ ] Accessibility audit (WCAG)
- [ ] Cross-browser testing

### 5.10 Documentation
- [ ] Complete user guide
- [ ] API documentation (OpenAPI)
- [ ] Deployment guide
- [ ] Troubleshooting guide
- [ ] Video tutorials

---

## Quick Reference

### Running the Project

**Infrastructure:** Database in Docker, Backend/Frontend on host machine.

```bash
cd ~/projects/personal/agent-rangers

# 1. Start database services (PostgreSQL + Redis)
docker compose up -d

# 2. Start backend (in separate terminal)
cd backend
source venv/bin/activate  # or create: python -m venv venv && pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 3. Start frontend (in separate terminal)
cd frontend
npm install  # first time only
npm run dev -- --host
```

**Stop services:**
```bash
# Stop database
docker compose down

# Backend/Frontend: Ctrl+C in their terminals
```

### URLs
| Service | URL |
|---------|-----|
| Frontend | http://192.168.1.225:5173 |
| Backend API | http://192.168.1.225:8000 |
| API Docs | http://192.168.1.225:8000/docs |
| Health Check | http://192.168.1.225:8000/health |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6380 |

### Project Structure
```
agent-rangers/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI routes
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   └── services/      # Business logic
│   ├── alembic/           # Database migrations
│   ├── .env               # Local environment config
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/           # API client
│       ├── components/    # React components
│       ├── hooks/         # Custom hooks
│       ├── stores/        # Zustand stores
│       └── types/         # TypeScript types
├── .claude/               # Claude-flow config (Phase 3)
│   └── agents/            # Agent definitions
├── docs/
│   └── ARCHITECTURE.md    # Full architecture doc
├── docker-compose.yml     # Database services only
└── ROADMAP.md             # This file
```

### Database Migrations
```bash
cd ~/projects/personal/agent-rangers/backend
source venv/bin/activate

# Create new migration
alembic revision --autogenerate -m "description"

# Run migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## Progress Summary

| Phase | Status | Progress |
|-------|--------|----------|
| Phase 1: Foundation | ✅ Complete | 100% |
| Phase 2: Workflow Engine | ✅ Complete | 100% |
| Phase 3: Claude-Flow | ✅ Complete | 100% |
| Phase 4: Knowledge (RAG) | 🔲 Not Started | 0% |
| Phase 5: Polish | 🔲 Not Started | 0% |

**Overall Progress:** ~60% (Phase 1, 2, 3 complete)

---

*Last updated: 2026-02-04*
