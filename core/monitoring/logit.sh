#!/bin/bash
# Monitor and analyze Cursor agent actions for the EverythingSwing project

# Configuration
LOGS_DIR="/Volumes/AI_ETS_2TB/EverythingSwing/logs"
TASKS_DIR="/Volumes/AI_ETS_2TB/EverythingSwing/tasks"
PERPLEXITY_SPACE_ID="z1qAo2PYTrqykFKd_GurNg"
CONFIG_FILE="${LOGS_DIR}/.logit_config"
MONITOR_PID_FILE="${LOGS_DIR}/.logit_monitor.pid"

# Create required directories
mkdir -p "$LOGS_DIR" "$TASKS_DIR"

# Display help information
show_help() {
    echo "Usage: logit [OPTIONS]"
    echo ""
    echo "Monitor and analyze Cursor agent actions for the EverythingSwing project."
    echo ""
    echo "Options:"
    echo "  -h, -help         Show this help message"
    echo "  -s, -start        Start monitoring (default if no options given)"
    echo "  -x, -stop         Stop monitoring"
    echo "  -a, -analyze      Analyze recent actions without starting monitoring"
    echo "  -c, -config       Configure Perplexity API settings"
    echo "  -l, -list         List recent recommendations"
    echo "  -r NUM, -rev NUM  Request revisions to recommendation number NUM"
    echo "  -p NUM, -appr NUM Approve recommendation number NUM"
    echo ""
    echo "Examples:"
    echo "  logit             Start monitoring and analyze recent actions"
    echo "  logit -x          Stop monitoring"
    echo "  logit -p 3        Approve recommendation #3"
}

# Start the monitoring process
start_monitoring() {
    # Check if already running
    if [[ -f "$MONITOR_PID_FILE" ]]; then
        pid=$(cat "$MONITOR_PID_FILE")
        if ps -p "$pid" > /dev/null; then
            echo "Monitoring already running (PID: $pid)"
            return 0
        else
            echo "Previous monitoring process died, restarting..."
            rm -f "$MONITOR_PID_FILE"
        fi
    fi
    
    # Start background process to monitor Cursor events
    echo "Starting Cursor monitoring..."
    nohup cursor-cli monitor --events=file_write,cmd_exec,error_throw 2>&1 | \
    while read -r line; do
        timestamp=$(date "+%Y-%m-%d %H:%M:%S")
        echo "[$timestamp] $line" >> "$LOGS_DIR/cursor_actions.log"
    done &
    
    # Save PID for later reference
    echo $! > "$MONITOR_PID_FILE"
    echo "Monitoring started successfully (PID: $(cat "$MONITOR_PID_FILE"))"
    
    # Run initial analysis
    analyze_actions
}

# Stop the monitoring process
stop_monitoring() {
    if [[ -f "$MONITOR_PID_FILE" ]]; then
        pid=$(cat "$MONITOR_PID_FILE")
        if ps -p "$pid" > /dev/null; then
            kill "$pid"
            echo "Monitoring stopped (PID: $pid)"
        else
            echo "No active monitoring process found"
        fi
        rm -f "$MONITOR_PID_FILE"
    else
        echo "No monitoring process found"
    fi
}

# Send logged actions to Perplexity for analysis
analyze_actions() {
    if [[ ! -f "$LOGS_DIR/cursor_actions.log" ]]; then
        echo "No action log found to analyze"
        return 1
    fi
    
    echo "Analyzing recent Cursor actions..."
    python3 "$LOGS_DIR/../core/monitoring/perplexity_analyzer.py" analyze
}

# Configure API settings
configure_settings() {
    read -p "Enter your Perplexity API key: " api_key
    read -p "Perplexity Space ID [$PERPLEXITY_SPACE_ID]: " space_id
    space_id=${space_id:-$PERPLEXITY_SPACE_ID}
    
    mkdir -p "$(dirname "$CONFIG_FILE")"
    echo "PERPLEXITY_API_KEY=\"$api_key\"" > "$CONFIG_FILE"
    echo "PERPLEXITY_SPACE_ID=\"$space_id\"" >> "$CONFIG_FILE"
    echo "Configuration saved."
}

# Approve a recommendation
approve_recommendation() {
    recommendation_num=$1
    echo "Approving recommendation #$recommendation_num..."
    python3 "$LOGS_DIR/../core/monitoring/perplexity_analyzer.py" approve "$recommendation_num"
}

# Request revision for a recommendation
request_revision() {
    recommendation_num=$1
    echo "Requesting revision for recommendation #$recommendation_num..."
    python3 "$LOGS_DIR/../core/monitoring/perplexity_analyzer.py" revise "$recommendation_num"
}

# Main command processing
if [[ $# -eq 0 ]]; then
    start_monitoring
else
    case "$1" in
        -h|-help)
            show_help
            ;;
        -s|-start)
            start_monitoring
            ;;
        -x|-stop)
            stop_monitoring
            ;;
        -a|-analyze)
            analyze_actions
            ;;
        -c|-config)
            configure_settings
            ;;
        -l|-list)
            find "$LOGS_DIR" -name "recommendation_*.md" -type f | xargs ls -lt | head -n 5
            ;;
        -p|-appr)
            if [[ -n "$2" && "$2" =~ ^[0-9]+$ ]]; then
                approve_recommendation "$2"
            else
                echo "Error: -p/-appr requires a recommendation number"
                exit 1
            fi
            ;;
        -r|-rev)
            if [[ -n "$2" && "$2" =~ ^[0-9]+$ ]]; then
                request_revision "$2"
            else
                echo "Error: -r/-rev requires a recommendation number"
                exit 1
            fi
            ;;
        *)
            echo "Unknown option: $1"
            echo "Run 'logit -h' for help"
            exit 1
            ;;
    esac
fi
