from contextlib import asynccontextmanager
from core.database import AsyncSessionLocal
import structlog

logger = structlog.get_logger(__name__)

@asynccontextmanager
async def scoped_transaction():
    """
    Yields an AsyncSession mapped to an active transaction.
    Automatically commits on success, and rolls back on failure.
    DO NOT await external I/O or network calls inside this context.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            logger.error(f"Transaction failed, rolling back: {e}")
            await session.rollback()
            raise
