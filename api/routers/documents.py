import os
import uuid
import shutil
import aiofiles
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, BackgroundTasks
from sqlmodel import select
from core.database import AsyncSessionLocal
from core.storage import get_secure_file_path
from models.base import User, Document, ProcessingJob
from api.dependencies import get_current_user
from services.ingestion import wipe_document_idempotent, execute_deletion_saga
from core.worker import trigger_new_job
from core.config import settings

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Securely accepts an uploaded file and schedules it for processing."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")
        
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
    magic_bytes = await file.read(4)
    if not magic_bytes.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="Invalid PDF format")
    await file.seek(0)
        
    doc_id = uuid.uuid4()
    
    # 1. Save file securely to uploads directory
    try:
        dest_path = get_secure_file_path(str(doc_id), file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    try:
        async with aiofiles.open(dest_path, "wb") as buffer:
            while content := await file.read(1024 * 1024):
                await buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write file: {str(e)}")
        
    # 2. Register Document and ProcessingJob
    async with AsyncSessionLocal() as session:
        doc = Document(id=doc_id, user_id=current_user.id, filename=file.filename, status="PENDING")
        job = ProcessingJob(document_id=doc_id, status="PENDING")
        session.add(doc)
        session.add(job)
        await session.commit()
        
    # Trigger background worker instantly
    trigger_new_job()
        
    # 3. Return 202 Accepted. The background worker will pick up the PENDING job.
    return {"message": "Upload accepted", "document_id": str(doc_id), "status": "PENDING"}

@router.get("")
async def list_documents(current_user: User = Depends(get_current_user)):
    """List all documents owned by the user."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Document).where(Document.user_id == current_user.id)
        )
        docs = result.scalars().all()
        return docs

@router.get("/{document_id}")
async def get_document_status(document_id: uuid.UUID, current_user: User = Depends(get_current_user)):
    """Get status of a specific document."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Document).where(Document.id == document_id, Document.user_id == current_user.id)
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
            
        return doc

@router.delete("/{document_id}")
async def delete_document(
    document_id: uuid.UUID, 
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Triggers the full deletion saga."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Document).where(Document.id == document_id, Document.user_id == current_user.id)
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
            
        filename = doc.filename
        
    # Trigger saga in background
    background_tasks.add_task(execute_deletion_saga, document_id)
    
    # Also delete the physical file if it exists
    dest_path = get_secure_file_path(str(document_id), filename)
    if os.path.exists(dest_path):
        os.remove(dest_path)
        
    return {"message": "Deletion triggered", "document_id": str(document_id)}
