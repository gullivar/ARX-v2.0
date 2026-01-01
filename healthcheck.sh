#!/bin/bash

# Healthcheck script for systemd or cron monitoring
# Usage: ./healthcheck.sh

BACKEND_URL="http://localhost:8000/api/v2/pipeline/health"
FRONTEND_URL="http://localhost:5173"

# Check backend health
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL" --max-time 5)

if [ "$BACKEND_STATUS" != "200" ]; then
    echo "[$(date)] Backend health check FAILED (HTTP $BACKEND_STATUS)"
    
    # Auto-restart if configured
    if [ "$AUTO_RESTART" = "true" ]; then
        echo "[$(date)] Auto-restarting services..."
        cd /Users/joseph/Dev_project/07.ARX/v2.0_new
        ./end.sh
        sleep 3
        ./start.sh
        echo "[$(date)] Services restarted"
    fi
    exit 1
fi

# Check frontend
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL" --max-time 5)

if [ "$FRONTEND_STATUS" != "200" ]; then
    echo "[$(date)] Frontend health check FAILED (HTTP $FRONTEND_STATUS)"
    exit 1
fi

echo "[$(date)] All services healthy (Backend: $BACKEND_STATUS, Frontend: $FRONTEND_STATUS)"
exit 0
