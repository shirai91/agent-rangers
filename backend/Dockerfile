FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

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
