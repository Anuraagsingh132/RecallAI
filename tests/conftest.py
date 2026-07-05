import os
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/recallai_test")
os.environ["QDRANT_URL"] = "http://localhost:6333"
os.environ["ENV"] = "testing"

import pytest
import pytest_asyncio
import alembic.config
import alembic.command
from fastapi.testclient import TestClient
from main import app
from core.database import engine
from sqlmodel import SQLModel

import subprocess
import asyncio
from sqlalchemy import text

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database_schema():
    """Create the schema once per test session using Alembic."""
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE;"))
        await conn.execute(text("CREATE SCHEMA public;"))
        
    import subprocess
    result = subprocess.run(["alembic", "upgrade", "head"], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Alembic migration failed: {result.stderr}")
    yield

@pytest_asyncio.fixture(scope="function", autouse=True)
async def clear_tables():
    """Truncate all tables before every test to ensure test isolation."""
    async with engine.begin() as conn:
        result = await conn.execute(text("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' AND tablename != 'alembic_version';
        """))
        tables = [row[0] for row in result]
        if tables:
            quoted_tables = [f'"{table}"' for table in tables]
            await conn.execute(text(f"TRUNCATE TABLE {', '.join(quoted_tables)} CASCADE;"))
    yield

@pytest.fixture
def client():
    return TestClient(app)
