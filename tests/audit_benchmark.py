import asyncio
import time
import httpx
from main import app
from core.config import settings

async def run_benchmark(concurrent_requests: int):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        payload = b"a" * (5 * 1024 * 1024) # 5MB valid payload
        
        start_time = time.time()
        tasks = [client.post("/test-raw", content=payload) for _ in range(concurrent_requests)]
        responses = await asyncio.gather(*tasks)
        end_time = time.time()
        
        latencies = [r.elapsed.total_seconds() for r in responses]
        latencies.sort()
        
        p50 = latencies[int(len(latencies) * 0.5)] if latencies else 0
        p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0
        p99 = latencies[int(len(latencies) * 0.99)] if latencies else 0
        
        print(f"--- {concurrent_requests} Concurrent Uploads ---")
        print(f"Total Time: {end_time - start_time:.4f}s")
        print(f"Throughput: {concurrent_requests / (end_time - start_time):.2f} req/s")
        print(f"P50 Latency: {p50:.4f}s")
        print(f"P95 Latency: {p95:.4f}s")
        print(f"P99 Latency: {p99:.4f}s\n")

async def main():
    print("Starting Concurrency Benchmark...")
    for concurrency in [1, 10, 50]: # Keep it reasonable for local test runner
        await run_benchmark(concurrency)

if __name__ == "__main__":
    asyncio.run(main())
