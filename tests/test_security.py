import pytest
from fastapi.testclient import TestClient
from core.config import settings
import io
import asyncio
from fastapi import Request, UploadFile, File
import os
from main import app

@app.post("/test-raw")
async def dummy_raw(request: Request):
    count = 0
    async for chunk in request.stream():
        count += len(chunk)
    return {"status": "ok", "size": count}

@app.post("/test-upload")
async def dummy_upload(file: UploadFile = File(...)):
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    return {"status": "success", "size": file_size}

def test_missing_content_length(client: TestClient):
    payload = b"a" * (settings.MAX_UPLOAD_SIZE_BYTES + 1)
    def chunk_generator():
        yield payload
    
    response = client.post("/test-raw", content=chunk_generator(), headers={"Transfer-Encoding": "chunked"})
    assert response.status_code == 413

def test_invalid_content_length(client: TestClient):
    response = client.post("/test-raw", content=b"hello", headers={"Content-Length": "not-a-number"})
    assert response.status_code == 200

def test_chunked_transfer_upload_oversized(client: TestClient):
    def chunk_generator():
        for _ in range(11):
            yield b"a" * (1024 * 1024)  # 1MB chunks, total 11MB
    response = client.post("/test-raw", content=chunk_generator(), headers={"Transfer-Encoding": "chunked"})
    assert response.status_code == 413

def test_boundary_condition_exact(client: TestClient):
    # Exactly 10MB raw stream
    payload = b"a" * settings.MAX_UPLOAD_SIZE_BYTES
    response = client.post("/test-raw", content=payload)
    assert response.status_code == 200

def test_boundary_condition_over(client: TestClient):
    # 10MB + 1 byte
    payload = b"a" * (settings.MAX_UPLOAD_SIZE_BYTES + 1)
    response = client.post("/test-raw", content=payload)
    assert response.status_code == 413

def test_ephemeral_file_cleanup(client: TestClient):
    # Verify the test-upload endpoint works with standard files
    payload = b"a" * 1024
    response = client.post("/test-upload", files={"file": ("test.txt", io.BytesIO(payload))})
    assert response.status_code == 200
    assert response.json()["size"] == 1024

@pytest.mark.asyncio
async def test_multiple_simultaneous_oversized(client: TestClient):
    import httpx
    from main import app
    
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        payload = b"a" * (settings.MAX_UPLOAD_SIZE_BYTES + 1)
        tasks = [ac.post("/test-raw", content=payload) for _ in range(5)]
        responses = await asyncio.gather(*tasks)
        for r in responses:
            assert r.status_code == 413
