# API Reference

Complete API documentation for Agent Rangers Backend.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently no authentication is required. In future versions, JWT or OAuth2 authentication will be implemented.

## Common Response Codes

- `200 OK` - Request succeeded
- `201 Created` - Resource created successfully
- `204 No Content` - Resource deleted successfully
- `400 Bad Request` - Invalid request data
- `404 Not Found` - Resource not found
- `409 Conflict` - Version conflict (optimistic locking)
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

## Health & Info

### Health Check

```http
GET /health
```

**Response 200:**
```json
{
  "status": "healthy",
  "service": "agent-rangers-api",
  "version": "0.1.0"
}
```

### Root Info

```http
GET /
```

**Response 200:**
```json
{
  "service": "Agent Rangers API",
  "version": "0.1.0",
  "description": "FastAPI backend for AI Multi-Agent Kanban Framework",
  "docs": "/docs",
  "health": "/health"
}
```

## Boards

### List All Boards

```http
GET /api/boards
```

**Response 200:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "My Board",
    "description": "Board description",
    "settings": {"theme": "dark"},
    "created_at": "2026-02-03T15:00:00Z",
    "updated_at": "2026-02-03T15:00:00Z"
  }
]
```

### Get Board

```http
GET /api/boards/{board_id}
```

**Parameters:**
- `board_id` (path, UUID) - Board identifier

**Response 200:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "My Board",
  "description": "Board description",
  "settings": {"theme": "dark"},
  "created_at": "2026-02-03T15:00:00Z",
  "updated_at": "2026-02-03T15:00:00Z",
  "columns": [
    {
      "id": "650e8400-e29b-41d4-a716-446655440001",
      "board_id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Backlog",
      "order": 1000.0,
      "color": "#6366f1",
      "wip_limit": null,
      "created_at": "2026-02-03T15:00:00Z",
      "updated_at": "2026-02-03T15:00:00Z"
    }
  ]
}
```

**Response 404:**
```json
{
  "detail": "Board 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

### Create Board

```http
POST /api/boards
```

**Request Body:**
```json
{
  "name": "New Board",
  "description": "Optional description",
  "settings": {"theme": "light"}
}
```

**Response 201:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "New Board",
  "description": "Optional description",
  "settings": {"theme": "light"},
  "created_at": "2026-02-03T15:00:00Z",
  "updated_at": "2026-02-03T15:00:00Z",
  "columns": []
}
```

### Update Board

```http
PUT /api/boards/{board_id}
```

**Parameters:**
- `board_id` (path, UUID) - Board identifier

**Request Body (all fields optional):**
```json
{
  "name": "Updated Board Name",
  "description": "Updated description",
  "settings": {"theme": "dark", "showLabels": true}
}
```

**Response 200:** Same as Create Board

### Delete Board

```http
DELETE /api/boards/{board_id}
```

**Parameters:**
- `board_id` (path, UUID) - Board identifier

**Response 204:** No content

## Columns

### Get Board Columns

```http
GET /api/boards/{board_id}/columns
```

**Parameters:**
- `board_id` (path, UUID) - Board identifier

**Response 200:**
```json
[
  {
    "id": "650e8400-e29b-41d4-a716-446655440001",
    "board_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Backlog",
    "order": 1000.0,
    "color": "#6366f1",
    "wip_limit": 5,
    "created_at": "2026-02-03T15:00:00Z",
    "updated_at": "2026-02-03T15:00:00Z"
  },
  {
    "id": "650e8400-e29b-41d4-a716-446655440002",
    "board_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "In Progress",
    "order": 2000.0,
    "color": "#22c55e",
    "wip_limit": 3,
    "created_at": "2026-02-03T15:00:00Z",
    "updated_at": "2026-02-03T15:00:00Z"
  }
]
```

### Create Column

```http
POST /api/boards/{board_id}/columns
```

**Parameters:**
- `board_id` (path, UUID) - Board identifier

**Request Body:**
```json
{
  "name": "Done",
  "color": "#84cc16",
  "wip_limit": null,
  "order": 3000.0
}
```

**Note:** `order` is optional. If not provided, column is added at the end.

**Response 201:**
```json
{
  "id": "650e8400-e29b-41d4-a716-446655440003",
  "board_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Done",
  "order": 3000.0,
  "color": "#84cc16",
  "wip_limit": null,
  "created_at": "2026-02-03T15:00:00Z",
  "updated_at": "2026-02-03T15:00:00Z"
}
```

### Update Column

```http
PUT /api/columns/{column_id}
```

**Parameters:**
- `column_id` (path, UUID) - Column identifier

**Request Body (all fields optional):**
```json
{
  "name": "Updated Column",
  "order": 1500.0,
  "color": "#f59e0b",
  "wip_limit": 10
}
```

**Response 200:** Same as Create Column

### Delete Column

```http
DELETE /api/columns/{column_id}
```

**Parameters:**
- `column_id` (path, UUID) - Column identifier

**Response 204:** No content

**Note:** Tasks in this column will have their `column_id` set to NULL.

## Tasks

### Get Board Tasks

```http
GET /api/boards/{board_id}/tasks
```

**Parameters:**
- `board_id` (path, UUID) - Board identifier

**Response 200:**
```json
[
  {
    "id": "750e8400-e29b-41d4-a716-446655440001",
    "board_id": "550e8400-e29b-41d4-a716-446655440000",
    "column_id": "650e8400-e29b-41d4-a716-446655440001",
    "title": "Implement user authentication",
    "description": "Add JWT-based authentication",
    "order": 1000.0,
    "priority": 3,
    "labels": ["backend", "security"],
    "version": 1,
    "created_at": "2026-02-03T15:00:00Z",
    "updated_at": "2026-02-03T15:00:00Z"
  }
]
```

### Get Task

```http
GET /api/tasks/{task_id}
```

**Parameters:**
- `task_id` (path, UUID) - Task identifier

**Response 200:** Same as task object above

**Response 404:**
```json
{
  "detail": "Task 750e8400-e29b-41d4-a716-446655440001 not found"
}
```

### Create Task

```http
POST /api/boards/{board_id}/tasks
```

**Parameters:**
- `board_id` (path, UUID) - Board identifier

**Request Body:**
```json
{
  "title": "New Task",
  "description": "Task description",
  "column_id": "650e8400-e29b-41d4-a716-446655440001",
  "priority": 2,
  "labels": ["frontend", "ui"],
  "order": 2000.0
}
```

**Field Details:**
- `title` (required, string, max 500) - Task title
- `description` (optional, string) - Task description
- `column_id` (optional, UUID) - Column to place task in
- `priority` (optional, integer 0-4, default 0) - Priority level
  - 0: None
  - 1: Low
  - 2: Medium
  - 3: High
  - 4: Urgent
- `labels` (optional, array of strings) - Task labels
- `order` (optional, float) - Position in column (auto-calculated if omitted)

**Response 201:**
```json
{
  "id": "750e8400-e29b-41d4-a716-446655440002",
  "board_id": "550e8400-e29b-41d4-a716-446655440000",
  "column_id": "650e8400-e29b-41d4-a716-446655440001",
  "title": "New Task",
  "description": "Task description",
  "order": 2000.0,
  "priority": 2,
  "labels": ["frontend", "ui"],
  "version": 1,
  "created_at": "2026-02-03T15:00:00Z",
  "updated_at": "2026-02-03T15:00:00Z"
}
```

### Update Task

```http
PUT /api/tasks/{task_id}
```

**Parameters:**
- `task_id` (path, UUID) - Task identifier

**Request Body (all fields optional):**
```json
{
  "title": "Updated Task Title",
  "description": "Updated description",
  "priority": 4,
  "labels": ["backend", "database", "urgent"],
  "version": 1
}
```

**Note:** Include `version` for optimistic locking to prevent concurrent update conflicts.

**Response 200:**
```json
{
  "id": "750e8400-e29b-41d4-a716-446655440001",
  "board_id": "550e8400-e29b-41d4-a716-446655440000",
  "column_id": "650e8400-e29b-41d4-a716-446655440001",
  "title": "Updated Task Title",
  "description": "Updated description",
  "order": 1000.0,
  "priority": 4,
  "labels": ["backend", "database", "urgent"],
  "version": 2,
  "created_at": "2026-02-03T15:00:00Z",
  "updated_at": "2026-02-03T15:05:00Z"
}
```

**Response 409 (Version Conflict):**
```json
{
  "detail": {
    "error": "VERSION_CONFLICT",
    "message": "Task was modified by another user",
    "server_version": 2,
    "client_version": 1
  }
}
```

### Move Task

```http
PUT /api/tasks/{task_id}/move
```

**Parameters:**
- `task_id` (path, UUID) - Task identifier

**Request Body:**
```json
{
  "column_id": "650e8400-e29b-41d4-a716-446655440002",
  "order": 1500.0,
  "version": 2
}
```

**Field Details:**
- `column_id` (required, UUID) - Target column
- `order` (required, float) - New position in target column
- `version` (required, integer) - Current version for optimistic locking

**Response 200:** Same as task object with updated `column_id`, `order`, and `version`

**Response 409:** Same as Update Task version conflict

### Delete Task

```http
DELETE /api/tasks/{task_id}
```

**Parameters:**
- `task_id` (path, UUID) - Task identifier

**Response 204:** No content

## WebSocket

### Real-time Board Updates

```
WS /ws/boards/{board_id}
```

**Parameters:**
- `board_id` (path, UUID) - Board identifier

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/boards/550e8400-e29b-41d4-a716-446655440000');

ws.onopen = () => {
  console.log('Connected');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected');
};
```

**Initial Message (Server → Client):**
```json
{
  "type": "connected",
  "payload": {
    "board_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

**Event Types:**

### Task Events

**Task Created:**
```json
{
  "type": "task_created",
  "payload": {
    "task_id": "750e8400-e29b-41d4-a716-446655440001",
    "data": {
      "id": "750e8400-e29b-41d4-a716-446655440001",
      "board_id": "550e8400-e29b-41d4-a716-446655440000",
      "column_id": "650e8400-e29b-41d4-a716-446655440001",
      "title": "New Task",
      "description": "Task description",
      "order": 1000.0,
      "priority": 2,
      "labels": ["frontend"],
      "version": 1,
      "created_at": "2026-02-03T15:00:00Z",
      "updated_at": "2026-02-03T15:00:00Z"
    }
  }
}
```

**Task Updated:**
```json
{
  "type": "task_updated",
  "payload": {
    "task_id": "750e8400-e29b-41d4-a716-446655440001",
    "data": {
      "title": "Updated Task",
      "priority": 3,
      "version": 2
    }
  }
}
```

**Task Moved:**
```json
{
  "type": "task_moved",
  "payload": {
    "task_id": "750e8400-e29b-41d4-a716-446655440001",
    "from_column_id": "650e8400-e29b-41d4-a716-446655440001",
    "to_column_id": "650e8400-e29b-41d4-a716-446655440002",
    "order": 1500.0,
    "version": 3
  }
}
```

**Task Deleted:**
```json
{
  "type": "task_deleted",
  "payload": {
    "task_id": "750e8400-e29b-41d4-a716-446655440001"
  }
}
```

### Column Events

**Column Created:**
```json
{
  "type": "column_created",
  "payload": {
    "column_id": "650e8400-e29b-41d4-a716-446655440003",
    "data": {
      "id": "650e8400-e29b-41d4-a716-446655440003",
      "board_id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Review",
      "order": 2500.0,
      "color": "#f59e0b",
      "wip_limit": 3,
      "created_at": "2026-02-03T15:00:00Z",
      "updated_at": "2026-02-03T15:00:00Z"
    }
  }
}
```

**Column Updated:**
```json
{
  "type": "column_updated",
  "payload": {
    "column_id": "650e8400-e29b-41d4-a716-446655440001",
    "data": {
      "name": "Updated Backlog",
      "wip_limit": 10
    }
  }
}
```

**Column Deleted:**
```json
{
  "type": "column_deleted",
  "payload": {
    "column_id": "650e8400-e29b-41d4-a716-446655440001"
  }
}
```

### Keep-Alive (Client → Server)

Send ping to keep connection alive:

```javascript
ws.send('ping');
// Server responds with 'pong'
```

## Fractional Ordering Examples

Fractional ordering allows efficient drag-and-drop without updating all items.

### Initial State
```
Column: [Task A(1000), Task B(2000), Task C(3000)]
```

### Move Task C between A and B
```
New order = (1000 + 2000) / 2 = 1500
Result: [Task A(1000), Task C(1500), Task B(2000)]
```

### Move Task to End
```
New order = max(order) + 1000 = 3000 + 1000 = 4000
Result: [..., Task D(4000)]
```

### Move Task to Beginning
```
New order = min(order) / 2 = 1000 / 2 = 500
Result: [Task E(500), Task A(1000), ...]
```

## Error Handling

### Validation Error (422)

```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Internal Server Error (500)

```json
{
  "error": "Internal server error",
  "detail": "An unexpected error occurred"
}
```

In DEBUG mode, includes traceback:
```json
{
  "error": "Internal server error",
  "detail": "division by zero",
  "traceback": "Traceback (most recent call last):\n..."
}
```

## Rate Limiting

Currently no rate limiting is implemented. For production, consider:
- Using `slowapi` for rate limiting
- Implementing API key authentication
- Setting up nginx rate limiting

## OpenAPI Documentation

Interactive API documentation is available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Code Examples

### Python (httpx)

```python
import httpx
import asyncio

async def main():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Create board
        response = await client.post("/api/boards", json={
            "name": "My Board",
            "description": "Test board"
        })
        board = response.json()

        # Create column
        response = await client.post(f"/api/boards/{board['id']}/columns", json={
            "name": "Todo",
            "color": "#6366f1"
        })
        column = response.json()

        # Create task
        response = await client.post(f"/api/boards/{board['id']}/tasks", json={
            "title": "My Task",
            "column_id": column["id"],
            "priority": 2,
            "labels": ["test"]
        })
        task = response.json()
        print(f"Created task: {task['id']}")

asyncio.run(main())
```

### JavaScript (fetch)

```javascript
// Create board
const board = await fetch('http://localhost:8000/api/boards', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'My Board',
    description: 'Test board'
  })
}).then(r => r.json());

// Create column
const column = await fetch(`http://localhost:8000/api/boards/${board.id}/columns`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'Todo',
    color: '#6366f1'
  })
}).then(r => r.json());

// Create task
const task = await fetch(`http://localhost:8000/api/boards/${board.id}/tasks`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    title: 'My Task',
    column_id: column.id,
    priority: 2,
    labels: ['test']
  })
}).then(r => r.json());

console.log('Created task:', task.id);
```

### cURL

```bash
# Create board
curl -X POST http://localhost:8000/api/boards \
  -H "Content-Type: application/json" \
  -d '{"name":"My Board","description":"Test board"}'

# Create column
curl -X POST http://localhost:8000/api/boards/{board_id}/columns \
  -H "Content-Type: application/json" \
  -d '{"name":"Todo","color":"#6366f1"}'

# Create task
curl -X POST http://localhost:8000/api/boards/{board_id}/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"My Task","column_id":"{column_id}","priority":2,"labels":["test"]}'

# Get board with columns
curl http://localhost:8000/api/boards/{board_id}
```
