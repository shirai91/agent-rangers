# Quick Start Guide

Get Agent Rangers Backend up and running in 5 minutes.

## Prerequisites

- Docker and Docker Compose installed
- (Optional) Python 3.12+ for local development

## Option 1: Docker Compose (Recommended)

### Start Everything

```bash
# From project root
cd /home/shirai91/projects/personal/agent-rangers
docker compose up -d
```

This starts:
- PostgreSQL on port 5432
- Redis on port 6379
- Backend API on port 8000

### Verify It's Working

```bash
# Check health
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","service":"agent-rangers-api","version":"0.1.0"}

# View API docs
open http://localhost:8000/docs  # or visit in browser
```

### View Logs

```bash
docker compose logs -f backend
```

### Stop Services

```bash
docker compose down
```

## Option 2: Local Development

### 1. Setup Script (Linux/Mac)

```bash
cd backend
chmod +x setup.sh
./setup.sh
```

This will:
- Create .env file
- Start PostgreSQL and Redis with Docker
- Create Python virtual environment
- Install dependencies
- Run database migrations

### 2. Start Development Server

```bash
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Test the API

### Using the Test Script

```bash
# Make sure API is running first
cd backend
python test_api.py
```

This runs a complete test suite that:
1. Creates a board
2. Creates columns (Backlog, In Progress, Done)
3. Creates tasks
4. Updates tasks
5. Moves tasks between columns
6. Tests optimistic locking
7. Deletes resources

### Manual Testing with cURL

```bash
# Create a board
curl -X POST http://localhost:8000/api/boards \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Board","description":"My first board"}'

# Get all boards
curl http://localhost:8000/api/boards

# Create a column (use board_id from above)
curl -X POST http://localhost:8000/api/boards/YOUR_BOARD_ID/columns \
  -H "Content-Type: application/json" \
  -d '{"name":"Todo","color":"#6366f1"}'

# Create a task (use board_id and column_id from above)
curl -X POST http://localhost:8000/api/boards/YOUR_BOARD_ID/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"My First Task","column_id":"YOUR_COLUMN_ID","priority":2,"labels":["test"]}'
```

## WebSocket Testing

### Using wscat

```bash
# Install wscat
npm install -g wscat

# Connect to WebSocket (use your board_id)
wscat -c ws://localhost:8000/ws/boards/YOUR_BOARD_ID

# You'll receive:
# {"type":"connected","payload":{"board_id":"YOUR_BOARD_ID"}}

# Send ping to test
# > ping
# < pong
```

### Using JavaScript

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/boards/YOUR_BOARD_ID');

ws.onopen = () => console.log('Connected');
ws.onmessage = (event) => console.log('Received:', JSON.parse(event.data));

// Send ping
ws.send('ping');
```

## Common Commands

### Using Make

```bash
# Show all available commands
make help

# Start with Docker
make docker-up

# View logs
make docker-logs

# Run tests
make test

# Database migrations
make migrate

# Stop services
make docker-down
```

### Database Access

```bash
# PostgreSQL shell
docker compose exec postgres psql -U agent_rangers -d agent_rangers

# Redis CLI
docker compose exec redis redis-cli
```

## Project Structure Overview

```
backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── database.py          # Database connection
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── api/                 # API endpoints
│   └── services/            # Business logic
├── alembic/                 # Database migrations
├── Dockerfile               # Docker configuration
├── requirements.txt         # Python dependencies
└── test_api.py             # API test suite
```

## Next Steps

1. **Explore API Documentation**: Visit http://localhost:8000/docs for interactive API docs

2. **Read Full Documentation**:
   - `README.md` - Complete feature documentation
   - `API_REFERENCE.md` - Detailed API reference
   - `DEPLOYMENT.md` - Production deployment guide

3. **Frontend Integration**: Connect your frontend to:
   - REST API: `http://localhost:8000/api`
   - WebSocket: `ws://localhost:8000/ws/boards/{board_id}`

4. **Database**:
   - View with any PostgreSQL client at `postgresql://agent_rangers:agent_rangers_dev@localhost:5432/agent_rangers`
   - Modify schema in `app/models/`
   - Create migrations: `alembic revision --autogenerate -m "description"`

## Troubleshooting

### Port Already in Use

```bash
# Check what's using port 8000
lsof -i :8000

# Use different port
uvicorn app.main:app --reload --port 8001
```

### Database Connection Failed

```bash
# Check PostgreSQL is running
docker compose ps

# Restart PostgreSQL
docker compose restart postgres

# Check logs
docker compose logs postgres
```

### Migration Failed

```bash
# Check current migration version
alembic current

# Reset database (development only!)
docker compose down -v  # Removes volumes
docker compose up -d
alembic upgrade head
```

### Redis Connection Failed

```bash
# Check Redis is running
docker compose exec redis redis-cli ping

# Should return: PONG
```

## Environment Variables

Key environment variables in `.env`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://agent_rangers:agent_rangers_dev@localhost:5432/agent_rangers

# Redis
REDIS_URL=redis://localhost:6379

# CORS (add your frontend URL)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Debug mode
DEBUG=True
```

## API Key Concepts

### Fractional Ordering

Tasks and columns use floating-point numbers for ordering:
- Easy drag-and-drop: just calculate midpoint between neighbors
- No need to update all items when reordering
- Example: Moving item between 1000 and 2000 → set order to 1500

### Optimistic Locking

Tasks have a `version` field:
- Increments on each update
- Prevents concurrent update conflicts
- Client must send current version with updates
- Returns 409 Conflict if versions don't match

### WebSocket Broadcasting

Real-time updates use Redis pub/sub:
- Supports multiple backend instances
- All clients on a board receive updates
- Events: task_created, task_updated, task_moved, task_deleted, column events

## Performance Tips

1. **Connection Pooling**: Already configured (pool_size=10, max_overflow=20)
2. **Eager Loading**: Relationships use `selectinload` to avoid N+1 queries
3. **Indexes**: Database has indexes on foreign keys and order fields
4. **Async**: All database operations are asynchronous

## Support

- **Documentation**: See README.md, API_REFERENCE.md, DEPLOYMENT.md
- **Interactive API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Issues**: GitHub issues (if applicable)

## What's Next?

Check out the full feature set in `README.md` including:
- Advanced query patterns
- Authentication (coming soon)
- Rate limiting (coming soon)
- Metrics and monitoring
- Production deployment strategies
