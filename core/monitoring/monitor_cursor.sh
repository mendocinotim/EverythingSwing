# COMPLETE REPLACEMENT FOR monitor_cursor.sh
#!/bin/bash
LOG_DIR="/Volumes/AI_ETS_2TB/EverythingSwing/logs"
mkdir -p "$LOG_DIR"

# Monitor Cursor actions and log with timestamps
cursor-cli monitor --events=file_write,cmd_exec,error_throw 2>&1 | while read -r action
do
    TIMESTAMP=$(date +%Y%m%d-%H%M%S)
    echo "[$TIMESTAMP] $action" >> "$LOG_DIR/cursor_actions.log"
    
    # Send to Perplexity Space analysis
    curl -X POST "https://api.perplexity.ai/spaces/v1/z1qAo2PYTrqykFKd_GurNg/ingest" \
        -H "Authorization: Bearer $PERPLEXITY_API_KEY" \
        -d "{\"action\":\"$action\",\"context\":{\"project\":\"EverythingSwing\"}}"
done
