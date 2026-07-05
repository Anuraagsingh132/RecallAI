import structlog
import asyncio
import fitz
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Tuple

logger = structlog.get_logger(__name__)

PARENT_CHUNK_SIZE = 1000
PARENT_CHUNK_OVERLAP = 200
CHILD_CHUNK_SIZE = 250
CHILD_CHUNK_OVERLAP = 0
MAX_BUFFER_SIZE = 10000

def _get_parent_splitter():
    return RecursiveCharacterTextSplitter(
        chunk_size=PARENT_CHUNK_SIZE,
        chunk_overlap=PARENT_CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""]
    )

def _get_child_splitter():
    return RecursiveCharacterTextSplitter(
        chunk_size=CHILD_CHUNK_SIZE,
        chunk_overlap=CHILD_CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""]
    )

def extract_and_chunk_sync(file_path: str, loop: asyncio.AbstractEventLoop, queue: asyncio.Queue):
    """
    Synchronous generator that extracts text from PDF and feeds it into the async Queue.
    This runs in a background thread to prevent event loop blocking.
    Applies backpressure via queue limits.
    """
    parent_splitter = _get_parent_splitter()
    child_splitter = _get_child_splitter()
    buffer = ""
    
    if not os.path.exists(file_path):
        future = asyncio.run_coroutine_threadsafe(queue.put(FileNotFoundError(f"File not found on disk: {file_path}")), loop)
        future.result()
        return

    try:
        doc = fitz.open(file_path)
        for page in doc:
            buffer += page.get_text() + "\n"
            
            while len(buffer) >= PARENT_CHUNK_SIZE * 2:
                if len(buffer) > MAX_BUFFER_SIZE:
                    logger.warning(f"Buffer exceeded MAX_BUFFER_SIZE ({len(buffer)} > {MAX_BUFFER_SIZE}). Forcing chunk split.")
                    
                chunks = parent_splitter.split_text(buffer)
                if len(chunks) > 1:
                    # Yield all but the last chunk
                    for chunk in chunks[:-1]:
                        child_chunks = child_splitter.split_text(chunk)
                        # Push to async queue with backpressure
                        future = asyncio.run_coroutine_threadsafe(queue.put((chunk, child_chunks)), loop)
                        future.result()  # Block thread until queue has space
                    buffer = chunks[-1]
                else:
                    # Not enough split boundaries found in a huge block
                    if len(buffer) > MAX_BUFFER_SIZE:
                        logger.warning("Forcing hard split due to massive un-splittable block.")
                        child_chunks = child_splitter.split_text(buffer)
                        future = asyncio.run_coroutine_threadsafe(queue.put((buffer, child_chunks)), loop)
                        future.result()
                        buffer = ""
                    break
                    
        # End of document
        if buffer.strip():
            for chunk in parent_splitter.split_text(buffer):
                child_chunks = child_splitter.split_text(chunk)
                future = asyncio.run_coroutine_threadsafe(queue.put((chunk, child_chunks)), loop)
                future.result()
                
        # Send EOF marker
        future = asyncio.run_coroutine_threadsafe(queue.put(None), loop)
        future.result()

    except fitz.FileDataError as e:
        logger.error(f"PyMuPDF FileDataError on {file_path}: {e}")
        future = asyncio.run_coroutine_threadsafe(queue.put(ValueError("Uploaded file is corrupted or not a valid PDF.")), loop)
        future.result()
    except Exception as e:
        logger.error(f"Unexpected PyMuPDF error on {file_path}: {e}")
        future = asyncio.run_coroutine_threadsafe(queue.put(e), loop)
        future.result()
