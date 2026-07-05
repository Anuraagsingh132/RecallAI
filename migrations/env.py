import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from sqlmodel import SQLModel
# Import all models to register them with SQLModel.metadata
from models.base import User, Session, Document, DocumentChunk, ProcessingJob, Conversation, Message
from core.database import DATABASE_URL

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the URL from our core settings
config.set_main_option("sqlalchemy.url", DATABASE_URL)

target_metadata = SQLModel.metadata

def do_run_migrations(connection):
    context.configure(
        connection=connection, 
        target_metadata=target_metadata
    )
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def run_migrations_online():
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    pass # Offline mode not used here
else:
    run_migrations_online()
