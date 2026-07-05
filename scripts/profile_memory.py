import asyncio
import tracemalloc
import fitz
import os
import shutil
from sqlmodel import SQLModel
from core.database import engine, AsyncSessionLocal
from models.base import User, ProcessingJob, Document
from core.transactions import scoped_transaction
from core.qdrant import init_qdrant, qdrant_client, COLLECTION_NAME
from services.ingestion import process_document
from core.storage import get_secure_file_path, ensure_upload_dir
from unittest.mock import patch

def create_large_pdf(filename: str, num_pages: int):
    doc = fitz.open()
    for _ in range(num_pages):
        page = doc.new_page()
        # Lots of text to simulate a dense page (~3000 chars per page)
        text = "This is a dummy PDF file for testing memory consumption. " * 60
        page.insert_text((50,50), text)
    doc.save(filename)
    doc.close()

async def mock_generate_embeddings(texts):
    return [[0.1] * 768 for _ in texts]

async def profile_ingestion(num_pages: int):
    # Setup
    pdf_name = f"dummy_{num_pages}.pdf"
    create_large_pdf(pdf_name, num_pages)
    
    await init_qdrant()
    ensure_upload_dir()
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
        
    async with scoped_transaction() as session:
        user = User()
        session.add(user)
        await session.flush()
        doc = Document(user_id=user.id, filename=pdf_name)
        session.add(doc)
        await session.flush()
        job = ProcessingJob(document_id=doc.id)
        session.add(job)
        await session.flush()
        doc_id = doc.id
        job_id = job.id
        
    dest_path = get_secure_file_path(doc_id, pdf_name)
    shutil.copy(pdf_name, dest_path)
    
    # Profile
    tracemalloc.start()
    
    with patch("services.ingestion.generate_embeddings", side_effect=mock_generate_embeddings):
        await process_document(job_id)
        
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    print(f"[{num_pages} pages] Current memory: {current / 10**6:.2f} MB, Peak memory: {peak / 10**6:.2f} MB")
    
    # Cleanup
    os.remove(pdf_name)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await qdrant_client.delete_collection(COLLECTION_NAME)

async def main():
    print("Starting Memory Profiling...")
    for pages in [10, 100, 1000]:
        await profile_ingestion(pages)

if __name__ == "__main__":
    asyncio.run(main())
