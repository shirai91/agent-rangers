# IMPLEMENTATION_PLAN.md - Build Sequence
## Agent Rangers: Step-by-Step Implementation Guide

**Version:** 1.0  
**Last Updated:** 2026-02-03

---

## 1. Overview

This document provides a **sequential build order** for Agent Rangers. Each step builds on the previous one. Do not skip steps.

### 1.1 Phase Summary

| Phase | Focus | Duration | Status |
|-------|-------|----------|--------|
| 1 | Core Kanban Foundation | 2 weeks | ✅ Complete |
| 2 | Workflow Engine | 2 weeks | ✅ Complete |
| 3 | Claude-Flow Integration | 3 weeks | ✅ Complete |
| 4 | Knowledge Base (RAG) | 2 weeks | 🔲 Not Started |
| 5 | Polish & Optimization | 3 weeks | 🔲 Not Started |

---

## 2. Phase 1: Core Kanban Foundation ✅

### Step 1.1: Project Setup
**Time:** 1 hour

```bash
# Create project directory
mkdir -p ~/projects/personal/agent-rangers
cd ~/projects/personal/agent-rangers

# Initialize git
git init

# Create directory structure
mkdir -p backend/app/{api,models,schemas,services}
mkdir -p backend/alembic/versions
mkdir -p frontend/src/{api,components,hooks,stores,types}
mkdir -p docs
```

**Deliverables:**
- [x] Directory structure created
- [x] Git repository initialized

---

### Step 1.2: Docker Compose Setup
**Time:** 30 minutes

Create `docker-compose.yml`:
- PostgreSQL 16 with health check
- Redis 7 with health check
- Backend service (will build Dockerfile later)
- Frontend service (will build Dockerfile later)

**Deliverables:**
- [x] `docker-compose.yml` created
- [x] Services start with `docker compose up`

---

### Step 1.3: Backend - Database Layer
**Time:** 2 hours

1. Create `backend/requirements.txt` with exact versions
2. Create `backend/Dockerfile`
3. Create `backend/app/database.py` - async SQLAlchemy setup
4. Create `backend/app/config.py` - settings from environment
5. Create `backend/alembic.ini`
6. Create `backend/alembic/env.py`

**Deliverables:**
- [x] Backend container builds
- [x] Database connection works
- [x] Alembic configured

---

### Step 1.4: Backend - Models
**Time:** 1 hour

Create SQLAlchemy models in order:

1. `backend/app/models/board.py` - Board model
2. `backend/app/models/column.py` - Column model (references Board)
3. `backend/app/models/task.py` - Task model (references Board, Column)
4. `backend/app/models/__init__.py` - Export all models

**Deliverables:**
- [x] All models created
- [x] Relationships defined
- [x] Models importable

---

### Step 1.5: Backend - Initial Migration
**Time:** 30 minutes

```bash
# Generate migration
docker exec agent-rangers-backend alembic revision --autogenerate -m "initial_schema"

# Review and edit migration file
# Run migration
docker exec agent-rangers-backend alembic upgrade head
```

**Deliverables:**
- [x] Migration file created: `001_initial_schema.py`
- [x] Tables created in database
- [x] Indexes created

---

### Step 1.6: Backend - Pydantic Schemas
**Time:** 1 hour

Create schemas in order:

1. `backend/app/schemas/board.py`
   - BoardCreate, BoardUpdate, BoardResponse, BoardListResponse

2. `backend/app/schemas/column.py`
   - ColumnCreate, ColumnUpdate, ColumnResponse

3. `backend/app/schemas/task.py`
   - TaskCreate, TaskUpdate, TaskMove, TaskResponse

4. `backend/app/schemas/__init__.py`

**Deliverables:**
- [x] All schemas created
- [x] Validation rules defined
- [x] Response models configured

---

### Step 1.7: Backend - Service Layer
**Time:** 2 hours

Create `backend/app/services/board_service.py`:

1. Board CRUD operations
2. Column CRUD operations
3. Task CRUD operations
4. Move task with optimistic locking
5. Fractional ordering logic

**Deliverables:**
- [x] All CRUD operations implemented
- [x] Optimistic locking works
- [x] Fractional ordering works

---

### Step 1.8: Backend - API Endpoints
**Time:** 2 hours

Create endpoints in order:

1. `backend/app/main.py` - FastAPI app setup, CORS, lifespan
2. `backend/app/api/boards.py` - Board endpoints
3. `backend/app/api/columns.py` - Column endpoints
4. `backend/app/api/tasks.py` - Task endpoints
5. `backend/app/api/__init__.py` - Router aggregation

**Test each endpoint with curl or API docs at `/docs`**

**Deliverables:**
- [x] All endpoints working
- [x] CORS configured
- [x] OpenAPI docs available

---

### Step 1.9: Backend - WebSocket
**Time:** 1 hour

Create `backend/app/api/websocket.py`:

1. ConnectionManager class
2. Board-specific rooms
3. Broadcast function
4. Connect/disconnect handlers

Update endpoints to broadcast changes.

**Deliverables:**
- [x] WebSocket connection works
- [x] Events broadcast to connected clients
- [x] Clean disconnect handling

---

### Step 1.10: Frontend - Project Setup
**Time:** 1 hour

```bash
cd frontend

# Initialize Vite project
npm create vite@latest . -- --template react-ts

# Install dependencies
npm install react-router-dom@^6.22.0 zustand@^4.5.0
npm install @dnd-kit/core@^6.1.0 @dnd-kit/sortable@^8.0.0 @dnd-kit/utilities@^3.2.2
npm install clsx@^2.1.0 tailwind-merge@^2.2.0 class-variance-authority@^0.7.0
npm install lucide-react@^0.316.0

# Setup Tailwind
npm install -D tailwindcss@^3.4.0 postcss@^8.4.33 autoprefixer@^10.4.17
npx tailwindcss init -p
```

Configure:
- `tailwind.config.js`
- `postcss.config.js`
- `tsconfig.json` - Add path aliases
- `vite.config.ts` - Add path aliases

**Deliverables:**
- [x] Frontend builds
- [x] Tailwind working
- [x] Path aliases working

---

### Step 1.11: Frontend - UI Components
**Time:** 2 hours

Create shadcn/ui components manually or via CLI:

1. `src/lib/utils.ts` - cn() utility
2. `src/components/ui/button.tsx`
3. `src/components/ui/card.tsx`
4. `src/components/ui/input.tsx`
5. `src/components/ui/label.tsx`
6. `src/components/ui/dialog.tsx`
7. `src/components/ui/dropdown-menu.tsx`
8. `src/components/ui/badge.tsx`
9. `src/components/ui/skeleton.tsx`
10. `src/components/ui/slot.tsx`

**Deliverables:**
- [x] All UI components created
- [x] Components styled correctly
- [x] Components exported

---

### Step 1.12: Frontend - Types
**Time:** 30 minutes

Create `src/types/index.ts`:

1. Board, Column, Task interfaces
2. CreateBoardInput, CreateColumnInput, CreateTaskInput
3. MoveTaskInput (with version)
4. WSEvent type

**Deliverables:**
- [x] All types defined
- [x] Types match backend schemas

---

### Step 1.13: Frontend - API Client
**Time:** 1 hour

Create `src/api/client.ts`:

1. ApiError and NetworkError classes
2. fetchJSON helper with timeout
3. Board API methods
4. Column API methods
5. Task API methods (including move)

**Deliverables:**
- [x] API client created
- [x] Error handling works
- [x] All endpoints covered

---

### Step 1.14: Frontend - State Store
**Time:** 2 hours

Create `src/stores/boardStore.ts`:

1. State interface (boards, currentBoard, columns, tasks, loading, error)
2. Board actions (fetch, create, delete)
3. Column actions (create, update, delete)
4. Task actions (create, update, move, delete)
5. Optimistic update helpers
6. WebSocket event handlers

**Deliverables:**
- [x] Store created
- [x] All actions implemented
- [x] Optimistic updates work

---

### Step 1.15: Frontend - WebSocket Hook
**Time:** 1 hour

Create `src/hooks/useWebSocket.ts`:

1. Connection state
2. Auto-reconnect with exponential backoff
3. Message handling → store updates
4. Cleanup on unmount

**Deliverables:**
- [x] Hook created
- [x] Reconnection works
- [x] Events update store

---

### Step 1.16: Frontend - Dialogs
**Time:** 1.5 hours

Create dialog components:

1. `src/components/CreateBoardDialog.tsx`
2. `src/components/CreateColumnDialog.tsx`
3. `src/components/CreateTaskDialog.tsx` (also handles edit)

**Deliverables:**
- [x] Dialogs created
- [x] Form validation works
- [x] Submit to API works

---

### Step 1.17: Frontend - Kanban Components
**Time:** 2 hours

Create kanban components:

1. `src/components/TaskCard.tsx` - Draggable task
2. `src/components/Column.tsx` - Droppable column
3. `src/components/Board.tsx` - DnD context, columns layout

**Deliverables:**
- [x] Components render
- [x] Drag and drop works
- [x] Tasks move correctly

---

### Step 1.18: Frontend - Main App
**Time:** 1.5 hours

Create routing and views:

1. Update `src/main.tsx` - Add BrowserRouter
2. Create `src/App.tsx`:
   - BoardsListView component (route: `/`)
   - BoardView component (route: `/boards/:boardId`)
   - Routes configuration

**Deliverables:**
- [x] Routing works
- [x] Board list displays
- [x] Board view displays
- [x] Navigation works

---

### Step 1.19: Integration Testing
**Time:** 2 hours

Test complete flow:

1. Create a board
2. Add columns
3. Add tasks
4. Drag tasks between columns
5. Open in two tabs, verify sync
6. Create version conflict, verify handling
7. Refresh page, verify persistence

**Deliverables:**
- [x] All features work end-to-end
- [x] WebSocket sync verified
- [x] Optimistic locking verified

---

### Step 1.20: Documentation & Commit
**Time:** 1 hour

1. Write README files
2. Create ROADMAP.md
3. Create ARCHITECTURE.md
4. Commit: "Phase 1 Complete: Core Kanban Foundation"

**Deliverables:**
- [x] Documentation complete
- [x] Code committed
- [x] Phase 1 complete!

---

## 3. Phase 2: Workflow Engine ✅

### Step 2.1: Database Schema Updates
**Time:** 2 hours

Create migration `002_workflow_engine.py`:

1. Add `workflow_definitions` table
2. Add `workflow_transitions` table
3. Add `task_activities` table
4. Add columns to `columns` table (triggers_agents, etc.)

---

### Step 2.2: Backend - Workflow Models
**Time:** 1.5 hours

1. Create WorkflowDefinition model
2. Create WorkflowTransition model
3. Create TaskActivity model
4. Update Column model with new fields

---

### Step 2.3: Backend - Workflow Service
**Time:** 3 hours

Create WorkflowService:

1. CRUD for workflow definitions
2. CRUD for transitions
3. Validate transitions
4. Get allowed targets

---

### Step 2.4: Backend - Activity Service
**Time:** 2 hours

Create ActivityService:

1. Log activity on all task changes
2. Get task activity history
3. Get board activity feed

---

### Step 2.5: Backend - Workflow API
**Time:** 2 hours

Add endpoints:

1. Workflow definition endpoints
2. Transition endpoints
3. Activity endpoints
4. Update task move to validate transitions

---

### Step 2.6: Frontend - XState Integration
**Time:** 3 hours

1. Install xstate dependencies
2. Create workflow machine factory
3. Create useWorkflow hook

---

### Step 2.7: Frontend - Workflow Types & API
**Time:** 1 hour

1. Add workflow types
2. Add workflow API methods

---

### Step 2.8: Frontend - Store Updates
**Time:** 2 hours

1. Add workflow state to store
2. Update move task with validation
3. Handle workflow events

---

### Step 2.9: Frontend - Workflow Editor UI
**Time:** 4 hours

1. WorkflowEditor component
2. TransitionArrow component
3. TransitionEditor dialog
4. ColumnSettings dialog

---

### Step 2.10: Frontend - Drop Zone Validation
**Time:** 2 hours

1. Fetch allowed targets on board load
2. Visual feedback for valid/invalid drops
3. Update Column component

---

### Step 2.11: Frontend - Activity Feed
**Time:** 3 hours

1. ActivityFeed component
2. ActivityItem component
3. TaskActivityPanel component

---

### Step 2.12: Testing & Commit
**Time:** 2 hours

1. Test workflow transitions
2. Test activity logging
3. Commit: "Phase 2 Complete: Workflow Engine"

---

## 4. Phase 3: Claude-Flow Integration ✅

### Step 3.1: Claude-Flow Setup
**Time:** 1 hour

```bash
npm install -g claude-flow@v3alpha
claude-flow init
mkdir -p .claude/agents
```

---

### Step 3.2: Agent Definition Files
**Time:** 2 hours

Create YAML files:

1. `.claude/agents/software-architect.yml`
2. `.claude/agents/software-developer.yml`
3. `.claude/agents/code-reviewer.yml`
4. `.claude/agents/queen-coordinator.yml`

---

### Step 3.3: Database Schema Updates
**Time:** 1.5 hours

Create migration `003_agent_execution.py`:

1. Add `agent_executions` table
2. Add `agent_outputs` table
3. Update `tasks` table with agent fields

---

### Step 3.4: Backend - Agent Models
**Time:** 1 hour

1. Create AgentExecution model
2. Create AgentOutput model
3. Update Task model

---

### Step 3.5: Backend - Agent Orchestrator
**Time:** 4 hours

Create AgentOrchestrator:

1. Initialize claude-flow swarm
2. Spawn agents
3. Execute workflows
4. Stream output
5. Handle completion

---

### Step 3.6: Backend - Agent Workflow Service
**Time:** 3 hours

Create AgentWorkflowService:

1. Start architecture phase
2. Start development phase
3. Start review phase
4. Handle feedback loops

---

### Step 3.7: Backend - Agent Context Builder
**Time:** 2 hours

Create AgentContextBuilder:

1. Build context for each phase
2. Get previous outputs
3. Get project context

---

### Step 3.8: Backend - Agent API
**Time:** 2 hours

Add endpoints:

1. Start agent workflow
2. Get agent status
3. Cancel execution
4. Stream output (SSE)
5. Get execution history

---

### Step 3.9: Backend - Agent Trigger Integration
**Time:** 2 hours

1. Update task move to check triggers
2. Auto-start agents on trigger columns
3. Update task status

---

### Step 3.10: Frontend - Agent Types & API
**Time:** 1 hour

1. Add agent types
2. Add agent API methods

---

### Step 3.11: Frontend - Store Updates
**Time:** 2 hours

1. Add agent state to store
2. Handle agent WebSocket events
3. Polling fallback

---

### Step 3.12: Frontend - Agent Status Components
**Time:** 2 hours

1. AgentStatusBadge component
2. AgentStatusIndicator component
3. Update TaskCard

---

### Step 3.13: Frontend - Agent Execution Panel
**Time:** 3 hours

1. AgentExecutionPanel component
2. ExecutionDetails component
3. AgentOutputViewer component

---

### Step 3.14: Frontend - Agent Control UI
**Time:** 2 hours

1. AgentControlPanel component
2. Add trigger buttons
3. Add status to column headers

---

### Step 3.15: Testing & Commit
**Time:** 3 hours

1. Test full agent workflow
2. Test output streaming
3. Test cancellation
4. Commit: "Phase 3 Complete: Claude-Flow Integration"

---

## 5. Phase 4: Knowledge Base (RAG) 🔲

### Step 4.1: pgvector Setup
**Time:** 1 hour

1. Add pgvector extension to PostgreSQL
2. Create migration `004_knowledge_base.py`
3. Create `knowledge_chunks` table

---

### Step 4.2: Embedding Service
**Time:** 2 hours

1. Install Ollama locally
2. Pull nomic-embed-text model
3. Create EmbeddingService class

---

### Step 4.3: Document Chunking Service
**Time:** 2 hours

1. Create ChunkingService class
2. Implement semantic chunking
3. Implement code-aware chunking

---

### Step 4.4: Knowledge Indexing Service
**Time:** 3 hours

1. Create KnowledgeIndexer class
2. Index files
3. Index agent outputs
4. Handle incremental indexing

---

### Step 4.5: RAG Retrieval Service
**Time:** 2 hours

1. Create RAGService class
2. Vector similarity search
3. Hybrid search
4. Context building

---

### Step 4.6: Backend - Knowledge API
**Time:** 1.5 hours

Add endpoints:

1. Trigger indexing
2. Get indexing status
3. Search knowledge base

---

### Step 4.7: Agent Context Integration
**Time:** 2 hours

1. Update AgentContextBuilder to use RAG
2. Auto-index agent outputs

---

### Step 4.8: Frontend - Knowledge UI
**Time:** 2 hours

1. KnowledgePanel component
2. KnowledgeSearch component
3. Add to board settings

---

### Step 4.9: Testing & Commit
**Time:** 2 hours

1. Test indexing
2. Test retrieval
3. Test agent context
4. Commit: "Phase 4 Complete: Knowledge Base"

---

## 6. Phase 5: Polish & Optimization 🔲

### Step 5.1: Performance Dashboard
**Time:** 3 hours

1. Create MetricsDashboard page
2. Add charts for agent metrics
3. Add date filtering

---

### Step 5.2: Cost Tracking
**Time:** 2 hours

1. Implement token counting
2. Implement cost calculation
3. Add cost estimates

---

### Step 5.3: Error Handling & Retry
**Time:** 2 hours

1. Add retry logic for agents
2. Add circuit breaker
3. Improve error messages

---

### Step 5.4: Concurrent Update Handling
**Time:** 2 hours

1. Conflict resolution dialog
2. Real-time collaboration indicators

---

### Step 5.5: UI/UX Improvements
**Time:** 3 hours

1. Add keyboard shortcuts
2. Add bulk operations
3. Improve mobile responsiveness
4. Add dark mode

---

### Step 5.6: Search & Filtering
**Time:** 2 hours

1. Add global search
2. Add advanced filters
3. Save filter presets

---

### Step 5.7: Notifications
**Time:** 2 hours

1. In-app notifications
2. Browser notifications
3. Notification preferences

---

### Step 5.8: Export & Import
**Time:** 2 hours

1. Export board data
2. Import from JSON
3. Basic Trello import

---

### Step 5.9: Final Testing
**Time:** 3 hours

1. Full E2E test suite
2. Performance testing
3. Security audit
4. Accessibility audit

---

### Step 5.10: Documentation & Launch
**Time:** 2 hours

1. Complete user guide
2. API documentation
3. Deployment guide
4. Final commit: "Phase 5 Complete: Production Ready"

---

## 7. Verification Checklist

### After Each Step

- [ ] Code compiles without errors
- [ ] Tests pass (if applicable)
- [ ] Feature works as expected
- [ ] No console errors
- [ ] Documentation updated (if needed)

### After Each Phase

- [ ] All steps completed
- [ ] Integration tested
- [ ] Performance acceptable
- [ ] Code reviewed
- [ ] Committed with descriptive message

---

## 8. Rollback Plan

If a step fails:

1. **Don't panic** - Git has your back
2. **Identify the issue** - Check logs, errors
3. **Rollback if needed** - `git checkout .` or `git reset --hard HEAD~1`
4. **Fix and retry** - Address the root cause
5. **Document the issue** - Update this plan if needed

---

## 9. Time Estimates Summary

| Phase | Estimated | Actual |
|-------|-----------|--------|
| Phase 1 | 40 hours | ~2 hours (AI-assisted) |
| Phase 2 | 60 hours | TBD |
| Phase 3 | 80 hours | TBD |
| Phase 4 | 60 hours | TBD |
| Phase 5 | 50 hours | TBD |
| **Total** | **290 hours** | TBD |

---

*Document Owner: Agent Rangers Team*  
*Review Cycle: Each phase completion*
