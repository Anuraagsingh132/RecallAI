import structlog
import asyncio
import uuid
import os
from qdrant_client.http.models import PointStruct, Filter, FieldCondition, MatchValue
from sqlmodel import select
from models.base import Document, DocumentChunk, ProcessingJob
from core.database import AsyncSessionLocal
from core.transactions import scoped_transaction
from core.qdrant import qdrant_client, COLLECTION_NAME
from core.embeddings import generate_embeddings
from core.storage import get_secure_file_path, delete_file_idempotent
from services.chunking import extract_and_chunk_sync
from core.config import settings

logger = structlog.get_logger(__name__)

async def wipe_document_idempotent(document_id: uuid.UUID):
    # 1. Wipe Qdrant
    try:
        await qdrant_client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[FieldCondition(key="document_id", match=MatchValue(value=str(document_id)))]
            )
        )
    except Exception as e:
        logger.warning(f"Failed to wipe document {document_id} from Qdrant: {e}")
        # Ignore 404s or other errors during idempotency wipe
        
    # 2. Wipe Database Chunks
    async with scoped_transaction() as session:
        chunks = await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == document_id))
        for chunk in chunks.scalars().all():
            await session.delete(chunk)

async def execute_deletion_saga(document_id: uuid.UUID):
    async with scoped_transaction() as session:
        doc = await session.get(Document, document_id)
        if doc:
            doc.status = "DELETING"
            
    await wipe_document_idempotent(document_id)
    
    async with scoped_transaction() as session:
        doc = await session.get(Document, document_id)
        if doc:
            await session.delete(doc)

async def process_document(job_id: uuid.UUID):
    """The state machine for ingestion with streaming generator."""
    file_path = None
    doc_id = None
    producer_task = None
    
    async with scoped_transaction() as session:
        job = await session.get(ProcessingJob, job_id)
        if not job:
            return
        job.status = "PROCESSING"
        doc = await session.get(Document, job.document_id)
        doc.status = "PROCESSING"
        doc_id = doc.id
        doc_filename = doc.filename
        doc_user_id = doc.user_id
        
    try:
        # Idempotency wipe
        await wipe_document_idempotent(doc_id)
        
        # 1. Resolve absolute file path
        file_path = get_secure_file_path(doc_id, doc_filename)
        
        async with scoped_transaction() as session:
            job = await session.get(ProcessingJob, job_id)
            job.status = "EMBEDDING"
        
        # 2. Setup Streaming Queue
        queue = asyncio.Queue(maxsize=10)
        loop = asyncio.get_running_loop()
        
        # Launch producer thread
        producer_task = asyncio.create_task(
            asyncio.to_thread(extract_and_chunk_sync, file_path, loop, queue)
        )
        
        batch_child_chunks = []
        batch_child_payloads = []
        
        while True:
            item = await queue.get()
            
            if item is None:
                queue.task_done()
                break # EOF
                
            if isinstance(item, Exception):
                queue.task_done()
                raise item # Exception from PyMuPDF
                
            parent_text, child_texts = item
            
            # Save parent to SQLite
            async with scoped_transaction() as session:
                chunk = DocumentChunk(document_id=doc_id, content=parent_text, page_number=1)
                session.add(chunk)
                await session.flush()
                parent_id = chunk.id
                
            for child_text in child_texts:
                batch_child_chunks.append(child_text)
                batch_child_payloads.append({
                    "user_id": str(doc_user_id),
                    "document_id": str(doc_id),
                    "parent_chunk_id": str(parent_id),
                    "page_number": 1
                })
                
            # Check Batch Limits
            if len(batch_child_chunks) >= settings.EMBEDDING_BATCH_SIZE:
                await _flush_embedding_batch(batch_child_chunks, batch_child_payloads)
                batch_child_chunks.clear()
                batch_child_payloads.clear()
                
            queue.task_done()
            
        # Flush remaining chunks
        if batch_child_chunks:
            await _flush_embedding_batch(batch_child_chunks, batch_child_payloads)
            
        await producer_task
            
        # 6. Final Commit
        async with scoped_transaction() as session:
            job = await session.get(ProcessingJob, job_id)
            job.status = "COMPLETED"
            doc = await session.get(Document, doc_id)
            doc.status = "COMPLETED"
            doc.embedding_model_version = "text-embedding-004"
            
    except asyncio.CancelledError:
        logger.warning(f"Ingestion cancelled for {doc_id}")
        raise
    except Exception as e:
        logger.error(f"Ingestion failed for {doc_id}: {e}")
        async with scoped_transaction() as session:
            job = await session.get(ProcessingJob, job_id)
            if job:
                job.status = "FAILED"
            doc = await session.get(Document, doc_id)
            if doc:
                doc.status = "FAILED"
        # Rollback partial chunks on failure to avoid orphans
        if doc_id:
            await wipe_document_idempotent(doc_id)
        raise
    finally:
        # Remediation A: Guaranteed File Cleanup
        if file_path:
            delete_file_idempotent(file_path)

async def _flush_embedding_batch(chunks: list[str], payloads: list[dict]):
    """Helper to process a single batch of embeddings and insert to Qdrant."""
    embeddings = await generate_embeddings(chunks)
    points = []
    for i, emb in enumerate(embeddings):
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=emb,
            payload=payloads[i]
        ))
    if points:
        await qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points)
