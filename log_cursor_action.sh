# COMPLETE REPLACEMENT FOR log_cursor_action.sh
#!/bin/bash
mkdir -p ./logs
echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> ./logs/cursor_actions.log
