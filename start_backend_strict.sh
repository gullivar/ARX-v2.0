#!/bin/bash
cd /root/project/ARX-v2.0/backend
pkill -f uvicorn
# Use absolute path to python in venv
./venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > uvicorn.log 2>&1 &
echo "Backend started."
