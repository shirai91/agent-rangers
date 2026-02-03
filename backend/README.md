# Agent Rangers Backend

FastAPI backend for Agent Rangers - AI Multi-Agent Kanban Framework.

## Features

- **FastAPI 0.115+** with async/await support
- **SQLAlchemy 2.0** with asyncpg for PostgreSQL
- **Alembic** for database migrations
- **Redis** pub/sub for real-time WebSocket broadcasting
- **Fractional ordering** for efficient drag-and-drop positioning
- **Optimistic locking** with version numbers for concurrent updates
- **WebSocket** real-time updates across multiple clients
- **CORS** support for frontend integration

## Project Structure

```
backend/
├── Dockerfile                  # Docker container configuration
├── requirements.txt            # Python dependencies
├── alembic.ini                # Alembic configuration
├── alembic/                   # Database migrations
│   ├── env.py                 # Alembic environment
│   └── versions/              # Migration scripts
│       └── 001_initial_schema.py
└── app/
    ├── __init__.py
    ├── main.py                # FastAPI application entry point
    ├── config.py              # Application configuration
    ├── database.py            # Database connection and session
    ├── models/                # SQLAlchemy models
    │   ├── __init__.py
    │   ├── board.py           # Board model
    │   ├── column.py          # Column model (workflow stages)
    │   └── task.py            # Task model
    ├── schemas/               # Pydantic schemas for validation
    │   ├── __init__.py
    │   ├── board.py
    │   ├── column.py
    │   └── task.py
    ├── api/                   # API endpoints
    │   ├── __init__.py
    │   ├── boards.py          # Board endpoints
    │   ├── columns.py         # Column endpoints
    │   ├── tasks.py           # Task endpoints
    │   └── websocket.py       # WebSocket endpoint
    └── services/              # Business logic
        ├── __init__.py
        └── board_service.py   # Board service layer
```

## Database Schema

### Tables

**boards**
- `id` (UUID, PK) - Board identifier
- `name` (VARCHAR) - Board name
- `description` (TEXT) - Board description
- `settings` (JSONB) - Board configuration
- `created_at` (TIMESTAMP) - Creation timestamp
- `updated_at` (TIMESTAMP) - Last update timestamp

**columns**
- `id` (UUID, PK) - Column identifier
- `board_id` (UUID, FK) - Reference to board
- `name` (VARCHAR) - Column name
- `order` (FLOAT) - Fractional ordering for drag-drop
- `color` (VARCHAR) - Hex color code
- `wip_limit` (INTEGER) - Work-in-progress limit
- `created_at` (TIMESTAMP) - Creation timestamp
- `updated_at` (TIMESTAMP) - Last update timestamp

**tasks**
- `id` (UUID, PK) - Task identifier
- `board_id` (UUID, FK) - Reference to board
- `column_id` (UUID, FK) - Reference to column (nullable)
- `title` (VARCHAR) - Task title
- `description` (TEXT) - Task description
- `order` (FLOAT) - Fractional ordering for drag-drop
- `priority` (INTEGER) - Priority level (0-4)
- `labels` (JSONB) - Array of label strings
- `version` (INTEGER) - Version for optimistic locking
- `created_at` (TIMESTAMP) - Creation timestamp
- `updated_at` (TIMESTAMP) - Last update timestamp

## API Endpoints

### Boards
- `GET /api/boards` - List all boards
- `POST /api/boards` - Create a new board
- `GET /api/boards/{board_id}` - Get board with columns
- `PUT /api/boards/{board_id}` - Update board
- `DELETE /api/boards/{board_id}` - Delete board
- `GET /api/boards/{board_id}/columns` - Get board columns
- `POST /api/boards/{board_id}/columns` - Create column
- `GET /api/boards/{board_id}/tasks` - Get board tasks
- `POST /api/boards/{board_id}/tasks` - Create task

### Columns
- `PUT /api/columns/{column_id}` - Update column
- `DELETE /api/columns/{column_id}` - Delete column

### Tasks
- `GET /api/tasks/{task_id}` - Get task
- `PUT /api/tasks/{task_id}` - Update task
- `PUT /api/tasks/{task_id}/move` - Move task to different column
- `DELETE /api/tasks/{task_id}` - Delete task

### WebSocket
- `WS /ws/boards/{board_id}` - Real-time board updates

## Environment Variables

Copy `.env.example` to `.env` and configure:

```env
DATABASE_URL=postgresql+asyncpg://agent_rangers:agent_rangers_dev@localhost:5432/agent_rangers
REDIS_URL=redis://localhost:6379
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
API_V1_PREFIX=/api
PROJECT_NAME=Agent Rangers API
DEBUG=True
```

## Development Setup

### Using Docker Compose (Recommended)

```bash
# Start all services (backend, PostgreSQL, Redis)
docker compose up -d

# View logs
docker compose logs -f backend

# Stop services
docker compose down
```

The backend will be available at `http://localhost:8000`

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run PostgreSQL and Redis
docker compose up -d postgres redis

# Run Alembic migrations
alembic upgrade head

# Start the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Database Migrations

### Create a new migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "description of changes"

# Create empty migration
alembic revision -m "description of changes"
```

### Apply migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade by one version
alembic upgrade +1

# Downgrade by one version
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

## WebSocket Usage

Connect to `ws://localhost:8000/ws/boards/{board_id}` to receive real-time updates.

### Message Format (Server → Client)

```json
{
  "type": "task_created|task_updated|task_moved|task_deleted|column_created|column_updated|column_deleted",
  "payload": {
    "task_id": "uuid",
    "column_id": "uuid",
    "data": {}
  }
}
```

### Ping/Pong

Send `"ping"` to keep connection alive, receive `"pong"` response.

## Fractional Ordering

Tasks and columns use fractional ordering for efficient drag-and-drop positioning:

- New items get order = max(existing_order) + 1000
- When moving between items, use order = (prev_order + next_order) / 2
- This allows O(1) reordering without updating all items

Example:
```
Initial: [1000, 2000, 3000]
Move item 3 between 1 and 2: [1000, 1500, 2000, 3000]
```

## Optimistic Locking

Tasks use version numbers to prevent concurrent update conflicts:

1. Client reads task with version=1
2. Client modifies task
3. Client sends update with version=1
4. Server checks: if current version != 1, return 409 Conflict
5. Server updates task and increments version to 2

## API Documentation

Interactive API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "service": "agent-rangers-api",
  "version": "0.1.0"
}
```

## Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```

## Production Deployment

1. Set `DEBUG=False` in environment variables
2. Use a production ASGI server (uvicorn with multiple workers)
3. Set up proper PostgreSQL connection pooling
4. Configure Redis for persistence if needed
5. Use environment-specific secrets management
6. Enable HTTPS/TLS
7. Set up monitoring and logging

Example production command:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 --log-level info
```

## Architecture Highlights

- **Async/await throughout**: All database operations and I/O are asynchronous
- **Connection pooling**: SQLAlchemy async engine with configurable pool size
- **Redis pub/sub**: Enables horizontal scaling with multiple backend instances
- **Dependency injection**: FastAPI's dependency system for clean service layer
- **Type safety**: Pydantic schemas for request/response validation
- **Database transactions**: Automatic rollback on errors via context managers

## License

MIT
