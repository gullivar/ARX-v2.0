
import os
import time
import subprocess
import urllib.request
import sys

# Configuration
START_BATCH = 31
END_BATCH = 554
CHUNK_SIZE = 50 
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

def run_cmd_with_timeout(cmd, cwd=PROJECT_DIR, timeout=40):
    # Run with timeout to prevent hanging
    try:
        subprocess.run(cmd, shell=True, check=True, cwd=cwd, timeout=timeout)
        return True
    except subprocess.TimeoutExpired:
        log(f"⚠️ Command Timed Out after {timeout}s: {cmd}")
        # Try to kill it? subprocess.run usually kills if timeout expires? 
        # Actually in shell=True it might not kill the child.
        # We need to manually cleanup if needed, but Python 3.7+ usually handles it.
        return False
    except subprocess.CalledProcessError as e:
        log(f"Command failed: {e}")
        return False

def check_backend_health():
    try:
        with urllib.request.urlopen("http://localhost:8000/api/health", timeout=2) as response:
            return response.getcode() == 200
    except:
        return False

def force_kill_backend():
    log("🛑 Force Killing Backend...")
    run_cmd_quiet("pkill -9 -f uvicorn")
    time.sleep(2)

def start_backend():
    log("🔄 Starting Backend...")
    subprocess.Popen(["bash", "start_backend_strict.sh"], cwd=PROJECT_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Wait for health check
    log("Waiting for Backend to come up...")
    for _ in range(30):
        time.sleep(2)
        if check_backend_health():
            log("✅ Backend is UP.")
            return True
    log("⚠️ Backend startup timed out.")
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
        # Clean up any potential zombies
        run_cmd_quiet("pkill -9 -f uvicorn")
        
        cmd = f"{PYTHON_BIN} import_single_batch_v2.py --batch {i}"
        
        # Use timeout!
        if run_cmd_with_timeout(cmd, cwd=BACKEND_DIR, timeout=60):
            success_count += 1
        else:
            fail_count += 1
            log(f"⚠️ Batch {i} Failed or Timed Out. Skipping.")
            # Aggressive cleanup
            run_cmd_quiet("pkill -9 -f import_single_batch")
            
        if i % 10 == 0:
            log(f"  ... Progress: Batch {i} done.")
            
    log(f"Import Finished: {success_count} success, {fail_count} failed.")
    return True

def main():
    log("🚀 Auto-Pilot Analysis Started (v7 - Timeout Protection)")
    
    force_kill_backend()
    
    for i in range(START_BATCH, END_BATCH + 1, CHUNK_SIZE):
        chunk_end = min(i + CHUNK_SIZE - 1, END_BATCH)
        log(f"\n==========================================")
        log(f"=== Processing Chunk {i} to {chunk_end} ===")
        log(f"==========================================")
        
        if not run_classification_chunk(i, chunk_end):
            log("❌ Classification failed. Stopping.")
            break
            
        import_results_sequentially(i, chunk_end)
        
        # Monitor check
        try:
            run_cmd(f"{PYTHON_BIN} check_db_status.py", cwd=BACKEND_DIR)
        except:
            pass
            
        log(f"✅ Chunk {i}-{chunk_end} Complete.")
        time.sleep(2)

if __name__ == "__main__":
    main()
