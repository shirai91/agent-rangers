FROM python:3.12-slim

WORKDIR /app

# Install system dependencies including curl for NodeSource setup
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20.x LTS using NodeSource
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install claude-flow CLI globally
RUN npm install -g @claude-flow/cli@latest

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create a script to run migrations and start the app
RUN echo '#!/bin/bash\n\
set -e\n\
echo "Waiting for PostgreSQL..."\n\
while ! pg_isready -h ${DATABASE_URL#*@} -U agent_rangers; do\n\
  sleep 1\n\
done\n\
echo "Running Alembic migrations..."\n\
alembic upgrade head\n\
echo "Starting FastAPI application..."\n\
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload' > /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh

EXPOSE 8000

CMD ["/app/entrypoint.sh"]
