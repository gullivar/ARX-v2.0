
import os
import time
import subprocess
import glob
import json
import requests

# Configuration
START_BATCH = 31
END_BATCH = 554
CHUNK_SIZE = 50 # Process 50 batches at a time
BACKEND_DIR = "/root/project/ARX-v2.0/backend"
PROJECT_DIR = "/root/project/ARX-v2.0"
PYTHON_BIN = f"{BACKEND_DIR}/venv/bin/python3"

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def run_cmd(cmd, cwd=PROJECT_DIR):
    log(f"Running: {cmd}")
    try:
        subprocess.run(cmd, shell=True, check=True, cwd=cwd)
        return True
    except subprocess.CalledProcessError as e:
        log(f"Command failed: {e}")
        return False

def restart_backend():
    log("🔄 Restarting Backend to clear VectorDB locks...")
    run_cmd("pkill -f uvicorn")
    time.sleep(2)
    # Start in background
    subprocess.Popen(["bash", "start_backend_strict.sh"], cwd=PROJECT_DIR)
    
    # Wait for health check
    log("Waiting for Backend to come up...")
    for _ in range(10):
        time.sleep(3)
        try:
            r = requests.get("http://localhost:8000/api/health", timeout=2)
            if r.status_code == 200:
                log("✅ Backend is UP.")
                return True
        except:
            pass
    log("⚠️ Backend might not be ready, but proceeding...")
    return False

def run_classification_chunk(start, end):
    log(f"🧠 Running Classification for Batches {start}-{end}...")
    # Generate a temporary runner script for this chunk
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

def import_results_chunk():
    log(f"📥 Importing Results into DB...")
    # Use v2 importer which handles all existing result files
    return run_cmd(f"{PYTHON_BIN} import_manual_results_v2.py", cwd=BACKEND_DIR)

def check_progress():
    # Simple verify
    try:
        # Check DB count
        # (This implies we need a python script to check DB, reusing existing one)
        run_cmd(f"{PYTHON_BIN} check_db_status.py", cwd=BACKEND_DIR)
    except:
        pass

def main():
    log("🚀 Auto-Pilot Analysis Started")
    
    for i in range(START_BATCH, END_BATCH + 1, CHUNK_SIZE):
        chunk_end = min(i + CHUNK_SIZE - 1, END_BATCH)
        log(f"\n=== Processing Chunk {i} to {chunk_end} ===")
        
        # 1. Classify
        if not run_classification_chunk(i, chunk_end):
            log("❌ Classification failed. Stopping.")
            break
            
        # 2. Restart Backend (Preventative measure for VectorDB stability)
        restart_backend()
        
        # 3. Import
        if not import_results_chunk():
            log("❌ Import failed. Stopping.")
            break
            
        # 4. Monitor
        check_progress()
        
        log(f"✅ Chunk {i}-{chunk_end} Complete.")
        time.sleep(5)

if __name__ == "__main__":
    main()
