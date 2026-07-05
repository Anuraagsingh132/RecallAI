import fitz
import requests
import time
import uuid

# Create a test PDF
doc = fitz.open()
page = doc.new_page()
page.insert_text(fitz.Point(50, 72), "RecallAI is an artificial intelligence system built in 2026.")
doc.save("test.pdf")
print("PDF created.")

BASE_URL = "http://127.0.0.1:8000"

# Register
username = f"testuser_{uuid.uuid4().hex[:8]}"
res = requests.post(f"{BASE_URL}/auth/register", json={"username": username, "password": "password"})
print("Register:", res.status_code, res.text)
if res.status_code != 200:
    print("Registration failed!")
    exit(1)

# Login
res = requests.post(f"{BASE_URL}/auth/token", data={"username": username, "password": "password"})
print("Login:", res.status_code, res.text)
if res.status_code != 200:
    print("Login failed!")
    exit(1)
token = res.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Upload Document
with open("test.pdf", "rb") as f:
    res = requests.post(f"{BASE_URL}/documents/upload", headers=headers, files={"file": ("test.pdf", f, "application/pdf")})
print("Upload:", res.status_code, res.text)
if res.status_code != 200:
    print("Upload failed!")
    exit(1)
doc_id = res.json()["document_id"]

# Poll status
print("Polling status...")
for _ in range(10):
    res = requests.get(f"{BASE_URL}/documents/{doc_id}", headers=headers)
    if res.status_code != 200:
        print("Status failed:", res.status_code, res.text)
        break
    status = res.json()["status"]
    print(f"Status: {status}")
    if status in ["COMPLETED", "FAILED"]:
        break
    time.sleep(2)

# Create Conversation
res = requests.post(f"{BASE_URL}/conversations", headers=headers)
print("Create Chat:", res.status_code, res.text)
if res.status_code != 200:
    exit(1)
conv_id = res.json()["conversation_id"]

# Send Message
print("Sending message...")
res = requests.post(f"{BASE_URL}/conversations/{conv_id}/messages", headers=headers, json={"content": "What year was RecallAI built?"})
print("Chat Response:", res.status_code, res.text)
