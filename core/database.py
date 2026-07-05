import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import event
from core.config import settings

from sqlalchemy.pool import NullPool

# Default to Postgres
DATABASE_URL = settings.DATABASE_URL

engine = create_async_engine(
    DATABASE_URL,
    echo=False
)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
