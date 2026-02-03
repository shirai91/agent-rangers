.PHONY: help install dev test clean migrate docker-up docker-down docker-logs format lint

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

dev: ## Run development server
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test: ## Run tests
	python test_api.py

clean: ## Clean up Python cache files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

migrate: ## Run database migrations
	alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MSG="description")
	alembic revision --autogenerate -m "$(MSG)"

migrate-down: ## Rollback one migration
	alembic downgrade -1

migrate-history: ## Show migration history
	alembic history

migrate-current: ## Show current migration
	alembic current

docker-up: ## Start all services with Docker Compose
	cd .. && docker compose up -d

docker-down: ## Stop all services
	cd .. && docker compose down

docker-logs: ## Show Docker Compose logs
	cd .. && docker compose logs -f backend

docker-build: ## Rebuild Docker images
	cd .. && docker compose build backend

docker-restart: ## Restart backend service
	cd .. && docker compose restart backend

format: ## Format code with black (install: pip install black)
	black app/ alembic/

lint: ## Lint code with ruff (install: pip install ruff)
	ruff check app/ alembic/

check: clean lint ## Clean and lint code

db-shell: ## Open PostgreSQL shell
	docker compose exec postgres psql -U agent_rangers -d agent_rangers

redis-cli: ## Open Redis CLI
	docker compose exec redis redis-cli

logs-backend: ## Show backend logs
	docker compose logs -f backend

logs-db: ## Show PostgreSQL logs
	docker compose logs -f postgres

logs-redis: ## Show Redis logs
	docker compose logs -f redis

shell: ## Open Python shell with app context
	python -c "from app.database import *; from app.models import *; import asyncio; asyncio.run(init_db())"

env: ## Create .env file from example
	cp .env.example .env
	@echo "Created .env file. Please update with your settings."
