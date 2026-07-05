import pytest
import pytest_asyncio
import asyncio
import uuid
from sqlmodel import select, SQLModel
from core.database import get_session, AsyncSessionLocal, engine
from models.base import User, ProcessingJob, Document
from core.transactions import scoped_transaction
from core.recovery import recover_zombie_jobs
from sqlalchemy.exc import IntegrityError

@pytest.mark.asyncio
async def test_concurrent_inserts():
    """Stress test WAL concurrency handles many simultaneous inserts."""
    async def insert_user():
        async with scoped_transaction() as session:
            user = User(username=f"user_{uuid.uuid4()}", hashed_password="pwd")
            session.add(user)
    
    tasks = [insert_user() for _ in range(20)]
    await asyncio.gather(*tasks)
    
    async with AsyncSessionLocal() as session:
        users = await session.execute(select(User))
        assert len(users.scalars().all()) == 20

@pytest.mark.asyncio
async def test_zombie_recovery():
    """Test background zombie job recovery works."""
    async with scoped_transaction() as session:
        user = User(username=f"user_{uuid.uuid4()}", hashed_password="pwd")
        session.add(user)
        doc = Document(user_id=user.id, filename="test.pdf")
        session.add(doc)
        await session.flush()
        
        job1 = ProcessingJob(document_id=doc.id, status="PROCESSING")
        job2 = ProcessingJob(document_id=doc.id, status="PROCESSING")
        job3 = ProcessingJob(document_id=doc.id, status="PENDING")
        session.add_all([job1, job2, job3])

    recovered = await recover_zombie_jobs()
    assert recovered == 2
    
    async with AsyncSessionLocal() as session:
        jobs = await session.execute(select(ProcessingJob))
        for j in jobs.scalars().all():
            assert j.status == "PENDING"

@pytest.mark.asyncio
async def test_forced_rollback():
    """Test scoped_transaction strictly rolls back on exception."""
    try:
        async with scoped_transaction() as session:
            user = User(username=f"user_{uuid.uuid4()}", hashed_password="pwd")
            session.add(user)
            await session.flush()
            raise ValueError("Simulated crash")
    except ValueError:
        pass
    
    async with AsyncSessionLocal() as session:
        users = await session.execute(select(User))
        assert len(users.scalars().all()) == 0

@pytest.mark.asyncio
async def test_data_integrity_cascade():
    """Verify database foreign keys actually cascade deletions."""
    user_id = None
    async with scoped_transaction() as session:
        user = User(username=f"user_{uuid.uuid4()}", hashed_password="pwd")
        session.add(user)
        await session.flush()
        user_id = user.id
        doc = Document(user_id=user.id, filename="cascade.pdf")
        session.add(doc)
        await session.flush()
        job = ProcessingJob(document_id=doc.id)
        session.add(job)
        
    async with scoped_transaction() as session:
        u = await session.get(User, user_id)
        await session.delete(u)
        
    async with AsyncSessionLocal() as session:
        jobs = await session.execute(select(ProcessingJob))
        assert len(jobs.scalars().all()) == 0

@pytest.mark.asyncio
async def test_foreign_key_violation():
    """Verify that inserting a record with an invalid foreign key fails."""
    with pytest.raises(Exception):
        async with scoped_transaction() as session:
            # Document with a non-existent user_id
            doc = Document(user_id=uuid.uuid4(), filename="invalid.pdf")
            session.add(doc)
