# Deployment Guide

## Quick Start with Docker Compose

The easiest way to run the entire stack:

```bash
# From project root
docker compose up -d

# Check logs
docker compose logs -f backend

# Stop services
docker compose down
```

This starts:
- PostgreSQL 16 on port 5432
- Redis 7 on port 6379
- Backend API on port 8000

## Local Development Setup

### Prerequisites

- Python 3.12+
- PostgreSQL 16
- Redis 7
- Docker and Docker Compose (recommended)

### Step-by-Step Setup

1. **Clone and navigate to backend directory**

```bash
cd /path/to/agent-rangers/backend
```

2. **Create virtual environment**

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set up environment variables**

```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Start PostgreSQL and Redis** (if not using Docker Compose)

```bash
# Using Docker Compose for databases only
docker compose up -d postgres redis

# Or install and run locally
# PostgreSQL: sudo systemctl start postgresql
# Redis: sudo systemctl start redis
```

6. **Run database migrations**

```bash
alembic upgrade head
```

7. **Start the development server**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

8. **Verify installation**

Visit http://localhost:8000/health or http://localhost:8000/docs

## Production Deployment

### Environment Configuration

Create a production `.env` file:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@db-host:5432/agent_rangers

# Redis
REDIS_URL=redis://redis-host:6379

# CORS (add your frontend domain)
CORS_ORIGINS=https://your-frontend-domain.com

# API Settings
API_V1_PREFIX=/api
PROJECT_NAME=Agent Rangers API
DEBUG=False
```

### Using Docker

1. **Build the image**

```bash
docker build -t agent-rangers-backend:latest .
```

2. **Run the container**

```bash
docker run -d \
  --name agent-rangers-backend \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/db" \
  -e REDIS_URL="redis://redis-host:6379" \
  -e CORS_ORIGINS="https://your-domain.com" \
  -e DEBUG=False \
  agent-rangers-backend:latest
```

3. **With Docker Compose** (recommended for production)

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: always

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      REDIS_URL: redis://redis:6379
      CORS_ORIGINS: ${CORS_ORIGINS}
      DEBUG: "False"
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    restart: always
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

volumes:
  postgres_data:
  redis_data:
```

Run with:

```bash
docker compose -f docker-compose.prod.yml up -d
```

### Cloud Deployment Options

#### AWS (ECS + RDS + ElastiCache)

1. **Database**: Use RDS for PostgreSQL 16
2. **Cache**: Use ElastiCache for Redis
3. **Compute**: Deploy on ECS Fargate or EC2
4. **Load Balancer**: Application Load Balancer
5. **Secrets**: AWS Secrets Manager

#### Google Cloud Platform

1. **Database**: Cloud SQL for PostgreSQL
2. **Cache**: Memorystore for Redis
3. **Compute**: Cloud Run or GKE
4. **Load Balancer**: Cloud Load Balancing
5. **Secrets**: Secret Manager

#### Azure

1. **Database**: Azure Database for PostgreSQL
2. **Cache**: Azure Cache for Redis
3. **Compute**: Azure Container Instances or AKS
4. **Load Balancer**: Azure Load Balancer
5. **Secrets**: Azure Key Vault

### Scaling Considerations

#### Horizontal Scaling

The backend supports horizontal scaling via:

1. **Multiple instances**: Redis pub/sub ensures WebSocket messages reach all instances
2. **Load balancer**: Place behind nginx or cloud load balancer
3. **Connection pooling**: SQLAlchemy handles database connections efficiently

Example nginx configuration:

```nginx
upstream backend {
    least_conn;
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}

server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

#### Database Optimization

1. **Connection pooling**: Already configured in `database.py`
   - pool_size=10
   - max_overflow=20

2. **Indexes**: Already created on:
   - Foreign keys (board_id, column_id)
   - Order fields (for sorting)
   - Primary keys (UUID)

3. **Query optimization**:
   - Use `selectinload` for eager loading relationships
   - Avoid N+1 queries with proper joins

#### Redis Configuration

For production, configure Redis persistence:

```bash
# In redis.conf
save 900 1
save 300 10
save 60 10000
appendonly yes
```

Or use managed Redis service (ElastiCache, Cloud Memorystore, etc.)

### Monitoring and Logging

#### Application Logs

FastAPI logs to stdout by default. Configure log aggregation:

```bash
# Using Docker logs
docker compose logs -f backend

# Export to file
docker compose logs backend > app.log

# Integrate with logging service (Datadog, CloudWatch, etc.)
```

#### Health Checks

Configure container orchestration health checks:

```yaml
# Docker Compose
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

#### Metrics

Add Prometheus metrics endpoint (optional):

```bash
pip install prometheus-fastapi-instrumentator
```

```python
# In app/main.py
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

### Database Backups

#### PostgreSQL Backups

```bash
# Manual backup
docker compose exec postgres pg_dump -U agent_rangers agent_rangers > backup.sql

# Restore
docker compose exec -T postgres psql -U agent_rangers agent_rangers < backup.sql

# Automated backups (cron)
0 2 * * * docker compose exec postgres pg_dump -U agent_rangers agent_rangers | gzip > /backups/backup-$(date +\%Y\%m\%d).sql.gz
```

#### Redis Backups

Redis persistence is configured via:
- RDB snapshots (save points)
- AOF (append-only file)

Backup the `/data` volume regularly.

### Security Checklist

- [ ] Set `DEBUG=False` in production
- [ ] Use strong database passwords
- [ ] Enable SSL/TLS for PostgreSQL connections
- [ ] Use HTTPS for API endpoints
- [ ] Configure CORS_ORIGINS to specific domains
- [ ] Implement rate limiting (e.g., using slowapi)
- [ ] Set up firewall rules
- [ ] Use secrets manager for sensitive data
- [ ] Enable database connection encryption
- [ ] Regular security updates for dependencies
- [ ] Implement API authentication (JWT, OAuth2)
- [ ] Log and monitor security events

### Performance Tuning

#### Database

```python
# Adjust connection pool in database.py
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,        # Increase for high load
    max_overflow=40,     # Increase overflow
    pool_pre_ping=True,  # Verify connections
    pool_recycle=3600,   # Recycle connections hourly
)
```

#### Uvicorn Workers

```bash
# Multiple workers for production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Or use gunicorn with uvicorn workers
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

Workers = (2 × CPU cores) + 1

#### Redis Connection Pooling

Already configured via `redis.asyncio.from_url()` which includes connection pooling.

### Troubleshooting

#### Database Connection Issues

```bash
# Check PostgreSQL is accessible
docker compose exec postgres pg_isready -U agent_rangers

# Check connection from backend
docker compose exec backend python -c "from app.database import engine; import asyncio; asyncio.run(engine.dispose())"
```

#### Redis Connection Issues

```bash
# Check Redis connectivity
docker compose exec redis redis-cli ping

# Check from backend
docker compose exec backend python -c "import redis; r = redis.from_url('redis://redis:6379'); print(r.ping())"
```

#### WebSocket Issues

- Ensure load balancer supports WebSocket upgrades
- Check CORS configuration
- Verify Redis pub/sub is working
- Check firewall allows WebSocket connections

#### Migration Issues

```bash
# Check current migration version
alembic current

# Show pending migrations
alembic history

# Force migration to specific version
alembic upgrade <revision>

# Rollback if needed
alembic downgrade -1
```

### CI/CD Pipeline Example

GitHub Actions workflow (`.github/workflows/deploy.yml`):

```yaml
name: Deploy Backend

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: |
          cd backend
          docker build -t agent-rangers-backend:${{ github.sha }} .

      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push agent-rangers-backend:${{ github.sha }}

      - name: Deploy to production
        run: |
          # Deploy using your preferred method
          # (kubectl, AWS CLI, etc.)
```

### Rollback Strategy

If deployment fails:

1. **Container rollback**: Use previous image tag
2. **Database rollback**: `alembic downgrade -1`
3. **Code rollback**: Revert to previous Git commit

Keep previous 3-5 versions of images and database backups.

## Support

For issues and questions:
- GitHub Issues: https://github.com/your-org/agent-rangers
- Documentation: /docs
- API Docs: http://your-domain.com/docs
