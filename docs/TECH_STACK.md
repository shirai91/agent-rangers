# TECH_STACK.md - Technology Stack Specification
## Agent Rangers: Exact Versions and Dependencies

**Version:** 2.0
**Last Updated:** 2026-02-04

---

## 1. Overview

| Layer | Technology | Version |
|-------|------------|---------|
| Frontend | React + Vite + TypeScript | React 18.2.0, Vite 5.0.11 |
| Backend | FastAPI + Python | FastAPI 0.115.0, Python 3.12 |
| Database | PostgreSQL | 16.x |
| Cache/PubSub | Redis | 7.x |
| Containerization | Docker + Docker Compose | Latest |

---

## 2. Frontend Stack

### 2.1 Core Framework

| Package | Version | Purpose |
|---------|---------|---------|
| `react` | ^18.2.0 | UI library |
| `react-dom` | ^18.2.0 | React DOM renderer |
| `react-router-dom` | ^6.22.0 | Client-side routing |
| `typescript` | ^5.3.3 | Type safety |
| `vite` | ^5.0.11 | Build tool and dev server |

### 2.2 State Management

| Package | Version | Purpose |
|---------|---------|---------|
| `zustand` | ^4.5.0 | Global state management |

### 2.3 Drag and Drop

| Package | Version | Purpose |
|---------|---------|---------|
| `@dnd-kit/core` | ^6.1.0 | DnD foundation |
| `@dnd-kit/sortable` | ^8.0.0 | Sortable lists |
| `@dnd-kit/utilities` | ^3.2.2 | DnD utilities |

### 2.4 Styling

| Package | Version | Purpose |
|---------|---------|---------|
| `tailwindcss` | ^3.4.0 | Utility-first CSS |
| `autoprefixer` | ^10.4.17 | CSS vendor prefixes |
| `postcss` | ^8.4.33 | CSS processing |
| `clsx` | ^2.1.0 | Conditional classes |
| `tailwind-merge` | ^2.2.0 | Merge Tailwind classes |
| `class-variance-authority` | ^0.7.0 | Component variants |

### 2.5 UI Components

| Package | Version | Purpose |
|---------|---------|---------|
| `lucide-react` | ^0.316.0 | Icons |
| `@radix-ui/react-slot` | (via shadcn) | Composition primitive |
| `@radix-ui/react-dialog` | (via shadcn) | Modal dialogs |
| `@radix-ui/react-dropdown-menu` | (via shadcn) | Dropdown menus |
| `@radix-ui/react-label` | (via shadcn) | Form labels |

### 2.6 Development Tools

| Package | Version | Purpose |
|---------|---------|---------|
| `@types/react` | ^18.2.0 | React type definitions |
| `@types/react-dom` | ^18.2.0 | React DOM types |
| `@vitejs/plugin-react` | ^4.2.1 | Vite React plugin |
| `eslint` | ^8.56.0 | Linting |
| `@typescript-eslint/eslint-plugin` | ^6.19.0 | TS ESLint rules |
| `@typescript-eslint/parser` | ^6.19.0 | TS ESLint parser |
| `eslint-plugin-react-hooks` | ^4.6.0 | React Hooks linting |
| `eslint-plugin-react-refresh` | ^0.4.5 | Fast refresh linting |

### 2.7 Frontend package.json

```json
{
  "name": "agent-rangers-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.22.0",
    "zustand": "^4.5.0",
    "@dnd-kit/core": "^6.1.0",
    "@dnd-kit/sortable": "^8.0.0",
    "@dnd-kit/utilities": "^3.2.2",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.2.0",
    "lucide-react": "^0.316.0",
    "class-variance-authority": "^0.7.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@typescript-eslint/eslint-plugin": "^6.19.0",
    "@typescript-eslint/parser": "^6.19.0",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.17",
    "eslint": "^8.56.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.5",
    "postcss": "^8.4.33",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.3.3",
    "vite": "^5.0.11"
  }
}
```

---

## 3. Backend Stack

### 3.1 Core Framework

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | 0.115.0 | Web framework |
| `uvicorn[standard]` | 0.30.6 | ASGI server |
| `python-multipart` | 0.0.9 | Form data parsing |
| `pydantic` | 2.9.1 | Data validation |
| `pydantic-settings` | 2.5.2 | Settings management |

### 3.2 Database

| Package | Version | Purpose |
|---------|---------|---------|
| `sqlalchemy` | 2.0.32 | ORM (async mode) |
| `asyncpg` | 0.29.0 | PostgreSQL async driver |
| `alembic` | 1.13.2 | Database migrations |
| `psycopg2-binary` | 2.9.9 | PostgreSQL driver (sync) |

### 3.3 Cache & PubSub

| Package | Version | Purpose |
|---------|---------|---------|
| `redis` | 5.0.8 | Redis client |
| `hiredis` | 2.3.2 | Redis parser (faster) |

### 3.4 WebSocket

| Package | Version | Purpose |
|---------|---------|---------|
| `websockets` | 12.0 | WebSocket support |

### 3.5 Security

| Package | Version | Purpose |
|---------|---------|---------|
| `python-jose[cryptography]` | 3.3.0 | JWT handling |
| `passlib[bcrypt]` | 1.7.4 | Password hashing |
| `python-dotenv` | 1.0.1 | Environment variables |

### 3.6 Utilities

| Package | Version | Purpose |
|---------|---------|---------|
| `orjson` | 3.10.7 | Fast JSON serialization |
| `python-dateutil` | 2.9.0 | Date utilities |

### 3.7 Backend requirements.txt

```txt
# FastAPI and ASGI server
fastapi==0.115.0
uvicorn[standard]==0.30.6
python-multipart==0.0.9

# Database and ORM
sqlalchemy==2.0.32
asyncpg==0.29.0
alembic==1.13.2
psycopg2-binary==2.9.9

# Redis for pub/sub and caching
redis==5.0.8
hiredis==2.3.2

# Pydantic for validation
pydantic==2.9.1
pydantic-settings==2.5.2

# WebSocket support
websockets==12.0

# CORS and security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.1

# JSON handling
orjson==3.10.7

# Utilities
python-dateutil==2.9.0
```

---

## 4. Infrastructure

### 4.1 Docker Images

| Service | Image | Version |
|---------|-------|---------|
| PostgreSQL | `postgres` | 16-alpine |
| Redis | `redis` | 7-alpine |
| Backend | Custom | Python 3.12-slim |
| Frontend | Custom | Node 20-alpine |

### 4.2 docker-compose.yml

```yaml
version: '3.8'

services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: rangers
      POSTGRES_PASSWORD: rangers_dev
      POSTGRES_DB: agent_rangers
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U rangers -d agent_rangers"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://rangers:rangers_dev@db:5432/agent_rangers
      REDIS_URL: redis://redis:6379
      CORS_ORIGINS: http://localhost:5173,http://192.168.1.225:5173
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "5173:5173"
    environment:
      VITE_API_URL: http://192.168.1.225:8000
      VITE_WS_URL: ws://192.168.1.225:8000
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev -- --host

volumes:
  postgres_data:
```

---

## 5. Development Environment

### 5.1 System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Docker | 24.0+ | Latest |
| Docker Compose | 2.20+ | Latest |
| Node.js (local dev) | 20.x | 20.x LTS |
| Python (local dev) | 3.12+ | 3.12.x |
| RAM | 4GB | 8GB+ |
| Disk | 10GB | 20GB+ |

### 5.2 IDE Configuration

**VS Code Extensions:**
- ESLint
- Prettier
- Tailwind CSS IntelliSense
- Python
- Pylance
- Docker

**VS Code Settings:**
```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "typescript.preferences.importModuleSpecifier": "non-relative",
  "tailwindCSS.includeLanguages": {
    "typescript": "javascript",
    "typescriptreact": "javascript"
  }
}
```

---

## 6. AI Integration Dependencies

### 6.1 Core AI Packages

| Package | Version | Purpose |
|---------|---------|---------|
| `anthropic` | ^0.40.0 | Direct Anthropic API for planning/review |
| `claude-agent-sdk` | latest | CLI spawning for autonomous development |

### 6.2 Frontend Workflow

| Package | Version | Purpose |
|---------|---------|---------|
| `xstate` | ^5.x | State machine for workflow |
| `@xstate/react` | ^4.x | React XState bindings |

### 6.3 Knowledge Base (RAG) - Phase 4

| Package | Version | Purpose |
|---------|---------|---------|
| `pgvector` | (PostgreSQL extension) | Vector similarity search |
| `ollama` | (External) | Local embedding model |
| `nomic-embed-text` | (Ollama model) | Text embeddings |

---

## 7. API Endpoints Summary

### 7.1 Backend API (http://192.168.1.225:8000)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/boards` | List all boards |
| POST | `/api/boards` | Create board |
| GET | `/api/boards/{id}` | Get board with columns/tasks |
| PUT | `/api/boards/{id}` | Update board |
| DELETE | `/api/boards/{id}` | Delete board |
| POST | `/api/boards/{id}/columns` | Create column |
| PUT | `/api/columns/{id}` | Update column |
| DELETE | `/api/columns/{id}` | Delete column |
| POST | `/api/boards/{id}/tasks` | Create task |
| GET | `/api/tasks/{id}` | Get task |
| PUT | `/api/tasks/{id}` | Update task |
| PUT | `/api/tasks/{id}/move` | Move task |
| DELETE | `/api/tasks/{id}` | Delete task |

### 7.2 WebSocket (ws://192.168.1.225:8000)

| Endpoint | Description |
|----------|-------------|
| `/ws/board/{boardId}` | Real-time board updates |

---

## 8. Environment Variables

### 8.1 Backend (.env)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://rangers:rangers_dev@db:5432/agent_rangers

# Redis
REDIS_URL=redis://redis:6379

# CORS
CORS_ORIGINS=http://localhost:5173,http://192.168.1.225:5173

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

### 8.2 Frontend (.env)

```bash
# API Configuration
VITE_API_URL=http://192.168.1.225:8000
VITE_WS_URL=ws://192.168.1.225:8000
```

---

## 9. Version Pinning Policy

### 9.1 Pinning Rules

| Dependency Type | Pinning Strategy | Example |
|-----------------|------------------|---------|
| Framework (React, FastAPI) | Minor version | `^18.2.0` → allows 18.x.x |
| Database drivers | Exact | `2.0.32` → only this version |
| UI components | Minor version | `^0.316.0` → allows 0.x.x |
| Dev tools | Minor version | `^5.3.3` → allows 5.x.x |
| Security packages | Exact | `3.3.0` → only this version |

### 9.2 Update Schedule

- **Security patches**: Immediately
- **Bug fixes**: Weekly review
- **Minor versions**: Monthly review
- **Major versions**: Quarterly review with testing

---

## 10. Browser Support

| Browser | Minimum Version |
|---------|-----------------|
| Chrome | 90+ |
| Firefox | 90+ |
| Safari | 14+ |
| Edge | 90+ |

**Note:** IE11 is NOT supported.

---

*Document Owner: Agent Rangers Team*  
*Review Cycle: Each dependency update*
