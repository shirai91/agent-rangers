# PRD.md - Product Requirements Document
## Agent Rangers: AI Multi-Agent Kanban Framework

**Version:** 2.0
**Last Updated:** 2026-02-04
**Status:** Phase 1-2 Complete, Phase 3 In Progress

---

## 1. Executive Summary

### 1.1 Product Vision
Agent Rangers is an AI-powered Kanban board framework that enables AI agents (Software Architect, Developer, Code Reviewer) to collaborate on software development tasks. Tasks flow through user-defined workflow columns, with AI agents automatically engaging when tasks enter designated "agent trigger" columns.

### 1.2 Problem Statement
Traditional Kanban boards require manual task execution. Software teams spend significant time on routine architecture decisions, code implementation, and code reviews. There's no existing solution that integrates multi-agent AI collaboration directly into a Kanban workflow.

### 1.3 Solution
A full-stack Kanban application with:
- Standard board/column/task management with drag-and-drop
- AI agent integration via Hybrid Orchestrator (Direct API + Claude Agent SDK) for automated task processing
- Workflow engine with configurable transitions and agent triggers
- Knowledge base (RAG) for context-aware agent assistance

### 1.4 Target Users
1. **Solo Developers** - Wanting AI assistance for architecture, implementation, and code review
2. **Small Teams** - Coordinating AI-assisted development workflows
3. **AI Enthusiasts** - Experimenting with multi-agent collaboration patterns

---

## 2. Product Scope

### 2.1 In Scope (MVP - Phase 1-3)

#### Core Kanban Features
- [x] Create, read, update, delete boards
- [x] Create, read, update, delete columns within boards
- [x] Create, read, update, delete tasks within columns
- [x] Drag-and-drop tasks between columns
- [x] Drag-and-drop to reorder tasks within columns
- [x] Real-time sync via WebSocket
- [x] Optimistic UI updates with conflict resolution
- [x] URL-based routing (`/boards/:boardId`)

#### Workflow Engine (Phase 2)
- [ ] Define allowed transitions between columns
- [ ] Configure columns as "agent trigger" columns
- [ ] Visual workflow editor (arrows between columns)
- [ ] Task activity logging and history
- [ ] WIP (Work In Progress) limits per column

#### Agent Integration (Phase 3)
- [ ] Software Architect agent - designs technical approaches
- [ ] Software Developer agent - implements code
- [ ] Code Reviewer agent - reviews code quality
- [ ] Automatic agent triggering on column entry
- [ ] Real-time agent output streaming
- [ ] Agent execution history and cost tracking

### 2.2 In Scope (Extended - Phase 4-5)

#### Knowledge Base (Phase 4)
- [ ] RAG-based context retrieval
- [ ] Project file indexing with pgvector
- [ ] Semantic search across knowledge base
- [ ] Automatic indexing of agent outputs

#### Polish & Optimization (Phase 5)
- [ ] Performance metrics dashboard
- [ ] Cost tracking and limits
- [ ] Keyboard shortcuts
- [ ] Advanced search and filtering
- [ ] Export/import functionality
- [ ] Dark mode

### 2.3 Out of Scope (Explicitly NOT Building)

1. **User Authentication** - No login, single-user local deployment
2. **Multi-tenancy** - No organization/team management
3. **Permissions/Roles** - No access control
4. **Cloud Deployment** - Local Docker deployment only
5. **Mobile Native Apps** - Web only (responsive)
6. **Integrations** - No Slack, GitHub, Jira integrations
7. **Comments/Mentions** - No collaboration features
8. **File Attachments** - No file upload to tasks
9. **Time Tracking** - No time estimates or logging
10. **Recurring Tasks** - No task templates or recurrence
11. **Calendar View** - Kanban view only
12. **Gantt Charts** - No timeline views
13. **Billing/Payments** - No monetization features

---

## 3. User Stories

### 3.1 Board Management

| ID | User Story | Acceptance Criteria |
|----|------------|---------------------|
| B1 | As a user, I want to create a new board | - Click "New Board" button<br>- Enter name (required) and description (optional)<br>- Board appears in list immediately |
| B2 | As a user, I want to see all my boards | - Board list shows on homepage (`/`)<br>- Each card shows name, description<br>- Boards sorted by creation date |
| B3 | As a user, I want to open a board | - Click board card to navigate<br>- URL changes to `/boards/:id`<br>- Board loads with columns and tasks |
| B4 | As a user, I want to delete a board | - Click menu → Delete<br>- Confirmation dialog appears<br>- All columns and tasks cascade deleted |

### 3.2 Column Management

| ID | User Story | Acceptance Criteria |
|----|------------|---------------------|
| C1 | As a user, I want to create columns | - Click "Add Column" button<br>- Enter name (required)<br>- Column appears at end |
| C2 | As a user, I want to rename a column | - Click edit on column header<br>- Edit name in dialog<br>- Name updates immediately |
| C3 | As a user, I want to delete a column | - Click delete on column header<br>- Confirmation if tasks exist<br>- All tasks in column deleted |
| C4 | As a user, I want to reorder columns | - Drag column header<br>- Visual feedback during drag<br>- Column order persists |

### 3.3 Task Management

| ID | User Story | Acceptance Criteria |
|----|------------|---------------------|
| T1 | As a user, I want to create a task | - Click "Add Task" in column<br>- Enter title (required), description (optional)<br>- Task appears at column bottom |
| T2 | As a user, I want to edit a task | - Click task card<br>- Edit dialog with all fields<br>- Changes save on submit |
| T3 | As a user, I want to move a task | - Drag task to another column<br>- Task moves with animation<br>- Order updates immediately |
| T4 | As a user, I want to reorder tasks | - Drag task within column<br>- Other tasks shift to make room<br>- New order persists |
| T5 | As a user, I want to delete a task | - Click menu → Delete on task<br>- Task removed immediately<br>- No confirmation (single task) |
| T6 | As a user, I want to set task priority | - Edit task → select priority<br>- Options: Low, Medium, High, Urgent<br>- Priority badge shows on card |

### 3.4 Real-time Sync

| ID | User Story | Acceptance Criteria |
|----|------------|---------------------|
| R1 | As a user, I want to see real-time updates | - Open board in two tabs<br>- Create task in tab 1<br>- Task appears in tab 2 within 1 second |
| R2 | As a user, I want to see move sync | - Move task in tab 1<br>- Task moves in tab 2<br>- No duplicate or missing tasks |
| R3 | As a user, I want conflict resolution | - Edit same task in two tabs<br>- Second save shows conflict<br>- User can retry with latest version |

### 3.5 Workflow Engine (Phase 2)

| ID | User Story | Acceptance Criteria |
|----|------------|---------------------|
| W1 | As a user, I want to define transitions | - Open workflow editor<br>- Draw arrows between columns<br>- Only allowed moves work |
| W2 | As a user, I want to see task history | - Open task detail<br>- Activity tab shows all changes<br>- Shows who/what made change |
| W3 | As a user, I want WIP limits | - Set limit on column<br>- Warning when at limit<br>- Block when over limit |

### 3.6 Agent Integration (Phase 3)

| ID | User Story | Acceptance Criteria |
|----|------------|---------------------|
| A1 | As a user, I want to trigger agents | - Move task to "In Development" column<br>- Agent starts automatically<br>- Progress shown on task |
| A2 | As a user, I want to see agent output | - Click task during processing<br>- See real-time streaming output<br>- Code blocks formatted |
| A3 | As a user, I want to cancel agents | - Click "Cancel" on running task<br>- Agent stops within 5 seconds<br>- Task returns to previous column |
| A4 | As a user, I want to track costs | - See token usage per task<br>- See cost estimate<br>- Dashboard shows totals |

---

## 4. Functional Requirements

### 4.1 Board Entity

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| id | UUID | Auto | Primary key |
| name | string | Yes | 1-255 characters |
| description | string | No | 0-1000 characters |
| settings | JSON | No | Board configuration |
| created_at | timestamp | Auto | UTC |
| updated_at | timestamp | Auto | UTC |

### 4.2 Column Entity

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| id | UUID | Auto | Primary key |
| board_id | UUID | Yes | Foreign key to boards |
| name | string | Yes | 1-255 characters |
| order | float | Auto | Fractional ordering |
| color | string | No | Hex color code |
| wip_limit | integer | No | 0 = unlimited |
| triggers_agents | boolean | No | Default false |
| is_start_column | boolean | No | Default false |
| is_end_column | boolean | No | Default false |
| created_at | timestamp | Auto | UTC |
| updated_at | timestamp | Auto | UTC |

### 4.3 Task Entity

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| id | UUID | Auto | Primary key |
| board_id | UUID | Yes | Foreign key to boards |
| column_id | UUID | Yes | Foreign key to columns |
| title | string | Yes | 1-255 characters |
| description | string | No | 0-5000 characters |
| assigned_to | string | No | Agent or user identifier |
| status | string | Yes | Default "open" |
| priority | string | No | low/medium/high/urgent |
| order | float | Auto | Fractional ordering |
| version | integer | Auto | Optimistic locking |
| created_at | timestamp | Auto | UTC |
| updated_at | timestamp | Auto | UTC |

### 4.4 API Response Codes

| Operation | Success | Error Cases |
|-----------|---------|-------------|
| GET list | 200 OK | 500 Server Error |
| GET single | 200 OK | 404 Not Found |
| POST create | 201 Created | 400 Validation, 409 Conflict |
| PUT update | 200 OK | 400 Validation, 404 Not Found, 409 Conflict |
| PUT move | 200 OK | 403 Forbidden (workflow), 404 Not Found, 409 Version Conflict |
| DELETE | 204 No Content | 404 Not Found |

---

## 5. Non-Functional Requirements

### 5.1 Performance

| Metric | Target |
|--------|--------|
| Page load time | < 2 seconds |
| API response time | < 500ms (p95) |
| WebSocket latency | < 100ms |
| Drag-drop response | < 50ms |
| Support concurrent boards | 10+ |
| Support tasks per board | 500+ |

### 5.2 Reliability

| Metric | Target |
|--------|--------|
| Uptime (local) | N/A |
| Data persistence | PostgreSQL with Docker volume |
| Crash recovery | Docker restart policy |
| Data loss prevention | Optimistic locking |

### 5.3 Compatibility

| Platform | Support |
|----------|---------|
| Chrome | Latest 2 versions |
| Firefox | Latest 2 versions |
| Safari | Latest 2 versions |
| Edge | Latest 2 versions |
| Mobile browsers | Responsive design |
| Screen sizes | 320px - 4K |

### 5.4 Security

| Requirement | Implementation |
|-------------|----------------|
| SQL Injection | SQLAlchemy ORM, parameterized queries |
| XSS | React auto-escaping |
| CORS | Configured for localhost only |
| Input validation | Pydantic schemas |

---

## 6. Success Criteria

### 6.1 Phase 1 (Foundation) ✅

- [x] User can create a board and see it in the list
- [x] User can add columns to a board
- [x] User can add tasks to columns
- [x] User can drag tasks between columns
- [x] Changes sync across browser tabs in real-time
- [x] Optimistic updates feel instant
- [x] Version conflicts show meaningful error

### 6.2 Phase 2 (Workflow Engine)

- [ ] User can define which column transitions are allowed
- [ ] Invalid moves are visually blocked
- [ ] Task activity history shows all changes
- [ ] WIP limits prevent adding tasks to full columns

### 6.3 Phase 3 (Agent Integration)

- [ ] Moving task to trigger column starts agent workflow
- [ ] User sees real-time agent output
- [ ] Agent creates files in specified locations
- [ ] Agent workflow completes and moves task forward
- [ ] User can view execution history and costs

### 6.4 Phase 4 (Knowledge Base)

- [ ] Project files are automatically indexed
- [ ] Agents receive relevant context from knowledge base
- [ ] User can search indexed knowledge

### 6.5 Phase 5 (Polish)

- [ ] Dashboard shows agent execution metrics
- [ ] Cost tracking is accurate
- [ ] Keyboard shortcuts work
- [ ] Search finds tasks quickly

---

## 7. Timeline

| Phase | Duration | Start | End | Status |
|-------|----------|-------|-----|--------|
| Phase 1: Foundation | 2 weeks | 2026-02-03 | 2026-02-03 | ✅ Complete |
| Phase 2: Workflow | 2 weeks | TBD | TBD | 🔲 Not Started |
| Phase 3: Agents | 3 weeks | TBD | TBD | 🔲 Not Started |
| Phase 4: RAG | 2 weeks | TBD | TBD | 🔲 Not Started |
| Phase 5: Polish | 3 weeks | TBD | TBD | 🔲 Not Started |

**Total Estimated:** 12 weeks

---

## 8. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Anthropic API changes | Medium | High | Pin SDK version, monitor releases |
| Agent cost overrun | Medium | Medium | Implement cost limits, estimates |
| Performance with large boards | Low | Medium | Implement pagination, virtualization |
| WebSocket disconnects | Medium | Low | Auto-reconnect with exponential backoff |
| Version conflict frequency | Low | Low | Clear UI for conflict resolution |

---

## 9. Glossary

| Term | Definition |
|------|------------|
| Board | A container for columns and tasks, represents a project |
| Column | A vertical lane in the Kanban board, represents a workflow stage |
| Task | A work item that moves through columns |
| Agent | An AI entity that performs work on tasks |
| Workflow | The defined rules for how tasks can move between columns |
| Trigger Column | A column that automatically starts agent processing |
| Optimistic Locking | Preventing concurrent edits using version numbers |
| RAG | Retrieval-Augmented Generation - providing context to AI |

---

*Document Owner: Agent Rangers Team*  
*Review Cycle: Each phase completion*
