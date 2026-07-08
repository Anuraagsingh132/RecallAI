import asyncio
from sqlmodel import SQLModel
from core.database import engine
# Import all models to register them with SQLModel metadata
from models.base import User, Document, ProcessingJob, Conversation, Message, TokenBlocklist

async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(create_db_and_tables())
