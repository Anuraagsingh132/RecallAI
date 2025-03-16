#!/bin/bash
#
# RecallAI Log Cleanup Script
# This script cleans up old log files but keeps the most recent ones.
#

# Terminal colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}  RecallAI - Log Cleanup Script${NC}"
echo -e "${BLUE}==========================================${NC}"

# Check if logs directory exists
if [ ! -d "logs" ]; then
    echo -e "${YELLOW}No logs directory found. Nothing to clean up.${NC}"
    exit 0
fi

# Count the number of log files
LOG_COUNT=$(find logs -name "*.log" | wc -l)

if [ $LOG_COUNT -eq 0 ]; then
    echo -e "${YELLOW}No log files found. Nothing to clean up.${NC}"
    exit 0
fi

echo -e "${YELLOW}Found $LOG_COUNT log files.${NC}"

# If there are more than 5 log files, keep only the 3 most recent ones
if [ $LOG_COUNT -gt 5 ]; then
    echo -e "${YELLOW}Cleaning up old log files, keeping the 3 most recent...${NC}"
    
    # List all log files sorted by modification time (oldest first)
    # Delete all but the 3 most recent
    find logs -name "*.log" -type f -printf "%T@ %p\n" | sort -n | head -n $(($LOG_COUNT - 3)) | cut -d' ' -f2- | xargs rm -f
    
    NEW_COUNT=$(find logs -name "*.log" | wc -l)
    echo -e "${GREEN}Cleanup complete. Removed $(($LOG_COUNT - $NEW_COUNT)) old log files.${NC}"
    echo -e "${GREEN}Remaining log files: $NEW_COUNT${NC}"
else
    echo -e "${GREEN}Only $LOG_COUNT log files found. No cleanup needed.${NC}"
fi

echo -e "${GREEN}==========================================${NC}" 