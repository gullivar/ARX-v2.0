import time
import requests
import subprocess
import os
import logging
import signal

# Setup Logging
logging.basicConfig(
    filename='watchdog.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BACKEND_PORT = 8000
FRONTEND_PORT = 5173
BACKEND_URL = f"http://localhost:{BACKEND_PORT}/health"
FRONTEND_URL = f"http://localhost:{FRONTEND_PORT}"

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
NPM_PATH = "/Users/joseph/.nvm/versions/node/v20.15.0/bin/npm"

# LLM Config
LLM_INTERNAL = "http://192.168.8.190:17311/api/version"
LLM_EXTERNAL = "http://106.254.248.154:17311/api/version"

def kill_port(port):
    """
    Force kill any process listening on the specified port.
    """
    try:
        # Find PID using lsof
        # -t: terse (PID only), -i:select by internet address
        result = subprocess.run(["lsof", "-t", f"-i:{port}"], capture_output=True, text=True)
        pids = result.stdout.strip().split('\n')
        
        for pid in pids:
            if pid:
                logger.warning(f"Killing process {pid} occupying port {port}")
                os.kill(int(pid), signal.SIGKILL)
                
        time.sleep(2) # Wait for OS to release port
    except Exception as e:
        logger.error(f"Error killing port {port}: {e}")

def check_service(url, name, timeout=30):
    try:
        resp = requests.get(url, timeout=timeout)
        if resp.status_code == 200:
            return True
        logger.warning(f"{name} returned status code {resp.status_code}")
        return False
    except requests.exceptions.ConnectionError:
        logger.warning(f"{name} Connection Refused")
        return False
    except requests.exceptions.Timeout:
        logger.warning(f"{name} Timeout")
        return False
    except Exception as e:
        logger.error(f"{name} Unknown Error: {e}")
        return False

def check_llm():
    try:
        requests.get(LLM_INTERNAL, timeout=2)
        return True
    except:
        try:
            requests.get(LLM_EXTERNAL, timeout=2)
            return True
        except:
            return False

def restart_backend():
    logger.warning(">>> Restarting Backend Service...")
    
    # 1. Kill any zombie process on Port 8000
    kill_port(BACKEND_PORT)
    
    # 2. Force kill remaining uvicorn (backup)
    subprocess.run("pkill -9 -f uvicorn", shell=True)
    time.sleep(1)

    # 3. Start Backend
    cmd = f"cd {BACKEND_DIR} && venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port {BACKEND_PORT} --reload --reload-exclude '*.db' --reload-exclude '*.log' >> uvicorn.log 2>&1 &"
    try:
        subprocess.Popen(cmd, shell=True)
        logger.info(f"Backend Start Command Issued: {cmd}")
    except Exception as e:
        logger.error(f"Failed to start backend: {e}")

    # 4. Wait for boot
    logger.info("Waiting for Backend to boot...")
    for i in range(10):
        time.sleep(2)
        if check_service(BACKEND_URL, "Backend"):
            logger.info("✅ Backend is ONLINE!")
            return
    
    logger.error("❌ Backend failed to start after restart attempt!")
    # We might want to read the log here to debug "Address already in use" loop
    # But kill_port should fix that.

def restart_frontend():
    logger.warning(">>> Restarting Frontend Service...")
    
    # 1. Kill Port 5173
    kill_port(FRONTEND_PORT)
    
    # 2. Kill vite
    subprocess.run("pkill -9 -f vite", shell=True)
    time.sleep(1)

    # 3. Start Frontend
    cmd = f"cd {FRONTEND_DIR} && {NPM_PATH} run dev -- --host >> frontend.log 2>&1 &"
    try:
        subprocess.Popen(cmd, shell=True)
        logger.info(f"Frontend Start Command Issued: {cmd}")
    except Exception as e:
        logger.error(f"Failed to start frontend: {e}")

def main():
    logger.info("=== Watchdog v2.0 Started (Zombie Hunter Edition) ===")
    logger.info(f"Monitoring Backend(:{BACKEND_PORT}), Frontend(:{FRONTEND_PORT}), and LLM...")
    
    while True:
        # LLM Check (Alert Only)
        if not check_llm():
            logger.error("🚨 LLM Server Unreachable! Check 192.168.8.190")

def check_deep_health():
    """
    Verify that the API is not just running, but actually returning valid data.
    """
    try:
        # Check Categories (Should verify DB connection and data seeding)
        url = f"http://localhost:{BACKEND_PORT}/api/v2/categories/"
        # V2.2: Increased timeout to 10s to prevent boot-loop when server is busy initializing
        resp = requests.get(url, timeout=10) 
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                return True
            logger.warning(f"Deep Health Check Failed: Categories empty or invalid format: {data}")
            return False
        logger.warning(f"Deep Health Check Failed: Status {resp.status_code}")
        return False
    except Exception as e:
        logger.warning(f"Deep Health Check Error: {e}")
        return False

def main():
    logger.info("=== Watchdog v2.1 Started (Deep Health Check) ===")
    logger.info(f"Monitoring Backend(:{BACKEND_PORT}), Frontend(:{FRONTEND_PORT}), LLM, and Data Integrity...")
    
    while True:
        # 1. Basic Port/Process Check
        backend_alive = check_service(BACKEND_URL, "Backend")
        frontend_alive = check_service(FRONTEND_URL, "Frontend")

        # 2. Restart if basic check fails
        if not backend_alive:
            restart_backend()
        elif not frontend_alive:
            restart_frontend()
        else:
            # 3. Deep Data Check (Only if backend appears alive)
            # If backend is up but sending garbage/empty data -> Restart might fix stuck DB session
            if not check_deep_health():
                logger.error("🚨 Backend is up but Data Check failed! Force Restarting Backend...")
                restart_backend()

        # LLM Check (Alert Only)
        if not check_llm():
            logger.error("🚨 LLM Server Unreachable! Check 192.168.8.190")

        time.sleep(10)

if __name__ == "__main__":
    main()
