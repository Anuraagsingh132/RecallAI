import asyncio
import uuid
import os
import shutil
from sqlmodel import SQLModel
from core.database import engine, AsyncSessionLocal
from models.base import User, ProcessingJob, Document
from core.transactions import scoped_transaction
from core.qdrant import init_qdrant
from services.ingestion import process_document
from core.storage import get_secure_file_path, ensure_upload_dir



async def setup():
    await init_qdrant()
    ensure_upload_dir()
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

async def debug():
    await setup()
    
    async with scoped_transaction() as session:
        user = User()
        session.add(user)
        await session.flush()
        doc = Document(user_id=user.id, filename="dummy.pdf")
        session.add(doc)
        await session.flush()
        job = ProcessingJob(document_id=doc.id)
        session.add(job)
        await session.flush()
        doc_id = doc.id
        job_id = job.id
        
    dest_path = get_secure_file_path(doc_id, "dummy.pdf")
    shutil.copy("tests/fixtures/dummy.pdf", dest_path)
    
    print("Starting process_document")
    try:
        await asyncio.wait_for(process_document(job_id), timeout=5)
        print("process_document completed")
    except asyncio.TimeoutError:
        print("process_document hung!")
    except Exception as e:
        print(f"process_document threw: {e}")
        
if __name__ == "__main__":
    asyncio.run(debug())
