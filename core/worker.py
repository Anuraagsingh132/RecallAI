import asyncio
import uuid
import structlog
from sqlalchemy import text
from core.database import engine
from core.transactions import scoped_transaction
from services.ingestion import process_document

logger = structlog.get_logger(__name__)

# Global event used to wake the worker up instantly when a new job is uploaded
_new_job_event: asyncio.Event | None = None

def trigger_new_job():
    global _new_job_event
    if _new_job_event:
        _new_job_event.set()

async def get_next_pending_job() -> tuple[uuid.UUID | None, uuid.UUID | None]:
    async with engine.begin() as conn:
        res = await conn.execute(text("SELECT id, document_id FROM processingjob WHERE status = 'PENDING' LIMIT 1"))
        row = res.fetchone()
        if not row: return None, None
        
        job_id = row[0]
        doc_id = row[1]
        
        # update it
        await conn.execute(
            text("UPDATE processingjob SET status = 'PROCESSING', updated_at = CURRENT_TIMESTAMP WHERE id = :job_id"),
            {"job_id": str(job_id) if isinstance(job_id, uuid.UUID) else job_id}
        )
        
        if isinstance(doc_id, str): doc_id = uuid.UUID(doc_id)
        if isinstance(job_id, str): job_id = uuid.UUID(job_id)
        return doc_id, job_id

async def mark_job_failed(document_id: uuid.UUID):
    stmt = text("UPDATE processingjob SET status = 'FAILED', updated_at = CURRENT_TIMESTAMP WHERE document_id = :doc_id")
    async with engine.begin() as conn:
        await conn.execute(stmt, {"doc_id": str(document_id)})

async def mark_job_pending(document_id: uuid.UUID):
    stmt = text("UPDATE processingjob SET status = 'PENDING', updated_at = CURRENT_TIMESTAMP WHERE document_id = :doc_id")
    async with engine.begin() as conn:
        res = await conn.execute(stmt, {"doc_id": str(document_id)})
        logger.info(f"mark_job_pending for {document_id} updated {res.rowcount} rows")

async def worker_loop():
    """
    Long-running daemon loop that fetches jobs and processes them.
    Falls back to a 10s polling interval if the event misses.
    """
    global _new_job_event
    _new_job_event = asyncio.Event()
    
    logger.info("Background worker started. Spinning up 3 concurrent tasks.")
    
    async def single_worker(worker_id: int):
        while True:
            # 1. Attempt to claim a job
            try:
                document_id, job_id = await get_next_pending_job()
            except Exception as e:
                logger.error(f"[Worker-{worker_id}] Database error claiming job: {e}")
                await asyncio.sleep(5)
                continue

            # 2. If a job exists, process it
            if document_id:
                try:
                    await process_document(job_id)
                except asyncio.CancelledError:
                    logger.warning(f"[Worker-{worker_id}] cancelled mid-job {document_id}. Reverting to PENDING.")
                    me = asyncio.current_task()
                    # Fully uncancel so we can safely execute DB operations
                    while me.uncancel() > 0:
                        pass
                    try:
                        await mark_job_pending(document_id)
                    except BaseException as e:
                        logger.error(f"[Worker-{worker_id}] Failed to mark pending: {repr(e)}")
                    finally:
                        raise
                except Exception as e:
                    logger.error(f"[Worker-{worker_id}] Job failed for document {document_id}: {e}")
                    await mark_job_failed(document_id)
            else:
                # 3. No jobs. Sleep until awoken, or up to 10 seconds.
                _new_job_event.clear()
                try:
                    await asyncio.wait_for(_new_job_event.wait(), timeout=10.0)
                except asyncio.TimeoutError:
                    # Polling fallback tick
                    pass

    workers = [asyncio.create_task(single_worker(i)) for i in range(3)]
    try:
        await asyncio.gather(*workers)
    except asyncio.CancelledError:
        logger.info("Worker graceful shutdown triggered.")
        # gather already cancels its children when it gets cancelled.
        # Just wait for them to finish graceful shutdown
        await asyncio.gather(*workers, return_exceptions=True)
        raise
