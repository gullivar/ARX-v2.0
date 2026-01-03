#!/bin/bash
PROJECT_DIR="/root/project/ARX-v2.0"
BACKEND_DIR="$PROJECT_DIR/backend"

cd "$BACKEND_DIR"
source venv/bin/activate
pip install uvicorn

# Restart Backend
pkill -f uvicorn
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > uvicorn.log 2>&1 &
echo "Backend Restarted with uvicorn installed."
