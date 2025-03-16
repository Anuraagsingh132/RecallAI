#!/bin/bash

# Terminal colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default alt port
ALT_PORT=8081

# Check if port is provided as argument
if [ $# -eq 1 ]; then
    if [[ $1 =~ ^[0-9]+$ ]] && [ $1 -gt 1024 ] && [ $1 -lt 65535 ]; then
        ALT_PORT=$1
    else
        echo -e "${RED}Invalid port number: $1${NC}"
        echo -e "${YELLOW}Usage: ./run_alt_port.sh [port]${NC}"
        echo -e "${YELLOW}Where port is a number between 1025 and 65534${NC}"
        echo -e "${YELLOW}Using default port: $ALT_PORT${NC}"
    fi
fi

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}  RecallAI - Alternative Port Startup${NC}"
echo -e "${BLUE}==========================================${NC}"

# Kill any existing Flask processes
echo -e "${YELLOW}Stopping any existing Flask applications...${NC}"
pkill -f "python.*app.py" || true
sleep 1

# Check if the alternative port is available
if lsof -Pi :$ALT_PORT -sTCP:LISTEN -t >/dev/null; then
    echo -e "${RED}Error: Port $ALT_PORT is already in use.${NC}"
    echo -e "${RED}Please specify a different port or close the application using that port.${NC}"
    exit 1
fi

echo -e "${GREEN}Using port: $ALT_PORT${NC}"

# Set environment variables
export FLASK_APP=app.py
export DEBUG=1
export PORT=$ALT_PORT

# Create log directory if it doesn't exist
mkdir -p logs

# Start the Flask application
LOG_FILE="logs/flask_port${ALT_PORT}_$(date +%Y%m%d_%H%M%S).log"
echo -e "${GREEN}Starting application on port $ALT_PORT with logging to $LOG_FILE...${NC}"
python3 app.py > "$LOG_FILE" 2>&1 &

# Get the PID of the Flask application
PID=$!
sleep 2

# Check if the process is still running
if ps -p $PID > /dev/null; then
    echo -e "${GREEN}==========================================${NC}"
    echo -e "${GREEN}Application started successfully!${NC}"
    echo -e "${GREEN}Access the application at: http://localhost:$ALT_PORT${NC}"
    echo -e "${GREEN}Process ID: $PID${NC}"
    echo -e "${GREEN}Log file: $LOG_FILE${NC}"
    echo -e "${GREEN}View logs with: tail -f $LOG_FILE${NC}"
    echo -e "${GREEN}Stop the application with: kill $PID${NC}"
    echo -e "${GREEN}==========================================${NC}"
else
    echo -e "${RED}Error: Application failed to start. Check logs for details:${NC}"
    echo -e "${RED}tail -f $LOG_FILE${NC}"
    exit 1
fi 