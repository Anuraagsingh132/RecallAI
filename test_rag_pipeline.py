import time
import requests

BASE_URL = "http://localhost:8000"

print("Registering rag_user...")
requests.post(f"{BASE_URL}/auth/register", json={"username": "rag_user", "password": "password"})

print("Logging in...")
token_res = requests.post(f"{BASE_URL}/auth/token", data={"username": "rag_user", "password": "password"}, headers={"Content-Type": "application/x-www-form-urlencoded"})
token = token_res.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("Uploading test_rag.pdf...")
with open("test_rag.pdf", "rb") as f:
    upload_res = requests.post(f"{BASE_URL}/documents/upload", headers=headers, files={"file": ("test_rag.pdf", f, "application/pdf")})

doc_id = upload_res.json()["id"]
print(f"Uploaded! Doc ID: {doc_id}")

print("Polling for processing completion...")
status = "PENDING"
for _ in range(15):
    doc_res = requests.get(f"{BASE_URL}/documents/{doc_id}", headers=headers)
    status = doc_res.json()["status"]
    print(f"Status: {status}")
    if status in ["COMPLETED", "FAILED"]:
        break
    time.sleep(1)

if status != "COMPLETED":
    print("Document processing failed or timed out!")
    exit(1)

print("Creating conversation...")
conv_res = requests.post(f"{BASE_URL}/conversations", headers=headers)
conv_id = conv_res.json()["conversation_id"]

print("Asking question...")
ask_res = requests.post(f"{BASE_URL}/conversations/{conv_id}/messages", headers=headers, json={"content": "What is the secret project code name and who is the lead engineer?"})

print("AI Response:")
print(ask_res.json())
