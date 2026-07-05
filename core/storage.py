import os
import uuid
import structlog
import aiofiles

logger = structlog.get_logger(__name__)

# Base directory for all physical file uploads
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")

def ensure_upload_dir():
    """Ensure the upload directory exists."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_secure_file_path(document_id: uuid.UUID, original_filename: str) -> str:
    """
    Constructs an absolute, normalized path within the UPLOAD_DIR.
    Provides path traversal protection by strictly joining with UPLOAD_DIR
    and verifying the resulting path is a child of UPLOAD_DIR.
    """
    ensure_upload_dir()
    
    # Sanitize the filename slightly (though UUID prefix guarantees uniqueness and safety)
    safe_filename = os.path.basename(original_filename)
    
    # Format: <uuid>_<safe_filename>
    stored_name = f"{document_id}_{safe_filename}"
    
    abs_path = os.path.abspath(os.path.join(UPLOAD_DIR, stored_name))
    
    # Path traversal protection
    if not abs_path.startswith(os.path.abspath(UPLOAD_DIR)):
        raise ValueError(f"Path traversal detected: {abs_path}")
        
    return abs_path

async def save_upload_stream(document_id: uuid.UUID, original_filename: str, file_stream) -> str:
    """
    Saves an uploaded file stream to the physical storage layer.
    Returns the absolute path to the stored file.
    """
    file_path = get_secure_file_path(document_id, original_filename)
    
    # Stream the file to disk to prevent OOM
    async with aiofiles.open(file_path, 'wb') as f:
        while chunk := await file_stream.read(1024 * 1024): # 1MB chunks
            await f.write(chunk)
            
    return file_path

def delete_file_idempotent(file_path: str):
    """
    Deletes the physical file if it exists. Idempotent.
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted physical file: {file_path}")
    except Exception as e:
        logger.error(f"Failed to delete file {file_path}: {e}")
