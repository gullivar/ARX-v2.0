
import os
import time
import subprocess
import urllib.request
import sys

# Configuration
START_BATCH = 31
END_BATCH = 554
CHUNK_SIZE = 50 # Process 50 batches at a time
BACKEND_DIR = "/root/project/ARX-v2.0/backend"
PROJECT_DIR = "/root/project/ARX-v2.0"
PYTHON_BIN = f"{BACKEND_DIR}/venv/bin/python3"

def log(msg):
    # Force flush
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def run_cmd(cmd, cwd=PROJECT_DIR, ignore_fail=False):
    log(f"Running: {cmd}")
    try:
        subprocess.run(cmd, shell=True, check=True, cwd=cwd)
        return True
    except subprocess.CalledProcessError as e:
        log(f"Command failed: {e}")
        if not ignore_fail:
            return False
        return True

def run_cmd_quiet(cmd, cwd=PROJECT_DIR):
    try:
        subprocess.run(cmd, shell=True, check=True, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except:
        return False

def check_backend_health():
    try:
        with urllib.request.urlopen("http://localhost:8000/api/health", timeout=2) as response:
            return response.getcode() == 200
    except:
        return False

def stop_backend():
    log("🛑 Stopping Backend to release VectorDB locks...")
    run_cmd_quiet("pkill -f uvicorn")
    time.sleep(3)
    # Ensure it's dead
    run_cmd_quiet("pkill -9 -f uvicorn")

def start_backend():
    log("🔄 Starting Backend...")
    # Start in background
    subprocess.Popen(["bash", "start_backend_strict.sh"], cwd=PROJECT_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Wait for health check
    log("Waiting for Backend to come up...")
    for _ in range(30): # Wait up to 60s
        time.sleep(2)
        if check_backend_health():
            log("✅ Backend is UP.")
            return True
    log("⚠️ Backend startup timed out (monitor might be delayed).")
    return False

def run_classification_chunk(start, end):
    log(f"🧠 Running Classification for Batches {start}-{end}...")
    chunk_script = f"""
import sys
sys.path.append('{PROJECT_DIR}')
from smart_classifier_v2 import process_batch

count = 0
for i in range({start}, {end} + 1):
    if process_batch(i):
        count += 1
print(f"Processed {{count}} batches.")
"""
    with open(f"{PROJECT_DIR}/temp_runner.py", "w") as f:
        f.write(chunk_script)
        
    return run_cmd(f"python3 temp_runner.py", cwd=PROJECT_DIR)

def import_results_sequentially(start, end):
    log(f"📥 Importing Results Sequentially (Batches {start}-{end})...")
    
    success_count = 0
    fail_count = 0
    
    for i in range(start, end + 1):
        # Call a fresh python process for EVERY batch -> Ensures memory is freed
        cmd = f"{PYTHON_BIN} import_single_batch.py --batch {i}"
        if run_cmd(cmd, cwd=BACKEND_DIR, ignore_fail=True):
            success_count += 1
        else:
            fail_count += 1
            # If we hit an error, maybe wait a bit or try to clean lock?
            time.sleep(1)
            
        if i % 10 == 0:
            log(f"  ... Progress: Batch {i} done.")
            
    log(f"Import Finished: {success_count} success, {fail_count} failed.")
    return True

def main():
    log("🚀 Auto-Pilot Analysis Started (v5 - Process Isolation Mode)")
    
    # 1. Clean Slate for DB (User requested stability)
    # WARNING: Only do this if we are starting fresh or resuming with persistent storage
    # Assuming user still wants to force progress even if it means some re-indexing
    
    for i in range(START_BATCH, END_BATCH + 1, CHUNK_SIZE):
        chunk_end = min(i + CHUNK_SIZE - 1, END_BATCH)
        log(f"\n==========================================")
        log(f"=== Processing Chunk {i} to {chunk_end} ===")
        log(f"==========================================")
        
        # 1. Classify
        if not run_classification_chunk(i, chunk_end):
            log("❌ Classification failed. Stopping.")
            break
            
        # 2. Stop Backend
        stop_backend()
        
        # 3. Import Sequentially (Process Isolation)
        import_results_sequentially(i, chunk_end)
            
        # 4. Start Backend
        start_backend()
        
        log(f"✅ Chunk {i}-{chunk_end} Complete.")
        
        # Cool down
        time.sleep(5)

if __name__ == "__main__":
    main()
