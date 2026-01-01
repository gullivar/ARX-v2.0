import asyncio
import httpx
import time
import json

LLM_HOST = "http://106.254.248.154:17311"
MODEL = "llama3:latest"

async def mock_analysis(client, i):
    prompt = "This is a test prompt. Reply with a short JSON."
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }
    start = time.time()
    try:
        resp = await client.post(f"{LLM_HOST}/api/generate", json=payload)
        duration = time.time() - start
        print(f"[{i}] Status: {resp.status_code}, Time: {duration:.2f}s")
        return duration
    except Exception as e:
        print(f"[{i}] Error: {e}")
        return 0

async def main():
    print(f"Testing Async LLM Throughput to {LLM_HOST}...")
    
    # Simulate batch of 10
    batch_size = 10
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
    timeout = httpx.Timeout(45.0, connect=5.0)
    
    start_total = time.time()
    
    async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
        tasks = [mock_analysis(client, i) for i in range(batch_size)]
        results = await asyncio.gather(*tasks)
        
    total_time = time.time() - start_total
    print("-" * 30)
    print(f"Total Time for {batch_size} reqs: {total_time:.2f}s")
    print(f"Average Request Time: {sum(results)/len(results):.2f}s")
    print(f"Effective TPS: {batch_size/total_time:.2f}")

if __name__ == "__main__":
    asyncio.run(main())
