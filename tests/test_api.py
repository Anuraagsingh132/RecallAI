import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import uuid
from sqlmodel import select
import os

from main import app
from core.database import AsyncSessionLocal
from models.base import User, Conversation, Message, Document
from pydantic import BaseModel
class AnswerResponse(BaseModel):
    answer_found: bool
    answer: str
    citations: list

from api.routers.auth import get_password_hash, create_access_token

# Removed duplicated setup_env

@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture
async def mock_user_id():
    async with AsyncSessionLocal() as session:
        user = User(username=f"mock_{uuid.uuid4()}", hashed_password=get_password_hash("pwd"))
        session.add(user)
        await session.commit()
        await session.refresh(user)
        token = create_access_token({"sub": user.username})
        return {"id": str(user.id), "token": token}

@pytest_asyncio.fixture
async def other_user_id():
    async with AsyncSessionLocal() as session:
        user = User(username=f"other_{uuid.uuid4()}", hashed_password=get_password_hash("pwd"))
        session.add(user)
        await session.commit()
        await session.refresh(user)
        token = create_access_token({"sub": user.username})
        return {"id": str(user.id), "token": token}

@pytest.mark.asyncio
async def test_upload_document(async_client, mock_user_id, monkeypatch):
    mock_called = False
    def mock_trigger():
        nonlocal mock_called
        mock_called = True
    monkeypatch.setattr("api.routers.documents.trigger_new_job", mock_trigger)
    
    # Needs valid magic bytes for PDF
    files = {"file": ("test.pdf", b"%PDF-1.4\n%mock\n", "application/pdf")}
    response = await async_client.post(
        "/documents/upload",
        files=files,
        headers={"Authorization": f"Bearer {mock_user_id['token']}"}
    )
        
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Upload accepted"
    assert "document_id" in data
    assert data["status"] == "PENDING"
    assert mock_called, "trigger_new_job was not called!"
    
    # Verify it's in the DB
    async with AsyncSessionLocal() as session:
        doc = await session.get(Document, uuid.UUID(data["document_id"]))
        assert doc is not None
        assert doc.user_id == uuid.UUID(mock_user_id['id'])
        assert doc.filename == "test.pdf"

@pytest.mark.asyncio
async def test_upload_non_pdf(async_client, mock_user_id):
    files = {"file": ("test.txt", b"this is text", "text/plain")}
    response = await async_client.post(
        "/documents/upload",
        files=files,
        headers={"Authorization": f"Bearer {mock_user_id['token']}"}
    )
    assert response.status_code == 400
    assert "Only PDF files are allowed" in response.json()["detail"]

@pytest.mark.asyncio
async def test_upload_invalid_magic_bytes(async_client, mock_user_id):
    files = {"file": ("test.pdf", b"fake pdf content", "application/pdf")}
    response = await async_client.post(
        "/documents/upload",
        files=files,
        headers={"Authorization": f"Bearer {mock_user_id['token']}"}
    )
    assert response.status_code == 400
    assert "Invalid PDF format" in response.json()["detail"]

@pytest.mark.asyncio
async def test_delete_document_api(async_client, mock_user_id, monkeypatch):
    files = {"file": ("test.pdf", b"%PDF-1.4\n%mock\n", "application/pdf")}
    res_up = await async_client.post("/documents/upload", files=files, headers={"Authorization": f"Bearer {mock_user_id['token']}"})
    doc_id = res_up.json()["document_id"]
    
    mock_exists = False
    mock_remove = False
    mock_qdrant_delete = False
    
    original_exists = os.path.exists
    def fake_exists(path):
        nonlocal mock_exists
        if str(doc_id) in str(path):
            mock_exists = True
            return True
        return original_exists(path)
        
    def fake_remove(path):
        nonlocal mock_remove
        if str(doc_id) in str(path):
            mock_remove = True
            
    async def fake_qdrant_delete(collection_name, points_selector):
        nonlocal mock_qdrant_delete
        mock_qdrant_delete = True
        
    monkeypatch.setattr("os.path.exists", fake_exists)
    monkeypatch.setattr("os.remove", fake_remove)
    monkeypatch.setattr("services.ingestion.qdrant_client.delete", fake_qdrant_delete)
    
    res_del = await async_client.delete(f"/documents/{doc_id}", headers={"Authorization": f"Bearer {mock_user_id['token']}"})
    assert res_del.status_code == 200
    
    import asyncio
    await asyncio.sleep(0.5)
    
    async with AsyncSessionLocal() as session:
        doc = await session.get(Document, uuid.UUID(doc_id))
        assert doc is None
        
    assert mock_exists, "os.path.exists was not called to check file"
    assert mock_remove, "os.remove was not called to delete file"
    assert mock_qdrant_delete, "Qdrant delete was not called"

@pytest.mark.asyncio
async def test_cross_user_isolation(async_client, mock_user_id, other_user_id):
    # User 1 creates conversation
    res1 = await async_client.post("/conversations", headers={"Authorization": f"Bearer {mock_user_id['token']}"})
    assert res1.status_code == 200
    conv_id = res1.json()["conversation_id"]
    
    # User 2 tries to fetch User 1's conversation messages
    res2 = await async_client.get(f"/conversations/{conv_id}/messages", headers={"Authorization": f"Bearer {other_user_id['token']}"})
    assert res2.status_code == 404 # Isolated
    
@pytest.mark.asyncio
async def test_chat_history(async_client, mock_user_id, monkeypatch):
    # 1. Create Conversation
    res_conv = await async_client.post("/conversations", headers={"Authorization": f"Bearer {mock_user_id['token']}"})
    conv_id = res_conv.json()["conversation_id"]
    
    # Mock retrieval and generation
    async def mock_retrieve_context(query, uid, top_k=20):
        return "mock context"
        
    async def mock_generate_answer(query, context, chat_history=None):
        ans = f"Mock answer to {query}. History count: {len(chat_history) if chat_history else 0}"
        return AnswerResponse(answer_found=True, answer=ans, citations=[])
        
    monkeypatch.setattr("api.routers.chat.retrieve_context", mock_retrieve_context)
    monkeypatch.setattr("api.routers.chat.generate_answer", mock_generate_answer)
    
    # 2. Send Message 1
    res1 = await async_client.post(
        f"/conversations/{conv_id}/messages", 
        json={"content": "Hello 1"},
        headers={"Authorization": f"Bearer {mock_user_id['token']}"}
    )
    assert res1.status_code == 200
    ans1 = res1.json()
    assert "Mock answer to Hello 1" in ans1["answer"]
    assert "History count: 0" in ans1["answer"] # 0 because it's the first message (excluding itself)
    
    # 3. Send Message 2
    res2 = await async_client.post(
        f"/conversations/{conv_id}/messages", 
        json={"content": "Hello 2"},
        headers={"Authorization": f"Bearer {mock_user_id['token']}"}
    )
    assert res2.status_code == 200
    ans2 = res2.json()
    assert "Mock answer to Hello 2" in ans2["answer"]
    assert "History count: 2" in ans2["answer"] # 1 user + 1 AI from msg 1
    
    # 4. Fetch History
    res_hist = await async_client.get(f"/conversations/{conv_id}/messages", headers={"Authorization": f"Bearer {mock_user_id['token']}"})
    hist = res_hist.json()
    assert len(hist) == 4 # 2 user msgs + 2 ai msgs
    assert hist[0]["content"] == "Hello 1"
    assert hist[1]["role"] == "model"
    assert hist[2]["content"] == "Hello 2"
    assert hist[3]["role"] == "model"

@pytest.mark.asyncio
async def test_logout_revokes_token(async_client, mock_user_id):
    # Try a protected route first, should succeed
    res1 = await async_client.post("/conversations", headers={"Authorization": f"Bearer {mock_user_id['token']}"})
    assert res1.status_code == 200
    
    # Logout
    res_logout = await async_client.post("/auth/logout", headers={"Authorization": f"Bearer {mock_user_id['token']}"})
    assert res_logout.status_code == 200
    
    # Try the protected route again, should fail
    res2 = await async_client.post("/conversations", headers={"Authorization": f"Bearer {mock_user_id['token']}"})
    assert res2.status_code == 401
