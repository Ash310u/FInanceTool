#!/bin/bash

# Financial Reporting Tool - Startup Script
set -e

# Colors
C='\033[0;36m'  # Cyan
G='\033[0;32m'  # Green
Y='\033[1;33m'  # Yellow
R='\033[0;31m'  # Red
D='\033[0;90m'  # Dark gray
NC='\033[0m'    # No Color

# Config
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"
BACKEND_PORT=5000
FRONTEND_PORT=8000
BACKEND_PID_FILE="/tmp/financial-tool-backend.pid"
FRONTEND_PID_FILE="/tmp/financial-tool-frontend.pid"

# Spinner
spin() {
    local pid=$1
    local delay=0.1
    local spinstr='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    while ps -p $pid > /dev/null 2>&1; do
        local temp=${spinstr#?}
        printf " ${C}[${temp:0:1}]${NC}"
        spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

# Header
clear
echo -e "${C}"
cat << "EOF"
╔═══════════════════════════════════════════════════════╗
║                                                       ║
║   ███████╗██╗███╗   ██╗ █████╗ ███╗   ██╗ ██████╗     ║
║   ██╔════╝██║████╗  ██║██╔══██╗████╗  ██║██╔════╝     ║
║   █████╗  ██║██╔██╗ ██║███████║██╔██╗ ██║██║          ║
║   ██╔══╝  ██║██║╚██╗██║██╔══██║██║╚██╗██║██║          ║
║   ██║     ██║██║ ╚████║██║  ██║██║ ╚████║╚██████╗     ║
║   ╚═╝     ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝     ║
║                                                       ║
║              R E P O R T I N G   T O O L              ║
║                                                       ║
╚═══════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"
sleep 0.5

# System check
echo -e "${D}[$(date +%H:%M:%S)]${NC} ${C}>>>${NC} Initializing system..."
sleep 0.2

# Check dependencies
echo -e -n "${D}[$(date +%H:%M:%S)]${NC} ${C}>>>${NC} Checking dependencies..."
if ! command -v python &> /dev/null; then
    echo -e " ${R}[FAIL]${NC}"
    exit 1
fi
echo -e " ${G}[OK]${NC}"

# Setup venv
if [ ! -d "venv" ]; then
    echo -e -n "${D}[$(date +%H:%M:%S)]${NC} ${C}>>>${NC} Creating virtual environment..."
    python -m venv venv > /dev/null 2>&1
    echo -e " ${G}[OK]${NC}"
fi

# Activate venv
source venv/bin/activate > /dev/null 2>&1

# Install dependencies
if ! python -c "import flask" 2>/dev/null; then
    echo -e -n "${D}[$(date +%H:%M:%S)]${NC} ${C}>>>${NC} Installing packages..."
    pip install -q flask flask-cors pandas openpyxl numpy xlsxwriter werkzeug > /dev/null 2>&1
    echo -e " ${G}[OK]${NC}"
fi

# Generate sample data silently
if [ ! -f "backend/sample_data.xlsx" ]; then
    echo -e -n "${D}[$(date +%H:%M:%S)]${NC} ${C}>>>${NC} Generating sample dataset..."
    cd backend
    python create_sample_excel.py -n 100 > /dev/null 2>&1
    cd ..
    echo -e " ${G}[OK]${NC}"
fi

# Stop existing processes
if [ -f "$BACKEND_PID_FILE" ] || [ -f "$FRONTEND_PID_FILE" ]; then
    echo -e -n "${D}[$(date +%H:%M:%S)]${NC} ${C}>>>${NC} Cleaning up old processes..."
    [ -f "$BACKEND_PID_FILE" ] && kill $(cat "$BACKEND_PID_FILE") 2>/dev/null || true
    [ -f "$FRONTEND_PID_FILE" ] && kill $(cat "$FRONTEND_PID_FILE") 2>/dev/null || true
    rm -f "$BACKEND_PID_FILE" "$FRONTEND_PID_FILE"
    sleep 1
    echo -e " ${G}[OK]${NC}"
fi

# Start backend
echo -e -n "${D}[$(date +%H:%M:%S)]${NC} ${C}>>>${NC} Starting backend server..."
cd backend
nohup python app.py > ../backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > "$BACKEND_PID_FILE"
cd ..
sleep 2
if curl -s http://127.0.0.1:$BACKEND_PORT/api/health > /dev/null 2>&1; then
    echo -e " ${G}[ONLINE]${NC}"
else
    echo -e " ${R}[FAIL]${NC}"
    exit 1
fi

# Start frontend
echo -e -n "${D}[$(date +%H:%M:%S)]${NC} ${C}>>>${NC} Starting frontend server..."
cd frontend
nohup python -m http.server $FRONTEND_PORT > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > "$FRONTEND_PID_FILE"
cd ..
sleep 1
echo -e " ${G}[ONLINE]${NC}"

# Open browser
echo -e -n "${D}[$(date +%H:%M:%S)]${NC} ${C}>>>${NC} Launching interface..."
if command -v xdg-open > /dev/null; then
    xdg-open "http://127.0.0.1:$FRONTEND_PORT" > /dev/null 2>&1 &
elif command -v firefox > /dev/null; then
    firefox "http://127.0.0.1:$FRONTEND_PORT" > /dev/null 2>&1 &
elif command -v chromium > /dev/null; then
    chromium "http://127.0.0.1:$FRONTEND_PORT" > /dev/null 2>&1 &
fi
sleep 1
echo -e " ${G}[OK]${NC}"

echo ""
echo -e "${G}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${G}║                  SYSTEM ONLINE                        ║${NC}"
echo -e "${G}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${C}  ►${NC} Frontend:  ${Y}http://127.0.0.1:$FRONTEND_PORT${NC}"
echo -e "${C}  ►${NC} Backend:   ${Y}http://127.0.0.1:$BACKEND_PORT${NC}"
echo -e "${C}  ►${NC} Sample:    ${D}backend/sample_data.xlsx${NC}"
echo ""
echo -e "${D}  Press ${Y}Ctrl+C${D} to terminate${NC}"
echo ""

# Cleanup handler
cleanup() {
    echo ""
    echo -e "${D}[$(date +%H:%M:%S)]${NC} ${Y}>>>${NC} Shutting down..."
    [ -f "$BACKEND_PID_FILE" ] && kill $(cat "$BACKEND_PID_FILE") 2>/dev/null || true
    [ -f "$FRONTEND_PID_FILE" ] && kill $(cat "$FRONTEND_PID_FILE") 2>/dev/null || true
    rm -f "$BACKEND_PID_FILE" "$FRONTEND_PID_FILE"
    echo -e "${D}[$(date +%H:%M:%S)]${NC} ${R}>>>${NC} System offline"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Keep running
while true; do
    sleep 1
done
