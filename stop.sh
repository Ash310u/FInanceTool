#!/bin/bash

# Financial Reporting Tool - Shutdown Script

# Colors
C='\033[0;36m'
R='\033[0;31m'
D='\033[0;90m'
NC='\033[0m'

BACKEND_PID_FILE="/tmp/financial-tool-backend.pid"
FRONTEND_PID_FILE="/tmp/financial-tool-frontend.pid"

echo ""
echo -e "${D}[$(date +%H:%M:%S)]${NC} ${R}>>>${NC} Initiating shutdown sequence..."

# Stop backend
if [ -f "$BACKEND_PID_FILE" ]; then
    BACKEND_PID=$(cat "$BACKEND_PID_FILE")
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo -e -n "${D}[$(date +%H:%M:%S)]${NC} ${C}>>>${NC} Terminating backend..."
        kill $BACKEND_PID 2>/dev/null || true
        sleep 1
        echo -e " ${R}[OFFLINE]${NC}"
    fi
    rm -f "$BACKEND_PID_FILE"
fi

# Stop frontend
if [ -f "$FRONTEND_PID_FILE" ]; then
    FRONTEND_PID=$(cat "$FRONTEND_PID_FILE")
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -e -n "${D}[$(date +%H:%M:%S)]${NC} ${C}>>>${NC} Terminating frontend..."
        kill $FRONTEND_PID 2>/dev/null || true
        sleep 1
        echo -e " ${R}[OFFLINE]${NC}"
    fi
    rm -f "$FRONTEND_PID_FILE"
fi

# Force kill if needed
pkill -f "python app.py" 2>/dev/null || true
pkill -f "http.server 8000" 2>/dev/null || true

echo -e "${D}[$(date +%H:%M:%S)]${NC} ${R}>>>${NC} System shutdown complete"
echo ""
