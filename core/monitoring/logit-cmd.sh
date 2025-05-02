#!/bin/bash
# Shortcut command for the logit monitoring system

# Configure paths
LOGS_DIR="/Volumes/AI_ETS_2TB/EverythingSwing/logs"
DOCKER_IMAGE="everythingswing"

# Create required directories
mkdir -p "$LOGS_DIR"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "Error: Docker is not running. Please start Docker Desktop first."
  exit 1
fi

# Helper functions for commands
logit_help() {
  docker run --rm -v "$LOGS_DIR:/app/logs" $DOCKER_IMAGE python core/monitoring/logit.py -h
}

logit_start() {
  docker run -d --name everythingswing-logit \
    -v "$LOGS_DIR:/app/logs" \
    -v "/Volumes/AI_ETS_2TB/EverythingSwing/tasks:/app/tasks" \
    -e PERPLEXITY_API_KEY="$PERPLEXITY_API_KEY" \
    $DOCKER_IMAGE python core/monitoring/logit.py -s
}

logit_analyze() {
  docker run --rm \
    -v "$LOGS_DIR:/app/logs" \
    -v "/Volumes/AI_ETS_2TB/EverythingSwing/tasks:/app/tasks" \
    -e PERPLEXITY_API_KEY="$PERPLEXITY_API_KEY" \
    $DOCKER_IMAGE python core/monitoring/logit.py -a
}

logit_approve() {
  docker run --rm \
    -v "$LOGS_DIR:/app/logs" \
    -v "/Volumes/AI_ETS_2TB/EverythingSwing/tasks:/app/tasks" \
    -e PERPLEXITY_API_KEY="$PERPLEXITY_API_KEY" \
    $DOCKER_IMAGE python core/monitoring/logit.py -p "$1"
}

logit_revise() {
  docker run --rm -it \
    -v "$LOGS_DIR:/app/logs" \
    -v "/Volumes/AI_ETS_2TB/EverythingSwing/tasks:/app/tasks" \
    -e PERPLEXITY_API_KEY="$PERPLEXITY_API_KEY" \
    $DOCKER_IMAGE python core/monitoring/logit.py -r "$1" "$2"
}

# Command parsing
case "$1" in
  ""|"-s"|"-start")
    logit_start
    ;;
  "-h"|"-help"|"--help")
    logit_help
    ;;
  "-a"|"-analyze")
    logit_analyze
    ;;
  "-p"|"-appr")
    if [ -z "$2" ]; then
      echo "Error: Please specify a recommendation number to approve"
      exit 1
    fi
    logit_approve "$2"
    ;;
  "-r"|"-rev")
    if [ -z "$2" ]; then
      echo "Error: Please specify a recommendation number to revise"
      exit 1
    fi
    logit_revise "$2" "$3"
    ;;
  *)
    echo "Unknown command: $1"
    echo "Run 'logit -h' for help"
    exit 1
    ;;
esac
