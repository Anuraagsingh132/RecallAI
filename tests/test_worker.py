import pytest
import asyncio
import uuid
from sqlmodel import select
from core.database import engine
from core.worker import get_next_pending_job, worker_loop, trigger_new_job, mark_job_failed, mark_job_pending
from models.base import ProcessingJob, Document, User
from core.transactions import scoped_transaction
from unittest.mock import patch
import pytest_asyncio
from sqlalchemy import text

# Removed setup_env

# Fixture removed to use conftest.py's global teardown

@pytest.mark.asyncio
async def test_atomic_claim_single():
    # Insert a job
    doc_id = uuid.uuid4()
    job_id = uuid.uuid4()
    u_id = uuid.uuid4()
    async with scoped_transaction() as session:
        user = User(id=u_id, username="test", hashed_password="test")
        doc = Document(id=doc_id, user_id=u_id, filename="test.pdf", original_filename="test.pdf", size_bytes=100)
        job = ProcessingJob(id=job_id, document_id=doc_id, status="PENDING")
        session.add(user)
        session.add(doc)
        session.add(job)
        
    claimed_doc_id, claimed_job_id = await get_next_pending_job()
    assert claimed_doc_id == doc_id
    assert claimed_job_id == job_id
    
    # Try claiming again
    second_doc_id, second_job_id = await get_next_pending_job()
    assert second_doc_id is None
    assert second_job_id is None
    
    # Verify DB state
    async with scoped_transaction() as session:
        result = await session.execute(select(ProcessingJob).where(ProcessingJob.id == job_id))
        db_job = result.scalar_one()
        assert db_job.status == "PROCESSING"

@pytest.mark.asyncio
async def test_duplicate_claim_prevention():
    # Insert a job
    doc_id = uuid.uuid4()
    job_id = uuid.uuid4()
    u_id = uuid.uuid4()
    async with scoped_transaction() as session:
        user = User(id=u_id, username="test2", hashed_password="test")
        doc = Document(id=doc_id, user_id=u_id, filename="test.pdf", original_filename="test.pdf", size_bytes=100)
        job = ProcessingJob(id=job_id, document_id=doc_id, status="PENDING")
        session.add(user)
        session.add(doc)
        session.add(job)
        
    # Simulate two workers claiming concurrently
    claim1, claim2 = await asyncio.gather(
        get_next_pending_job(),
        get_next_pending_job()
    )
    
    # Only one should succeed
    claims_docs = [claim1[0], claim2[0]]
    assert doc_id in claims_docs
    assert None in claims_docs

@pytest.mark.asyncio
async def test_worker_loop_success():
    doc_id = uuid.uuid4()
    job_id = uuid.uuid4()
    u_id = uuid.uuid4()
    async with scoped_transaction() as session:
        user = User(id=u_id, username="test3", hashed_password="test")
        doc = Document(id=doc_id, user_id=u_id, filename="test.pdf", original_filename="test.pdf", size_bytes=100)
        session.add(user)
        session.add(doc)
        session.add(ProcessingJob(id=job_id, document_id=doc_id, status="PENDING"))
        
    # Patch process_document so it finishes successfully
    with patch("core.worker.process_document") as mock_process:
        async def mock_call(j_id):
            # Simulate processing time and setting status to COMPLETED (which the real function does)
            async with scoped_transaction() as sess:
                stmt = text("UPDATE processingjob SET status='COMPLETED' WHERE id=:job")
                await sess.execute(stmt, {"job": j_id.hex})
                
        mock_process.side_effect = mock_call
        
        # Run worker loop for a brief moment then cancel
        task = asyncio.create_task(worker_loop())
        await asyncio.sleep(0.5)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
            
        mock_process.assert_called_once_with(job_id)
        
        async with scoped_transaction() as session:
            result = await session.execute(select(ProcessingJob).where(ProcessingJob.document_id == doc_id))
            job = result.scalar_one()
            assert job.status == "COMPLETED"

@pytest.mark.asyncio
async def test_worker_cancellation_reverts_to_pending():
    doc_id = uuid.uuid4()
    job_id = uuid.uuid4()
    u_id = uuid.uuid4()
    async with scoped_transaction() as session:
        user = User(id=u_id, username="test4", hashed_password="test")
        doc = Document(id=doc_id, user_id=u_id, filename="test.pdf", original_filename="test.pdf", size_bytes=100)
        session.add(user)
        session.add(doc)
        session.add(ProcessingJob(id=job_id, document_id=doc_id, status="PENDING"))
        
    # Patch process_document to hang infinitely so we can cancel it mid-flight
    started = asyncio.Event()
    with patch("core.worker.process_document") as mock_process:
        async def hang(j_id):
            started.set()
            await asyncio.sleep(10)
        mock_process.side_effect = hang
        
        task = asyncio.create_task(worker_loop())
        # Wait until the worker has definitely claimed the job and started processing
        await asyncio.wait_for(started.wait(), timeout=5.0)
        
        # Cancel mid-flight
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
            
        # Verify reverted to PENDING
        async with scoped_transaction() as session:
            result = await session.execute(select(ProcessingJob).where(ProcessingJob.document_id == doc_id))
            job = result.scalar_one()
            assert job.status == "PENDING"

@pytest.mark.asyncio
async def test_worker_exception_sets_failed():
    doc_id = uuid.uuid4()
    job_id = uuid.uuid4()
    u_id = uuid.uuid4()
    async with scoped_transaction() as session:
        user = User(id=u_id, username="test5", hashed_password="test")
        doc = Document(id=doc_id, user_id=u_id, filename="test.pdf", original_filename="test.pdf", size_bytes=100)
        session.add(user)
        session.add(doc)
        session.add(ProcessingJob(id=job_id, document_id=doc_id, status="PENDING"))
        
    failed_event = asyncio.Event()
    
    # We patch mark_job_failed to set an event so we know when it's done
    original_mark = mark_job_failed
    async def mock_mark(d_id):
        await original_mark(d_id)
        failed_event.set()
        
    with patch("core.worker.process_document") as mock_process, \
         patch("core.worker.mark_job_failed", side_effect=mock_mark):
        mock_process.side_effect = Exception("Intentional Failure")
        
        task = asyncio.create_task(worker_loop())
        await asyncio.wait_for(failed_event.wait(), timeout=5.0)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
            
        async with scoped_transaction() as session:
            result = await session.execute(select(ProcessingJob).where(ProcessingJob.document_id == doc_id))
            job = result.scalar_one()
            assert job.status == "FAILED"

