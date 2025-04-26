#!/bin/bash

# Set project root to current directory if not already set
if [ -z "$PROJECT_ROOT" ]; then
    PROJECT_ROOT="$(pwd)"
fi

# Create logs directory if it doesn't exist
LOGS_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOGS_DIR"

# Set log path with proper permissions
LOG_PATH="$LOGS_DIR/cursor-actions-$(date +%Y%m%d).log"
touch "$LOG_PATH"
chmod 644 "$LOG_PATH"

echo "Starting cursor monitor. Logging to $LOG_PATH"

# Run the cursor monitor with error handling
cursor-cli monitor --events=file_write,cmd_exec,error_throw 2>&1 | \
jq -c --unbuffered '. | {timestamp: (now|strflocaltime("%Y-%m-%dT%H:%M:%S")), type: .event, details: .payload}' 2>/dev/null | \
tee -a "$LOG_PATH" || {
    echo "Error: Cursor monitor failed. Check if cursor-cli and jq are installed." >&2
    exit 1
}
