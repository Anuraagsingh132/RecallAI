#!/bin/bash
#
# RecallAI Main Application Script
# This script starts the RecallAI application with proper configuration
# and handles common issues like port conflicts.
#

# Terminal colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  RecallAI - Startup Script${NC}"
echo -e "${BLUE}=========================================${NC}"

# Kill any existing Flask processes
echo -e "${YELLOW}Stopping any existing Flask applications...${NC}"
pkill -f "python.*app.py" || true
sleep 1

# Function to check if a port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        return 1
    else
        return 0
    fi
}

# Try ports in sequence
DEFAULT_PORT=8080
port=$DEFAULT_PORT
MAX_PORT=8085

while ! check_port $port && [ $port -le $MAX_PORT ]; do
    echo -e "${YELLOW}Port $port is in use. Trying next port...${NC}"
    port=$((port + 1))
done

if [ $port -gt $MAX_PORT ]; then
    echo -e "${RED}Error: Could not find an available port in range $DEFAULT_PORT-$MAX_PORT${NC}"
    echo -e "${RED}Please close some applications and try again.${NC}"
    exit 1
fi

echo -e "${GREEN}Using port: $port${NC}"

# Create necessary directories
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p data/vector_store data/uploads logs

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source venv/bin/activate 2>/dev/null || true
elif [ -d "venv_rag" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source venv_rag/bin/activate 2>/dev/null || true
fi

# Set environment variables
export FLASK_APP=app.py
export DEBUG=1
export PORT=$port

# Handle command line arguments
if [ "$1" == "--debug" ]; then
    echo -e "${GREEN}Starting in debug mode with full console output...${NC}"
    echo -e "${GREEN}Access the application at: http://localhost:$port${NC}"
    # Run with console output for debugging
    python3 app.py
else
    # Run the application with logging to file
    LOG_FILE="logs/flask_$(date +%Y%m%d_%H%M%S).log"
    echo -e "${GREEN}Starting application on port $port with logging to $LOG_FILE...${NC}"
    python3 app.py > "$LOG_FILE" 2>&1 &
    
    # Get the PID of the Flask application
    PID=$!
    sleep 2
    
    # Check if the process is still running
    if ps -p $PID > /dev/null; then
        echo -e "${GREEN}==========================================${NC}"
        echo -e "${GREEN}Application started successfully!${NC}"
        echo -e "${GREEN}Access the application at: http://localhost:$port${NC}"
        echo -e "${GREEN}Process ID: $PID${NC}"
        echo -e "${GREEN}Log file: $LOG_FILE${NC}"
        echo -e "${GREEN}View logs with: tail -f $LOG_FILE${NC}"
        echo -e "${GREEN}Stop the application with: ./stop_app.sh${NC}"
        echo -e "${GREEN}==========================================${NC}"
    else
        echo -e "${RED}Error: Application failed to start. Check logs for details:${NC}"
        echo -e "${RED}tail -f $LOG_FILE${NC}"
        exit 1
    fi
fi 