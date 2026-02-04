# APP_FLOW.md - Application Flow Documentation
## Agent Rangers: User Navigation & Interaction Flows

**Version:** 2.0
**Last Updated:** 2026-02-04

---

## 1. Screen Inventory

### 1.1 Current Screens (Phase 1)

| Screen | Route | Component | Description |
|--------|-------|-----------|-------------|
| Board List | `/` | `BoardsListView` | Homepage showing all boards |
| Board View | `/boards/:boardId` | `BoardView` | Kanban board with columns and tasks |

### 1.2 Planned Screens (Future Phases)

| Screen | Route | Component | Phase |
|--------|-------|-----------|-------|
| Board Settings | `/boards/:boardId/settings` | `BoardSettings` | Phase 2 |
| Workflow Editor | `/boards/:boardId/workflow` | `WorkflowEditor` | Phase 2 |
| Task Detail | `/boards/:boardId/tasks/:taskId` | `TaskDetail` | Phase 2 |
| Activity Feed | `/boards/:boardId/activity` | `ActivityFeed` | Phase 2 |
| Dashboard | `/dashboard` | `MetricsDashboard` | Phase 5 |
| Knowledge Search | `/boards/:boardId/knowledge` | `KnowledgeSearch` | Phase 4 |

---

## 2. User Flows

### 2.1 Application Entry Flow

```
User opens http://192.168.1.225:5173
    │
    ▼
┌─────────────────────────────┐
│     Board List View (/)     │
│  ┌─────────────────────────┤
│  │ Header: "Agent Rangers"  │
│  │ Button: "+ New Board"    │
│  ├─────────────────────────┤
│  │ Board Cards Grid:        │
│  │  ┌──────┐ ┌──────┐      │
│  │  │Board1│ │Board2│      │
│  │  └──────┘ └──────┘      │
│  └─────────────────────────┘
└─────────────────────────────┘
```

**Entry Points:**
- Direct URL: `http://192.168.1.225:5173` → Board List
- Direct URL: `http://192.168.1.225:5173/boards/:id` → Board View
- Browser back/forward → Respective route

**Initial Load Sequence:**
1. React app initializes
2. `BoardsListView` mounts
3. Calls `fetchBoards()` from store
4. Shows loading skeletons
5. API returns boards list
6. Renders board cards

---

### 2.2 Create Board Flow

```
Board List View
    │
    │ User clicks "+ New Board"
    ▼
┌─────────────────────────────┐
│    CreateBoardDialog        │
│  ┌─────────────────────────┤
│  │ Name: [____________]     │ ◄── Required
│  │ Description: [_____]     │ ◄── Optional
│  │                          │
│  │ [Cancel]    [Create]     │
│  └─────────────────────────┘
└─────────────────────────────┘
    │
    │ User fills name, clicks "Create"
    ▼
┌─────────────────────────────┐
│ Validation                  │
├─────────────────────────────┤
│ Name empty?                 │
│   YES → Show error, stop    │
│   NO  → Continue            │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│ API Call                    │
│ POST /api/boards            │
│ Body: { name, description } │
└─────────────────────────────┘
    │
    ├── Success (201) ──────────────┐
    │                               ▼
    │                   ┌─────────────────────┐
    │                   │ Dialog closes       │
    │                   │ Board added to list │
    │                   │ Success feedback    │
    │                   └─────────────────────┘
    │
    └── Error (4xx/5xx) ────────────┐
                                    ▼
                        ┌─────────────────────┐
                        │ Show error message  │
                        │ Keep dialog open    │
                        │ User can retry      │
                        └─────────────────────┘
```

---

### 2.3 Open Board Flow

```
Board List View
    │
    │ User clicks board card
    ▼
┌─────────────────────────────┐
│ Navigation                  │
│ navigate(`/boards/${id}`)   │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│      Board View             │
│  ┌─────────────────────────┤
│  │ Header: Board Name       │
│  │ Button: "← Back"         │
│  ├─────────────────────────┤
│  │ Loading: Show skeletons  │
│  └─────────────────────────┘
└─────────────────────────────┘
    │
    │ BoardView mounts
    ▼
┌─────────────────────────────┐
│ Parallel Operations:        │
│ 1. fetchBoard(boardId)      │
│ 2. WebSocket connect        │
└─────────────────────────────┘
    │
    │ API returns board data
    ▼
┌─────────────────────────────┐
│      Board View (Loaded)    │
│  ┌──────┬──────┬──────┐    │
│  │ Col1 │ Col2 │ Col3 │    │
│  ├──────┼──────┼──────┤    │
│  │Task1 │Task3 │      │    │
│  │Task2 │      │      │    │
│  └──────┴──────┴──────┘    │
└─────────────────────────────┘
```

---

### 2.4 Create Column Flow

```
Board View
    │
    │ User clicks "+ Add Column"
    ▼
┌─────────────────────────────┐
│   CreateColumnDialog        │
│  ┌─────────────────────────┤
│  │ Name: [____________]     │ ◄── Required
│  │                          │
│  │ [Cancel]    [Create]     │
│  └─────────────────────────┘
└─────────────────────────────┘
    │
    │ User enters name, clicks "Create"
    ▼
┌─────────────────────────────┐
│ API Call                    │
│ POST /api/boards/:id/columns│
│ Body: { name }              │
└─────────────────────────────┘
    │
    ├── Success (201) ──────────────┐
    │                               ▼
    │                   ┌─────────────────────┐
    │                   │ Dialog closes       │
    │                   │ Column appears      │
    │                   │ WebSocket broadcasts│
    │                   └─────────────────────┘
    │
    └── Error ──────────────────────┐
                                    ▼
                        ┌─────────────────────┐
                        │ Show error toast    │
                        │ Keep dialog open    │
                        └─────────────────────┘
```

---

### 2.5 Create Task Flow

```
Board View → Column
    │
    │ User clicks "+ Add Task" in column
    ▼
┌─────────────────────────────┐
│    CreateTaskDialog         │
│  ┌─────────────────────────┤
│  │ Title: [___________]     │ ◄── Required
│  │ Description: [_____]     │ ◄── Optional
│  │ Priority: [Dropdown]     │ ◄── Optional
│  │                          │
│  │ [Cancel]    [Create]     │
│  └─────────────────────────┘
└─────────────────────────────┘
    │
    │ User fills form, clicks "Create"
    ▼
┌─────────────────────────────┐
│ API Call                    │
│ POST /api/boards/:id/tasks  │
│ Body: {                     │
│   column_id,                │
│   title,                    │
│   description,              │
│   priority                  │
│ }                           │
└─────────────────────────────┘
    │
    ├── Success (201) ──────────────┐
    │                               ▼
    │                   ┌─────────────────────┐
    │                   │ Dialog closes       │
    │                   │ Task appears in col │
    │                   │ Scroll to task      │
    │                   │ WebSocket broadcasts│
    │                   └─────────────────────┘
    │
    └── Error ──────────────────────┐
                                    ▼
                        ┌─────────────────────┐
                        │ Show error message  │
                        │ Keep dialog open    │
                        └─────────────────────┘
```

---

### 2.6 Drag and Drop Task Flow

```
Board View
    │
    │ User starts dragging task card
    ▼
┌─────────────────────────────┐
│ DndContext onDragStart      │
│ ├─ Store original task state│
│ ├─ Show drag overlay        │
│ └─ Highlight drop zones     │
└─────────────────────────────┘
    │
    │ User drags over columns
    ▼
┌─────────────────────────────┐
│ DndContext onDragOver       │
│ ├─ Calculate drop position  │
│ └─ Visual feedback          │
└─────────────────────────────┘
    │
    │ User drops task
    ▼
┌─────────────────────────────┐
│ DndContext onDragEnd        │
│ ├─ Determine target column  │
│ ├─ Calculate new order      │
│ └─ Optimistic update        │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│ Optimistic Update           │
│ ├─ Immediately move task UI │
│ └─ User sees instant move   │
└─────────────────────────────┘
    │
    │ Background API call
    ▼
┌─────────────────────────────┐
│ API Call                    │
│ PUT /api/tasks/:id/move     │
│ Body: {                     │
│   column_id: target,        │
│   order: calculated,        │
│   version: current          │
│ }                           │
└─────────────────────────────┘
    │
    ├── Success (200) ──────────────┐
    │                               ▼
    │                   ┌─────────────────────┐
    │                   │ Update task version │
    │                   │ WebSocket broadcasts│
    │                   │ No visible change   │
    │                   └─────────────────────┘
    │
    └── Error (409 Conflict) ───────┐
                                    ▼
                        ┌─────────────────────┐
                        │ Revert optimistic   │
                        │ Task returns to     │
                        │ original position   │
                        │ Show error toast    │
                        │ "Task was modified" │
                        └─────────────────────┘
```

---

### 2.7 Edit Task Flow

```
Board View
    │
    │ User clicks task card
    ▼
┌─────────────────────────────┐
│    CreateTaskDialog (Edit)  │
│  ┌─────────────────────────┤
│  │ Title: [Current Title]   │
│  │ Description: [Current]   │
│  │ Priority: [Current]      │
│  │ Status: [Current]        │
│  │                          │
│  │ [Cancel]    [Save]       │
│  └─────────────────────────┘
└─────────────────────────────┘
    │
    │ User modifies, clicks "Save"
    ▼
┌─────────────────────────────┐
│ API Call                    │
│ PUT /api/tasks/:id          │
│ Body: { ...changes }        │
└─────────────────────────────┘
    │
    ├── Success (200) ──────────────┐
    │                               ▼
    │                   ┌─────────────────────┐
    │                   │ Dialog closes       │
    │                   │ Task updates        │
    │                   │ WebSocket broadcasts│
    │                   └─────────────────────┘
    │
    └── Error ──────────────────────┐
                                    ▼
                        ┌─────────────────────┐
                        │ Show error          │
                        │ Keep dialog open    │
                        └─────────────────────┘
```

---

### 2.8 Delete Task Flow

```
Board View → Task Card Menu
    │
    │ User clicks "..." → "Delete"
    ▼
┌─────────────────────────────┐
│ No Confirmation             │
│ (Single task deletion)      │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│ Optimistic Update           │
│ ├─ Remove task from UI      │
│ └─ User sees instant delete │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│ API Call                    │
│ DELETE /api/tasks/:id       │
└─────────────────────────────┘
    │
    ├── Success (204) ──────────────┐
    │                               ▼
    │                   ┌─────────────────────┐
    │                   │ WebSocket broadcasts│
    │                   │ No visible change   │
    │                   └─────────────────────┘
    │
    └── Error ──────────────────────┐
                                    ▼
                        ┌─────────────────────┐
                        │ Restore task to UI  │
                        │ Show error toast    │
                        └─────────────────────┘
```

---

### 2.9 Delete Board Flow

```
Board List View → Board Card Menu
    │
    │ User clicks "..." → "Delete"
    ▼
┌─────────────────────────────┐
│ Confirmation Dialog         │
│ "Delete this board? All     │
│ columns and tasks will be   │
│ deleted."                   │
│ [Cancel]      [Delete]      │
└─────────────────────────────┘
    │
    │ User confirms
    ▼
┌─────────────────────────────┐
│ API Call                    │
│ DELETE /api/boards/:id      │
└─────────────────────────────┘
    │
    ├── Success (204) ──────────────┐
    │                               ▼
    │                   ┌─────────────────────┐
    │                   │ Remove from list    │
    │                   │ Show success toast  │
    │                   └─────────────────────┘
    │
    └── Error ──────────────────────┐
                                    ▼
                        ┌─────────────────────┐
                        │ Show error toast    │
                        │ Board remains       │
                        └─────────────────────┘
```

---

### 2.10 Navigate Back Flow

```
Board View
    │
    │ User clicks "← Back to Boards"
    ▼
┌─────────────────────────────┐
│ Navigation                  │
│ navigate('/')               │
└─────────────────────────────┘
    │
    │ BoardView unmounts
    ▼
┌─────────────────────────────┐
│ Cleanup                     │
│ ├─ WebSocket disconnects    │
│ └─ Board state clears       │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│ Board List View             │
│ ├─ Fetch fresh board list   │
│ └─ Display boards           │
└─────────────────────────────┘
```

---

## 3. WebSocket Events

### 3.1 Connection Flow

```
BoardView mounts with boardId
    │
    ▼
┌─────────────────────────────┐
│ WebSocket Connect           │
│ ws://192.168.1.225:8000/    │
│   ws/board/{boardId}        │
└─────────────────────────────┘
    │
    ├── Connect Success ────────────┐
    │                               ▼
    │                   ┌─────────────────────┐
    │                   │ Connection open     │
    │                   │ Ready to receive    │
    │                   └─────────────────────┘
    │
    └── Connect Fail ───────────────┐
                                    ▼
                        ┌─────────────────────┐
                        │ Start reconnect     │
                        │ Exponential backoff │
                        │ Max 5 attempts      │
                        └─────────────────────┘
```

### 3.2 Event Types

| Event | Payload | Action |
|-------|---------|--------|
| `task_created` | `Task` | Add task to store |
| `task_updated` | `Task` | Update task in store |
| `task_moved` | `Task` | Move task in store |
| `task_deleted` | `{ id }` | Remove task from store |
| `column_created` | `Column` | Add column to store |
| `column_updated` | `Column` | Update column in store |
| `column_deleted` | `{ id }` | Remove column from store |

### 3.3 Reconnection Flow

```
WebSocket disconnects unexpectedly
    │
    ▼
┌─────────────────────────────┐
│ Attempt 1: Wait 1 second    │
│ Attempt 2: Wait 2 seconds   │
│ Attempt 3: Wait 4 seconds   │
│ Attempt 4: Wait 8 seconds   │
│ Attempt 5: Wait 16 seconds  │
└─────────────────────────────┘
    │
    ├── Reconnect Success ──────────┐
    │                               ▼
    │                   ┌─────────────────────┐
    │                   │ Resume normal ops   │
    │                   │ May miss events     │
    │                   │ Consider refresh    │
    │                   └─────────────────────┘
    │
    └── All Attempts Fail ──────────┐
                                    ▼
                        ┌─────────────────────┐
                        │ Show connection err │
                        │ Manual refresh hint │
                        └─────────────────────┘
```

---

## 4. Error Handling Flows

### 4.1 API Error Flow

```
Any API Call
    │
    └── Error Response ─────────────┐
                                    ▼
                        ┌─────────────────────┐
                        │ Check status code   │
                        └─────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
   ┌─────────┐        ┌─────────┐        ┌─────────┐
   │ 400     │        │ 404     │        │ 409     │
   │ Bad Req │        │ Not     │        │Conflict │
   │         │        │ Found   │        │         │
   └────┬────┘        └────┬────┘        └────┬────┘
        │                  │                  │
        ▼                  ▼                  ▼
   Show form          Navigate to       Show conflict
   validation         board list        message, let
   errors             with toast        user retry
```

### 4.2 Network Error Flow

```
Any API Call
    │
    └── Network Error ──────────────┐
                                    ▼
                        ┌─────────────────────┐
                        │ Show offline toast  │
                        │ "Network error"     │
                        │ Retry button        │
                        └─────────────────────┘
```

---

## 5. Loading States

### 5.1 Board List Loading

```
Initial Load:
┌─────────────────────────────┐
│ Header: Agent Rangers       │
├─────────────────────────────┤
│ ┌──────────┐ ┌──────────┐  │
│ │ ▓▓▓▓▓▓▓▓ │ │ ▓▓▓▓▓▓▓▓ │  │ ◄── Skeleton cards
│ │ ▓▓▓▓▓▓   │ │ ▓▓▓▓▓▓   │  │
│ └──────────┘ └──────────┘  │
│ ┌──────────┐               │
│ │ ▓▓▓▓▓▓▓▓ │               │
│ │ ▓▓▓▓▓▓   │               │
│ └──────────┘               │
└─────────────────────────────┘
```

### 5.2 Board View Loading

```
Initial Load:
┌─────────────────────────────┐
│ ◄ Back   ▓▓▓▓▓▓▓▓           │ ◄── Skeleton header
├─────────────────────────────┤
│ ┌──────┐ ┌──────┐ ┌──────┐ │
│ │▓▓▓▓▓▓│ │▓▓▓▓▓▓│ │▓▓▓▓▓▓│ │ ◄── Skeleton columns
│ │▓▓▓▓  │ │▓▓▓▓  │ │▓▓▓▓  │ │
│ │▓▓▓▓  │ │▓▓▓▓  │ │      │ │
│ │      │ │      │ │      │ │
│ └──────┘ └──────┘ └──────┘ │
└─────────────────────────────┘
```

---

## 6. Future Flows (Phases 2-5)

### 6.1 Workflow Editor Flow (Phase 2)
- Board Settings → Workflow Tab
- Visual canvas with columns
- Draw arrows for transitions
- Set transition properties

### 6.2 Agent Trigger Flow (Phase 3)
- Task moves to trigger column
- Agent execution starts automatically
- Real-time output streaming
- Automatic move on completion

### 6.3 Knowledge Search Flow (Phase 4)
- Search box in board view
- Real-time results as typing
- Click result to view source
- Results influence agent context

---

*Document Owner: Agent Rangers Team*  
*Review Cycle: Each phase completion*
