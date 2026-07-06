#!/usr/bin/env sh
# Container entrypoint: apply migrations, then start the API server.
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Ensuring default languages..."
python -m app.infrastructure.db.bootstrap

echo "Starting API server on port ${BACKEND_PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${BACKEND_PORT:-8000}"
