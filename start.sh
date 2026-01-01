#!/bin/bash
# ----------------------------------------------------------------------
# Start All Pipelines (Backend + Frontend)
# ----------------------------------------------------------------------

# Ensure we are in the script's directory (v2.0_new)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR" || exit

echo "[start.sh] Starting Backend Service..."

# Detect Python interpreter (Prefer venv)
if [ -f "backend/venv/bin/python3" ]; then
    PY_CMD="$SCRIPT_DIR/backend/venv/bin/python3"
else
    PY_CMD="python3"
fi

echo "[start.sh] Using Python: $PY_CMD"

# Start Backend
cd backend
nohup $PY_CMD -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-exclude '*.db' --reload-exclude '*.log' > uvicorn.log 2>&1 &
BACKEND_PID=$!
cd ..

echo "[start.sh] Backend started with PID: $BACKEND_PID"

echo "[start.sh] Starting Frontend Service..."
cd frontend
nohup npm run dev -- --host > frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo "[start.sh] Frontend started with PID: $FRONTEND_PID"
echo "[start.sh] Services Check:"
echo "  Backend Log: backend/uvicorn.log"
echo "  Frontend Log: frontend/frontend.log"

