#!/bin/bash
set -e

PROJECT_DIR="/root/project/ARX-v2.0"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# 1. Create .env
echo "[Start] Creating .env..."
cat <<EOF > "$BACKEND_DIR/.env"
PROJECT_NAME="W-Intel v2.0"
API_V1_STR="/api/v2"
LLM_API_URL="http://106.254.248.154:17311"
# Add other defaults if needed
EOF

# 2. Backend
echo "[Start] Starting Backend..."
cd "$BACKEND_DIR"
source venv/bin/activate

# Ensure dependencies (quick check)
pip install -r requirements.txt
pip install playwright
playwright install chromium

# Run Uvicorn in background
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > uvicorn.log 2>&1 &
BACKEND_PID=$!
echo "Backend running (PID: $BACKEND_PID)"

# 3. Frontend
echo "[Start] Starting Frontend..."
cd "$FRONTEND_DIR"
# Ensure node_modules (if not already installed)
if [ ! -d "node_modules" ]; then
    npm install
fi

nohup npm run dev -- --host > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend running (PID: $FRONTEND_PID)"

echo "Services started!"
