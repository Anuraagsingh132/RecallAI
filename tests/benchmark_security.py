import time
import os
import psutil
from fastapi.testclient import TestClient
from main import app
import io

def benchmark():
    client = TestClient(app)
    process = psutil.Process(os.getpid())
    
    # Baseline
    mem_before = process.memory_info().rss / 1024 / 1024
    print(f"Memory Before: {mem_before:.2f} MB")
    
    # Test valid upload speed
    payload = b"a" * (5 * 1024 * 1024) # 5MB
    start_time = time.time()
    res = client.post("/test-upload", files={"file": ("test.txt", io.BytesIO(payload))})
    duration = time.time() - start_time
    assert res.status_code == 200
    print(f"5MB Valid Upload Time: {duration:.4f}s")
    
    # Test rejected upload
    payload_oversize = b"a" * (15 * 1024 * 1024) # 15MB
    mem_payload_created = process.memory_info().rss / 1024 / 1024
    
    start_time = time.time()
    res2 = client.post("/test-upload", files={"file": ("test.txt", io.BytesIO(payload_oversize))})
    duration2 = time.time() - start_time
    assert res2.status_code == 413
    print(f"15MB Rejected Upload Time (Short-circuit): {duration2:.4f}s")
    
    mem_after = process.memory_info().rss / 1024 / 1024
    print(f"Memory After Requests: {mem_after:.2f} MB")
    
    # The payload strings exist in RAM in this benchmark script, 
    # but the middleware itself doesn't buffer them.

if __name__ == "__main__":
    benchmark()
