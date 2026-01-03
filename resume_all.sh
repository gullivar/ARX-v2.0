#!/bin/bash
# resume_all.sh
# 1. Kill any existing python processes to ensure a clean slate
echo "🔪 Killing existing Python processes..."
pkill -f "auto_monitor"
pkill -f "run_priority_crawl"
pkill -f "import_single_batch"
pkill -f "process_batch_llm"

# 2. Enable SQLite WAL mode (Write-Ahead Logging) for better concurrency
echo "🛠️  Enabling WAL mode for SQLite..."
sqlite3 /root/project/ARX-v2.0/backend/w_intel.db "PRAGMA journal_mode=WAL;"

# 3. Clean up lock files if any
echo "🧹 Cleaning up ChromaDB locks..."
rm -rf /root/project/ARX-v2.0/backend/chroma_db/*.lock

# 4. Start Auto-Pilot (Restoration)
echo "🚀 Starting Auto-Pilot v7..."
cd /root/project/ARX-v2.0
nohup python3 -u auto_monitor_v7.py > auto_monitor_v7.log 2>&1 &
echo "   PID: $!"

# 5. Start Priority Crawler (New Data)
echo "🚀 Starting Priority Crawler..."
cd /root/project/ARX-v2.0/backend
nohup ./venv/bin/python3 run_priority_crawl.py > crawl_priority.log 2>&1 &
echo "   PID: $!"

echo "✅ All systems resumed!"
