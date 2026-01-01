#!/bin/bash
# ----------------------------------------------------------------------
# Stop All Pipelines (Watchdog, Backend, Frontend)
# ----------------------------------------------------------------------

echo "[end.sh] Stopping Services..."

echo "[end.sh] Stopping Backend (Uvicorn)..."
pkill -f "uvicorn app.main:app"

echo "[end.sh] Stopping Frontend (Vite)..."
pkill -f "vite"

echo "[end.sh] All pipelines and services have been stopped."
