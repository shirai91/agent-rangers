# BACKEND_STRUCTURE.md - Backend Architecture
## Agent Rangers: Database Schema, API Contracts, and Service Layer

**Version:** 2.0
**Last Updated:** 2026-02-04

---

## 1. Directory Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry
│   ├── config.py                  # Configuration settings
│   ├── database.py                # Database connection & session
│   ├── api/
│   │   ├── __init__.py
│   │   ├── boards.py              # Board endpoints
│   │   ├── columns.py             # Column endpoints
│   │   ├── tasks.py               # Task endpoints
│   │   ├── agents.py              # Agent execution endpoints
│   │   └── websocket.py           # WebSocket handler
│   ├── models/
│   │   ├── __init__.py
│   │   ├── board.py               # Board SQLAlchemy model
│   │   ├── column.py              # Column SQLAlchemy model
│   │   ├── task.py                # Task SQLAlchemy model
│   │   └── agent_execution.py     # Agent execution model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── board.py               # Board Pydantic schemas
│   │   ├── column.py              # Column Pydantic schemas
│   │   ├── task.py                # Task Pydantic schemas
│   │   └── agent.py               # Agent execution schemas
│   └── services/
│       ├── __init__.py
│       ├── board_service.py       # Board business logic
│       └── hybrid_orchestrator.py # AI agent orchestration
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 001_initial_schema.py
│       ├── 002_workflow_engine.py
│       └── 003_agent_execution.py
├── workspaces/                    # Agent workspace directories
│   └── {task_id}/                 # Per-task isolated workspace
├── alembic.ini
├── requirements.txt
├── Dockerfile
└── .env.example
```

---

## 2. Database Schema

### 2.1 Entity Relationship Diagram

```
┌─────────────────┐
│     boards      │
├─────────────────┤
│ id (PK)         │
│ name            │
│ description     │
│ settings        │
│ created_at      │
│ updated_at      │
└────────┬────────┘
         │
         │ 1:N
         │
┌────────┴────────┐
│    columns      │
├─────────────────┤
│ id (PK)         │
│ board_id (FK)   │───────┐
│ name            │       │
│ order           │       │
│ color           │       │
│ wip_limit       │       │
│ created_at      │       │
│ updated_at      │       │
└────────┬────────┘       │
         │                │
         │ 1:N            │
         │                │
┌────────┴────────┐       │
│     tasks       │       │
├─────────────────┤       │
│ id (PK)         │       │
│ board_id (FK)   │───────┘
│ column_id (FK)  │
│ title           │
│ description     │
│ assigned_to     │
│ status          │
│ priority        │
│ order           │
│ version         │
│ created_at      │
│ updated_at      │
└─────────────────┘
```

### 2.2 Table: boards

```sql
CREATE TABLE boards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_boards_created_at ON boards(created_at DESC);
```

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | UUID | NO | gen_random_uuid() | Primary key |
| name | VARCHAR(255) | NO | - | Board name |
| description | TEXT | YES | NULL | Optional description |
| settings | JSONB | NO | '{}' | Board configuration |
| created_at | TIMESTAMPTZ | NO | NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NO | NOW() | Last update timestamp |

### 2.3 Table: columns

```sql
CREATE TABLE columns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    board_id UUID NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    "order" DOUBLE PRECISION NOT NULL DEFAULT 0,
    color VARCHAR(7),
    wip_limit INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_columns_board_id ON columns(board_id);
CREATE INDEX idx_columns_order ON columns(board_id, "order");
```

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | UUID | NO | gen_random_uuid() | Primary key |
| board_id | UUID | NO | - | Foreign key to boards |
| name | VARCHAR(255) | NO | - | Column name |
| order | DOUBLE PRECISION | NO | 0 | Fractional ordering |
| color | VARCHAR(7) | YES | NULL | Hex color code |
| wip_limit | INTEGER | YES | NULL | Max tasks (NULL = unlimited) |
| created_at | TIMESTAMPTZ | NO | NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NO | NOW() | Last update timestamp |

### 2.4 Table: tasks

```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    board_id UUID NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
    column_id UUID NOT NULL REFERENCES columns(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    assigned_to VARCHAR(100),
    status VARCHAR(50) NOT NULL DEFAULT 'open',
    priority VARCHAR(20),
    "order" DOUBLE PRECISION NOT NULL DEFAULT 0,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tasks_board_id ON tasks(board_id);
CREATE INDEX idx_tasks_column_id ON tasks(column_id);
CREATE INDEX idx_tasks_order ON tasks(column_id, "order");
```

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | UUID | NO | gen_random_uuid() | Primary key |
| board_id | UUID | NO | - | Foreign key to boards |
| column_id | UUID | NO | - | Foreign key to columns |
| title | VARCHAR(255) | NO | - | Task title |
| description | TEXT | YES | NULL | Task description |
| assigned_to | VARCHAR(100) | YES | NULL | Assignee identifier |
| status | VARCHAR(50) | NO | 'open' | Task status |
| priority | VARCHAR(20) | YES | NULL | low/medium/high/urgent |
| order | DOUBLE PRECISION | NO | 0 | Fractional ordering |
| version | INTEGER | NO | 1 | Optimistic locking version |
| created_at | TIMESTAMPTZ | NO | NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NO | NOW() | Last update timestamp |

---

## 3. SQLAlchemy Models

### 3.1 Board Model

```python
# app/models/board.py
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base

class Board(Base):
    __tablename__ = "boards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    settings = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    columns = relationship("Column", back_populates="board", cascade="all, delete-orphan", order_by="Column.order")
    tasks = relationship("Task", back_populates="board", cascade="all, delete-orphan")
```

### 3.2 Column Model

```python
# app/models/column.py
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base

class Column(Base):
    __tablename__ = "columns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    board_id = Column(UUID(as_uuid=True), ForeignKey("boards.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    order = Column(Float, nullable=False, default=0)
    color = Column(String(7), nullable=True)
    wip_limit = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    board = relationship("Board", back_populates="columns")
    tasks = relationship("Task", back_populates="column", cascade="all, delete-orphan", order_by="Task.order")
```

### 3.3 Task Model

```python
# app/models/task.py
from sqlalchemy import Column, String, Text, Float, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    board_id = Column(UUID(as_uuid=True), ForeignKey("boards.id", ondelete="CASCADE"), nullable=False)
    column_id = Column(UUID(as_uuid=True), ForeignKey("columns.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    assigned_to = Column(String(100), nullable=True)
    status = Column(String(50), nullable=False, default="open")
    priority = Column(String(20), nullable=True)
    order = Column(Float, nullable=False, default=0)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    board = relationship("Board", back_populates="tasks")
    column = relationship("Column", back_populates="tasks")
```

---

## 4. Pydantic Schemas

### 4.1 Board Schemas

```python
# app/schemas/board.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class BoardBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)

class BoardCreate(BoardBase):
    pass

class BoardUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)

class BoardResponse(BoardBase):
    id: UUID
    settings: dict = {}
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BoardListResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class BoardDetailResponse(BoardResponse):
    columns: List["ColumnResponse"] = []
    tasks: List["TaskResponse"] = []
```

### 4.2 Column Schemas

```python
# app/schemas/column.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class ColumnBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

class ColumnCreate(ColumnBase):
    pass

class ColumnUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    wip_limit: Optional[int] = Field(None, ge=0)

class ColumnResponse(ColumnBase):
    id: UUID
    board_id: UUID
    order: float
    color: Optional[str]
    wip_limit: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

### 4.3 Task Schemas

```python
# app/schemas/task.py
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID

PriorityType = Literal["low", "medium", "high", "urgent"]

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    priority: Optional[PriorityType] = None

class TaskCreate(TaskBase):
    column_id: UUID

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    assigned_to: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, max_length=50)
    priority: Optional[PriorityType] = None

class TaskMove(BaseModel):
    column_id: UUID = Field(..., description="Target column ID")
    order: float = Field(..., description="New position order")
    version: int = Field(..., description="Current version for optimistic locking")

class TaskResponse(TaskBase):
    id: UUID
    board_id: UUID
    column_id: UUID
    assigned_to: Optional[str]
    status: str
    order: float
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

---

## 5. API Endpoints

### 5.1 Health Check

```
GET /health
```

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### 5.2 Board Endpoints

#### List Boards

```
GET /api/boards
```

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "name": "string",
    "description": "string | null",
    "created_at": "2026-02-03T12:00:00Z"
  }
]
```

#### Create Board

```
POST /api/boards
Content-Type: application/json

{
  "name": "string (required)",
  "description": "string (optional)"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "name": "string",
  "description": "string | null",
  "settings": {},
  "created_at": "2026-02-03T12:00:00Z",
  "updated_at": "2026-02-03T12:00:00Z"
}
```

**Errors:**
- `400 Bad Request` - Validation error

#### Get Board

```
GET /api/boards/{board_id}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "name": "string",
  "description": "string | null",
  "settings": {},
  "created_at": "2026-02-03T12:00:00Z",
  "updated_at": "2026-02-03T12:00:00Z",
  "columns": [
    {
      "id": "uuid",
      "board_id": "uuid",
      "name": "string",
      "order": 1.0,
      "color": "#FFFFFF",
      "wip_limit": null,
      "created_at": "2026-02-03T12:00:00Z",
      "updated_at": "2026-02-03T12:00:00Z"
    }
  ],
  "tasks": [
    {
      "id": "uuid",
      "board_id": "uuid",
      "column_id": "uuid",
      "title": "string",
      "description": "string | null",
      "assigned_to": "string | null",
      "status": "open",
      "priority": "medium",
      "order": 1.0,
      "version": 1,
      "created_at": "2026-02-03T12:00:00Z",
      "updated_at": "2026-02-03T12:00:00Z"
    }
  ]
}
```

**Errors:**
- `404 Not Found` - Board not found

#### Update Board

```
PUT /api/boards/{board_id}
Content-Type: application/json

{
  "name": "string (optional)",
  "description": "string (optional)"
}
```

**Response:** `200 OK`

**Errors:**
- `404 Not Found` - Board not found
- `400 Bad Request` - Validation error

#### Delete Board

```
DELETE /api/boards/{board_id}
```

**Response:** `204 No Content`

**Errors:**
- `404 Not Found` - Board not found

### 5.3 Column Endpoints

#### Create Column

```
POST /api/boards/{board_id}/columns
Content-Type: application/json

{
  "name": "string (required)"
}
```

**Response:** `201 Created`

#### Update Column

```
PUT /api/columns/{column_id}
Content-Type: application/json

{
  "name": "string (optional)",
  "color": "#FFFFFF (optional)",
  "wip_limit": 5 (optional)
}
```

**Response:** `200 OK`

#### Delete Column

```
DELETE /api/columns/{column_id}
```

**Response:** `204 No Content`

### 5.4 Task Endpoints

#### Create Task

```
POST /api/boards/{board_id}/tasks
Content-Type: application/json

{
  "column_id": "uuid (required)",
  "title": "string (required)",
  "description": "string (optional)",
  "priority": "low|medium|high|urgent (optional)"
}
```

**Response:** `201 Created`

#### Get Task

```
GET /api/tasks/{task_id}
```

**Response:** `200 OK`

#### Update Task

```
PUT /api/tasks/{task_id}
Content-Type: application/json

{
  "title": "string (optional)",
  "description": "string (optional)",
  "assigned_to": "string (optional)",
  "status": "string (optional)",
  "priority": "low|medium|high|urgent (optional)"
}
```

**Response:** `200 OK`

#### Move Task

```
PUT /api/tasks/{task_id}/move
Content-Type: application/json

{
  "column_id": "uuid (required)",
  "order": 1.5 (required),
  "version": 1 (required)
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "column_id": "uuid",
  "order": 1.5,
  "version": 2,
  ...
}
```

**Errors:**
- `404 Not Found` - Task or column not found
- `409 Conflict` - Version mismatch
  ```json
  {
    "detail": {
      "error": "VERSION_CONFLICT",
      "message": "Task was modified by another user",
      "server_version": 3,
      "client_version": 2
    }
  }
  ```

#### Delete Task

```
DELETE /api/tasks/{task_id}
```

**Response:** `204 No Content`

### 5.5 WebSocket

```
WS /ws/board/{board_id}
```

**Connection:** Upgrade to WebSocket

**Events (Server → Client):**

```json
// Task created
{
  "type": "task_created",
  "data": { /* TaskResponse */ }
}

// Task updated
{
  "type": "task_updated",
  "data": { /* TaskResponse */ }
}

// Task moved
{
  "type": "task_moved",
  "data": { /* TaskResponse */ }
}

// Task deleted
{
  "type": "task_deleted",
  "data": { "id": "uuid" }
}

// Column created
{
  "type": "column_created",
  "data": { /* ColumnResponse */ }
}

// Column updated
{
  "type": "column_updated",
  "data": { /* ColumnResponse */ }
}

// Column deleted
{
  "type": "column_deleted",
  "data": { "id": "uuid" }
}
```

---

## 6. Service Layer

### 6.1 HybridOrchestrator (Agent Service)

The `HybridOrchestrator` is the core service for AI agent execution, combining:
- **Direct Anthropic API** for planning and review phases
- **Claude Agent SDK** for autonomous development
- **Text Editor Tool** for targeted code modifications

```python
# app/services/hybrid_orchestrator.py

class HybridOrchestrator:
    """Hybrid agent orchestration service"""

    async def execute_workflow(self, task_id: str, description: str, workspace: str):
        """Execute full architect → developer → reviewer workflow"""

    async def _api_call(self, role: str, system_prompt: str, prompt: str) -> str:
        """Direct Anthropic API call for planning/review"""

    async def _cli_execute(self, task_id: str, workspace: str, prompt: str, role: str):
        """Claude Agent SDK for autonomous file operations"""

    async def _apply_review_fixes(self, task_id: str, workspace: str, review: str):
        """Text Editor Tool for targeted fixes"""

    async def _emit_activity(self, task_id: str, activity_type: str, data: dict):
        """Emit activity to Redis pub/sub for real-time updates"""
```

### 6.2 BoardService

```python
# app/services/board_service.py

class BoardService:
    # Board operations
    @staticmethod
    async def get_boards(db: AsyncSession) -> List[Board]:
        """Get all boards ordered by creation date"""
    
    @staticmethod
    async def get_board(db: AsyncSession, board_id: UUID) -> Optional[Board]:
        """Get board with columns and tasks eagerly loaded"""
    
    @staticmethod
    async def create_board(db: AsyncSession, board_data: BoardCreate) -> Board:
        """Create a new board"""
    
    @staticmethod
    async def update_board(db: AsyncSession, board_id: UUID, board_data: BoardUpdate) -> Optional[Board]:
        """Update an existing board"""
    
    @staticmethod
    async def delete_board(db: AsyncSession, board_id: UUID) -> bool:
        """Delete a board and all its columns/tasks"""
    
    # Column operations
    @staticmethod
    async def create_column(db: AsyncSession, board_id: UUID, column_data: ColumnCreate) -> Optional[Column]:
        """Create a new column at the end of the board"""
    
    @staticmethod
    async def update_column(db: AsyncSession, column_id: UUID, column_data: ColumnUpdate) -> Optional[Column]:
        """Update an existing column"""
    
    @staticmethod
    async def delete_column(db: AsyncSession, column_id: UUID) -> bool:
        """Delete a column and all its tasks"""
    
    # Task operations
    @staticmethod
    async def create_task(db: AsyncSession, board_id: UUID, task_data: TaskCreate) -> Optional[Task]:
        """Create a new task at the bottom of the column"""
    
    @staticmethod
    async def get_task(db: AsyncSession, task_id: UUID) -> Optional[Task]:
        """Get a task by ID"""
    
    @staticmethod
    async def update_task(db: AsyncSession, task_id: UUID, task_data: TaskUpdate) -> Optional[Task]:
        """Update an existing task"""
    
    @staticmethod
    async def move_task(db: AsyncSession, task_id: UUID, move_data: TaskMove) -> Optional[Task]:
        """Move a task to a new column/position with optimistic locking"""
    
    @staticmethod
    async def delete_task(db: AsyncSession, task_id: UUID) -> bool:
        """Delete a task"""
```

### 6.2 Fractional Ordering

Tasks and columns use fractional ordering for efficient reordering:

```python
def calculate_order(prev_order: Optional[float], next_order: Optional[float]) -> float:
    """Calculate order value between two items"""
    if prev_order is None and next_order is None:
        return 1.0
    elif prev_order is None:
        return next_order - 1.0
    elif next_order is None:
        return prev_order + 1.0
    else:
        return (prev_order + next_order) / 2.0
```

### 6.3 Optimistic Locking

```python
async def move_task(db: AsyncSession, task_id: UUID, move_data: TaskMove) -> Optional[Task]:
    task = await db.get(Task, task_id)
    if not task:
        return None
    
    # Check version
    if task.version != move_data.version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "VERSION_CONFLICT",
                "message": "Task was modified by another user",
                "server_version": task.version,
                "client_version": move_data.version
            }
        )
    
    # Update task
    task.column_id = move_data.column_id
    task.order = move_data.order
    task.version += 1  # Increment version
    
    await db.commit()
    return task
```

---

## 7. WebSocket Manager

### 7.1 Connection Manager

```python
# app/api/websocket.py

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, board_id: str):
        await websocket.accept()
        if board_id not in self.active_connections:
            self.active_connections[board_id] = []
        self.active_connections[board_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, board_id: str):
        if board_id in self.active_connections:
            self.active_connections[board_id].remove(websocket)
    
    async def broadcast(self, board_id: str, message: dict):
        if board_id in self.active_connections:
            for connection in self.active_connections[board_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass  # Handle disconnected clients

manager = ConnectionManager()
```

### 7.2 Broadcasting Updates

After each database operation, broadcast the change:

```python
# In endpoint
task = await BoardService.create_task(db, board_id, task_data)
await manager.broadcast(
    str(board_id),
    {"type": "task_created", "data": TaskResponse.from_orm(task).dict()}
)
```

---

## 8. Error Handling

### 8.1 HTTP Exceptions

```python
from fastapi import HTTPException, status

# Not Found
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail=f"Board {board_id} not found"
)

# Validation Error (automatic from Pydantic)

# Conflict
raise HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail={
        "error": "VERSION_CONFLICT",
        "message": "Resource was modified"
    }
)
```

### 8.2 Error Response Format

```json
{
  "detail": "string | object"
}
```

---

## 9. Database Connection

### 9.1 Configuration

```python
# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
```

---

## 10. Migrations

### 10.1 Create Migration

```bash
docker exec agent-rangers-backend alembic revision --autogenerate -m "description"
```

### 10.2 Run Migrations

```bash
docker exec agent-rangers-backend alembic upgrade head
```

### 10.3 Rollback

```bash
docker exec agent-rangers-backend alembic downgrade -1
```

---

*Document Owner: Agent Rangers Team*  
*Review Cycle: Each schema change*
