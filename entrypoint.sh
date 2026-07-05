#!/bin/bash
set -e

echo "Waiting for PostgreSQL to be ready..."
until python -c "import socket; socket.create_connection(('postgres', 5432))" 2>/dev/null; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting Uvicorn server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
