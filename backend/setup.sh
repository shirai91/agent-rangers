#!/bin/bash

# Setup script for Agent Rangers Backend
set -e

echo "=========================================="
echo "Agent Rangers Backend Setup"
echo "=========================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

echo ""
echo "1. Creating .env file from example..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Created .env file"
else
    echo "⚠ .env file already exists, skipping"
fi

echo ""
echo "2. Starting services with Docker Compose..."
cd ..
docker compose up -d postgres redis
echo "✓ PostgreSQL and Redis started"

echo ""
echo "3. Waiting for PostgreSQL to be ready..."
sleep 5
until docker compose exec -T postgres pg_isready -U agent_rangers > /dev/null 2>&1; do
    echo "  Waiting for PostgreSQL..."
    sleep 2
done
echo "✓ PostgreSQL is ready"

echo ""
echo "4. Installing Python dependencies..."
cd backend
if [ -d "venv" ]; then
    echo "  Using existing virtual environment"
    source venv/bin/activate
else
    echo "  Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
fi

pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

echo ""
echo "5. Running database migrations..."
alembic upgrade head
echo "✓ Migrations complete"

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "To start the development server:"
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "Or use Docker Compose:"
echo "  docker compose up -d"
echo ""
echo "API will be available at:"
echo "  - http://localhost:8000"
echo "  - Docs: http://localhost:8000/docs"
echo "  - Health: http://localhost:8000/health"
echo ""
