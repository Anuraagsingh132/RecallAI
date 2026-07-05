#!/bin/bash
set -e

echo "Waiting for PostgreSQL to be ready..."
python -c "
import os, time, socket
from urllib.parse import urlparse
db_url = os.environ.get('DATABASE_URL', '')
if db_url:
    try:
        parsed = urlparse(db_url)
        host = parsed.hostname
        port = parsed.port or 5432
        while True:
            try:
                socket.create_connection((host, port), timeout=1)
                break
            except Exception:
                print('PostgreSQL is unavailable - sleeping')
                time.sleep(1)
    except Exception as e:
        print(f'Error parsing DATABASE_URL: {e}')
"

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting Uvicorn server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
