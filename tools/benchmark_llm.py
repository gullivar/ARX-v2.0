import time
import requests
import concurrent.futures
import statistics

# Configuration
LLM_INTERNAL = "http://192.168.8.190:17311"
LLM_EXTERNAL = "http://106.254.248.154:17311"
MODEL = "llama3:latest"

# Dummy large content (~4KB)
DUMMY_CONTENT = "This is a test content string. " * 150

def get_best_url():
    try:
        start = time.time()
        requests.get(f"{LLM_INTERNAL}/api/version", timeout=1)
        print(f"✅ Internal IP reachable ({time.time() - start:.3f}s)")
        return LLM_INTERNAL
    except:
        print("⚠️ Internal IP unreachable, using External.")
        return LLM_EXTERNAL

URL = get_best_url()

def benchmark_request(req_id, prompt, is_heavy=False):
    start = time.time()
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json" if is_heavy else None
    }
    
    try:
        url = f"{URL}/api/generate"
        response = requests.post(url, json=payload, timeout=120)
        duration = time.time() - start
        size = len(response.content)
        print(f"   [Req {req_id}] status={response.status_code}, time={duration:.2f}s, size={size}b")
        return duration
    except Exception as e:
        print(f"   [Req {req_id}] FAILED: {e}")
        return None

def run_benchmark():
    print(f"\n--- Benchmarking LLM at {URL} ---")
    
    # 1. Simple Ping
    print("\n1. Simple Chat (Hello World)...")
    t1 = benchmark_request(1, "Say hi", is_heavy=False)
    
    # 2. Heavy Analysis (Simulating Pipeline)
    print(f"\n2. Heavy Analysis (Content Length: {len(DUMMY_CONTENT)} chars)...")
    prompt = f"""
    Analyze this text:
    {DUMMY_CONTENT}
    
    Return JSON: {{ "category": "test", "is_malicious": false, "summary": "..." }}
    """
    t2 = benchmark_request(2, prompt, is_heavy=True)
    
    # 3. Concurrency Test
    print("\n3. Concurrency Test (5 parallel heavy requests)...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(benchmark_request, i+3, prompt, True) for i in range(5)]
        results = [f.result() for f in futures]
    
    valid_results = [r for r in results if r is not None]
    if valid_results:
        avg = statistics.mean(valid_results)
        print(f"\n--- Results ---")
        print(f"Simple Request: {t1:.2f}s")
        print(f"Single Heavy Request: {t2:.2f}s")
        print(f"Avg Parallel Request: {avg:.2f}s")
        print(f"Max Parallel Request: {max(valid_results):.2f}s")
        
        if avg > t2 * 1.5:
             print("⚠️  High performance penalty under load. Server might be queuing requests serially.")
        else:
             print("✅ Server handles parallel requests well.")

if __name__ == "__main__":
    run_benchmark()
