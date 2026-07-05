import pytest
import pytest_asyncio
import asyncio
import uuid
import os
import shutil
from sqlmodel import select, SQLModel
from core.database import AsyncSessionLocal, engine
from models.base import User, ProcessingJob, Document, DocumentChunk
from core.transactions import scoped_transaction
from core.qdrant import init_qdrant, qdrant_client, COLLECTION_NAME
from services.ingestion import process_document, execute_deletion_saga
from core.storage import get_secure_file_path, UPLOAD_DIR, ensure_upload_dir
from unittest.mock import patch
from core.embeddings import EmbeddingFatalError, EmbeddingError

async def mock_generate_embeddings(texts):
    return [[0.1] * 768 for _ in texts]

@pytest.fixture(autouse=True)
def mock_embeds():
    with patch("services.ingestion.generate_embeddings", side_effect=mock_generate_embeddings):
        yield

@pytest_asyncio.fixture(autouse=True)
async def setup_ingestion_env():
    await init_qdrant()
    ensure_upload_dir()
    yield
    await qdrant_client.delete_collection(COLLECTION_NAME)

async def setup_job(filename: str, copy_dummy: bool = True):
    async with scoped_transaction() as session:
        user = User(username=f"user_{uuid.uuid4()}", hashed_password="pwd")
        session.add(user)
        await session.flush()
        doc = Document(user_id=user.id, filename=filename)
        session.add(doc)
        await session.flush()
        job = ProcessingJob(document_id=doc.id)
        session.add(job)
        await session.flush()
        
        doc_id = doc.id
        job_id = job.id
        
    if copy_dummy:
        # Copy dummy PDF to uploads/ using the secure logic
        dest_path = get_secure_file_path(doc_id, filename)
        if os.path.exists("tests/fixtures/dummy.pdf"):
            shutil.copy("tests/fixtures/dummy.pdf", dest_path)
            
    return job_id, doc_id

@pytest.mark.asyncio
async def test_success_path():
    job_id, doc_id = await setup_job("test_doc.pdf")
    await process_document(job_id)
    
    async with AsyncSessionLocal() as session:
        doc = await session.get(Document, doc_id)
        assert doc.status == "COMPLETED"
        assert doc.embedding_model_version == "text-embedding-004"
        chunks = await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == doc_id))
        assert len(chunks.scalars().all()) > 0
        
    # Verify file was deleted by lifecycle manager
    dest_path = get_secure_file_path(doc_id, "test_doc.pdf")
    assert not os.path.exists(dest_path)

@pytest.mark.asyncio
async def test_gemini_429_failure():
    job_id, doc_id = await setup_job("fail.pdf")
    with patch("services.ingestion.generate_embeddings", side_effect=EmbeddingError("429")):
        with pytest.raises(EmbeddingError):
            await process_document(job_id)
    
    async with AsyncSessionLocal() as session:
        doc = await session.get(Document, doc_id)
        assert doc.status == "FAILED"

@pytest.mark.asyncio
async def test_qdrant_failure():
    job_id, doc_id = await setup_job("qdrant_fail.pdf")
    with patch("services.ingestion.qdrant_client.upsert", side_effect=Exception("Qdrant Down")):
        with patch("services.ingestion.wipe_document_idempotent") as mock_wipe:
            with pytest.raises(Exception):
                await process_document(job_id)
            assert mock_wipe.call_count == 2
    
    async with AsyncSessionLocal() as session:
        doc = await session.get(Document, doc_id)
        assert doc.status == "FAILED"



@pytest.mark.asyncio
async def test_deletion_saga():
    job_id, doc_id = await setup_job("saga_doc.pdf")
    await process_document(job_id)
    
    await execute_deletion_saga(doc_id)
    
    async with AsyncSessionLocal() as session:
        doc = await session.get(Document, doc_id)
        assert doc is None
        chunks = await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == doc_id))
        assert len(chunks.scalars().all()) == 0

@pytest.mark.asyncio
async def test_concurrent_ingestion():
    jobs = []
    for i in range(10):
        job_id, _ = await setup_job(f"concurrent_{i}.pdf")
        jobs.append(job_id)
        
    tasks = [process_document(j) for j in jobs]
    await asyncio.gather(*tasks)
    
    async with AsyncSessionLocal() as session:
        docs = await session.execute(select(Document).where(Document.status == "COMPLETED"))
        assert len(docs.scalars().all()) == 10

@pytest.mark.asyncio
async def test_file_not_found():
    job_id, doc_id = await setup_job("missing.pdf", copy_dummy=False)
    with pytest.raises(FileNotFoundError):
        await process_document(job_id)
        
    async with AsyncSessionLocal() as session:
        doc = await session.get(Document, doc_id)
        assert doc.status == "FAILED"

@pytest.mark.asyncio
async def test_cleanup_on_failure():
    job_id, doc_id = await setup_job("corrupted.pdf")
    # Simulate fitz error by deleting the file but patching fitz to raise error
    dest_path = get_secure_file_path(doc_id, "corrupted.pdf")
    
    with patch("services.chunking.fitz.open", side_effect=Exception("Simulated Corruption Error")):
        with pytest.raises(Exception):
            await process_document(job_id)
            
    # The finally block should have deleted the file!
    assert not os.path.exists(dest_path), "File was not cleaned up after failure!"
    
    async with AsyncSessionLocal() as session:
        doc = await session.get(Document, doc_id)
        assert doc.status == "FAILED"

@pytest.mark.asyncio
async def test_embedding_batch_limits():
    job_id, doc_id = await setup_job("large.pdf")
    
    # We will patch the chunk_text to yield a lot of items
    def mock_extract(*args):
        loop = args[1]
        queue = args[2]
        for i in range(250): # 250 items, each with 1 child chunk
            asyncio.run_coroutine_threadsafe(queue.put((f"Parent {i}", [f"Child {i}"])), loop).result()
        asyncio.run_coroutine_threadsafe(queue.put(None), loop).result()
        
    call_count = 0
    async def counted_mock_embed(chunks):
        nonlocal call_count
        call_count += 1
        return [[0.1]*768 for _ in chunks]

    with patch("services.ingestion.extract_and_chunk_sync", side_effect=mock_extract):
        with patch("services.ingestion.generate_embeddings", side_effect=counted_mock_embed):
            await process_document(job_id)
            
    # Batch size is 100. 250 chunks means 3 calls (100, 100, 50).
    assert call_count == 3, f"Expected 3 batch calls, got {call_count}"

