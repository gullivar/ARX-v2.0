
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

def run_cmd(cmd, cwd=PROJECT_DIR):
    log(f"Running: {cmd}")
    try:
        subprocess.run(cmd, shell=True, check=True, cwd=cwd)
        return True
    except subprocess.CalledProcessError as e:
        log(f"Command failed: {e}")
        return False

def check_backend_health():
    try:
        with urllib.request.urlopen("http://localhost:8000/api/health", timeout=2) as response:
            return response.getcode() == 200
    except:
        return False

def stop_backend():
    log("🛑 Stopping Backend to release VectorDB locks...")
    run_cmd("pkill -f uvicorn")
    time.sleep(3)

def start_backend():
    log("🔄 Starting Backend...")
    # Start in background
    subprocess.Popen(["bash", "start_backend_strict.sh"], cwd=PROJECT_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Wait for health check
    log("Waiting for Backend to come up...")
    for _ in range(15):
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

def import_results_chunk(start, end):
    log(f"📥 Importing Results into DB (Chunk {start}-{end})...")
    # Using v3 importer with range args
    return run_cmd(f"{PYTHON_BIN} import_manual_results_v3.py --start {start} --end {end}", cwd=BACKEND_DIR)

def check_progress():
    try:
        run_cmd(f"{PYTHON_BIN} check_db_status.py", cwd=BACKEND_DIR)
    except:
        pass

def main():
    log("🚀 Auto-Pilot Analysis Started (v4 - No Deps)")
    
    # Check if we should resume
    # Simple logic: start loop but check inside if work is needed? 
    # For now, let's just stick to the loop. 
    # To avoid re-doing work, classification script skips existing files.
    # Import script handles updates.
    
    for i in range(START_BATCH, END_BATCH + 1, CHUNK_SIZE):
        chunk_end = min(i + CHUNK_SIZE - 1, END_BATCH)
        log(f"\n=== Processing Chunk {i} to {chunk_end} ===")
        
        # 1. Classify
        if not run_classification_chunk(i, chunk_end):
            log("❌ Classification failed. Stopping.")
            break
            
        # 2. Stop Backend (CRITICAL for DB Lock)
        stop_backend()
        
        # 3. Import (Range scoped)
        if not import_results_chunk(i, chunk_end):
            log("❌ Import failed. Stopping.")
            break
            
        # 4. Start Backend (To serve results/monitor)
        start_backend()
        
        # 5. Monitor
        check_progress()
        
        log(f"✅ Chunk {i}-{chunk_end} Complete.")
        time.sleep(5)

if __name__ == "__main__":
    main()
