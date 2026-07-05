import pytest
import pytest_asyncio
import uuid
import time
from sqlmodel import SQLModel
from core.database import AsyncSessionLocal, engine
from models.base import User, Document, ProcessingJob
from core.transactions import scoped_transaction
from core.qdrant import init_qdrant, qdrant_client, COLLECTION_NAME
from services.ingestion import process_document
from services.retrieval import retrieve_context
from services.generation import generate_answer
from unittest.mock import patch

class MockMessage:
    def __init__(self, content):
        self.content = content

class MockChoice:
    def __init__(self, message):
        self.message = message

class MockResponse:
    def __init__(self, content):
        self.choices = [MockChoice(MockMessage(content))]

async def mock_groq_create(*args, **kwargs):
    messages = kwargs.get("messages", [])
    query = messages[-1]["content"] if messages else ""
    q_lower = query.lower()
    
    if "nonexistent" in q_lower:
        return MockResponse('{"answer_found": false, "answer": "", "citations": []}')
    if "partial" in q_lower:
        return MockResponse('{"answer_found": true, "answer": "I am partially certain. [Source: test.pdf, Page: 1]", "citations": []}')
    return MockResponse('{"answer_found": true, "answer": "Mocked answer. [Source: test.pdf, Page: 1]", "citations": []}')

from unittest.mock import patch, AsyncMock, MagicMock

@pytest.fixture(autouse=True)
def mock_groq():
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=mock_groq_create)
    with patch("services.generation.groq_client", mock_client):
        yield

async def mock_generate_embeddings(texts):
    return [[0.1] * 768 for _ in texts]

@pytest.fixture(autouse=True)
def mock_embeds():
    with patch("services.retrieval.generate_embeddings", side_effect=mock_generate_embeddings):
        with patch("services.ingestion.generate_embeddings", side_effect=mock_generate_embeddings):
            yield

@pytest_asyncio.fixture(autouse=True)
async def setup_qdrant():
    await init_qdrant()
    yield
    await qdrant_client.delete_collection(COLLECTION_NAME)

async def setup_ingested_doc(filename: str):
    import os
    from core.storage import get_secure_file_path
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
        job_id, doc_id, user_id = job.id, doc.id, user.id
        
    dest_path = get_secure_file_path(str(doc_id), filename)
    import shutil
    shutil.copy("tests/fixtures/dummy.pdf", dest_path)
        
    await process_document(job_id)
    return user_id, doc_id

@pytest.mark.asyncio
async def test_hallucination_cases():
    user_id, _ = await setup_ingested_doc("test.pdf")
    
    # Case A: Answer exists
    context = await retrieve_context("Mocked content", user_id)
    assert context != ""
    answer = await generate_answer("What is the content?", context)
    assert "[Source: test.pdf, Page: 1]" in answer.answer
    
    # Case B: Answer does not exist
    empty_answer = await generate_answer("Nonexistent data", "")
    assert empty_answer.answer_found is False
    
    # Case C: Partial answer
    partial_answer = await generate_answer("MOCK_PARTIAL", context)
    assert "partially" in partial_answer.answer

@pytest.mark.asyncio
async def test_security_isolation():
    user_a, _ = await setup_ingested_doc("user_a_doc.pdf")
    user_b, _ = await setup_ingested_doc("user_b_doc.pdf")
    
    context = await retrieve_context("Mocked content", user_b)
    
    assert "user_b_doc.pdf" in context
    assert "user_a_doc.pdf" not in context
    
@pytest.mark.asyncio
async def test_performance_latency():
    user_id, _ = await setup_ingested_doc("perf_doc.pdf")
    
    start = time.time()
    context = await retrieve_context("performance query", user_id)
    retrieval_time = time.time() - start
    
    start_gen = time.time()
    answer = await generate_answer("performance query", context)
    gen_time = time.time() - start_gen
    
    assert retrieval_time < 1.0 
