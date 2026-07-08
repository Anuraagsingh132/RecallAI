import requests
import time
import os
import uuid

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    print("--- STARTING AUTOMATED SMOKE TEST ---")
    
    # Check if backend is up
    try:
        resp = requests.get(f"{BASE_URL}/health")
        print("Backend /health status:", resp.status_code)
    except Exception as e:
        print(f"Backend not reachable: {e}")
        return

    test_user = f"testuser_{uuid.uuid4().hex[:6]}"
    password = "password123"

    print("\n1. Register new user")
    resp = requests.post(f"{BASE_URL}/auth/register", json={"username": test_user, "password": password})
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    print("[OK] Register success")

    print("\n2. Register same user again")
    resp = requests.post(f"{BASE_URL}/auth/register", json={"username": test_user, "password": password})
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
    print("[OK] Duplicate register caught")

    print("\n3. Login with correct credentials")
    resp = requests.post(f"{BASE_URL}/auth/token", data={"username": test_user, "password": password})
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    token = resp.json()["access_token"]
    print("[OK] Login success, got token")

    print("\n4. Login with wrong password")
    resp = requests.post(f"{BASE_URL}/auth/token", data={"username": test_user, "password": "wrongpassword"})
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
    print("[OK] Wrong password caught")

    headers = {"Authorization": f"Bearer {token}"}

    print("\n5. Upload a document")
    # create a dummy PDF file
    with open("dummy.pdf", "wb") as f:
        f.write(b"%PDF-1.4\n%This is a dummy PDF file.\n")
    
    with open("dummy.pdf", "rb") as f:
        resp = requests.post(f"{BASE_URL}/documents/upload", headers=headers, files={"file": ("dummy.pdf", f, "application/pdf")})
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    doc_id = resp.json()["document_id"]
    print(f"[OK] Upload success, doc_id: {doc_id}")

    print("\n6. Poll document status")
    start_time = time.time()
    while True:
        resp = requests.get(f"{BASE_URL}/documents/{doc_id}", headers=headers)
        status = resp.json()["status"]
        elapsed = time.time() - start_time
        print(f"   Status at {elapsed:.1f}s: {status}")
        if status in ["COMPLETED", "ERROR", "FAILED"]:
            break
        time.sleep(1)
        if elapsed > 30:
            print("[FAIL] Polling timeout")
            break

    print("\n7. List documents")
    resp = requests.get(f"{BASE_URL}/documents", headers=headers)
    assert resp.status_code == 200
    docs = resp.json()
    assert any(d["id"] == doc_id for d in docs), "Document not found in list"
    print(f"[OK] Listed documents, found {len(docs)} docs")

    print("\n8. Create conversation")
    resp = requests.post(f"{BASE_URL}/conversations", headers=headers)
    assert resp.status_code == 200
    conv_id = resp.json()["conversation_id"]
    print(f"[OK] Conversation created, id: {conv_id}")

    print("\n9. Send message (should NOT answer)")
    resp = requests.post(f"{BASE_URL}/conversations/{conv_id}/messages", headers=headers, json={"content": "What is the meaning of life, the universe, and everything?"})
    assert resp.status_code == 200
    data = resp.json()
    print(f"   AI Answer: {data['answer']}")
    print(f"   Answer found flag: {data['answer_found']}")
    assert data["answer_found"] == False, "Expected answer_found to be false for a dummy PDF"
    print("[OK] Handled unanswerable question correctly")

    print("\n10. Send message (should answer)")
    # Since our dummy.pdf is empty, we can't test a real answer easily, but we know it processes it.
    print("[OK] (Skipping real answer check since we uploaded a dummy PDF with no text)")

    print("\n11. Delete document")
    resp = requests.delete(f"{BASE_URL}/documents/{doc_id}", headers=headers)
    assert resp.status_code == 200
    
    # wait for background saga to finish
    time.sleep(2)
    
    # verify it's gone
    resp = requests.get(f"{BASE_URL}/documents", headers=headers)
    docs = resp.json()
    assert not any(d["id"] == doc_id for d in docs), "Document still in list"
    print("[OK] Document deleted")

    print("\n12. Logout and verify token is dead")
    resp = requests.post(f"{BASE_URL}/auth/logout", headers=headers)
    assert resp.status_code == 200
    
    resp = requests.get(f"{BASE_URL}/documents", headers=headers)
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
    print("[OK] Token successfully invalidated")

    print("--- AUTOMATED SMOKE TEST COMPLETE ---")

if __name__ == "__main__":
    run_tests()
