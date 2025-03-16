#!/bin/bash

# Terminal colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}==========================================${NC}"
echo -e "${YELLOW}  RecallAI - Stopping Application${NC}"
echo -e "${YELLOW}==========================================${NC}"

# Find and stop all Flask processes
PIDS=$(pgrep -f "python.*app.py")

if [ -z "$PIDS" ]; then
    echo -e "${YELLOW}No Flask application processes found running.${NC}"
    exit 0
fi

echo -e "${YELLOW}Found Flask application processes: $PIDS${NC}"

# Kill each process
for PID in $PIDS; do
    echo -e "${YELLOW}Stopping process with PID: $PID${NC}"
    kill $PID 2>/dev/null || kill -9 $PID 2>/dev/null
done

# Check if all processes are stopped
sleep 2
REMAINING=$(pgrep -f "python.*app.py")

if [ -z "$REMAINING" ]; then
    echo -e "${GREEN}All Flask application processes successfully stopped.${NC}"
else
    echo -e "${RED}Warning: Some processes could not be stopped: $REMAINING${NC}"
    echo -e "${RED}You may need to manually kill these processes.${NC}"
    exit 1
fi

# Check if any ports are still in use
for PORT in 8080 8081 8082 8083 8084 8085; do
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null; then
        PROCESS=$(lsof -Pi :$PORT -sTCP:LISTEN -t)
        echo -e "${YELLOW}Warning: Port $PORT is still in use by process: $PROCESS${NC}"
    fi
done

echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}Application shutdown complete.${NC}"
echo -e "${GREEN}==========================================${NC}" 