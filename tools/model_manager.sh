#!/bin/bash
# EverythingSwing Model Manager
# This script manages models for LM Studio and AnythingLLM

PROJECT_ROOT="/Volumes/AI_ETS_2TB/EverythingSwing"
MODELS_DIR="${PROJECT_ROOT}/models"
LM_STUDIO_MODELS_DIR="${MODELS_DIR}/lmstudio"
ANYTHING_LLM_MODELS_DIR="${MODELS_DIR}/anythingllm"
DEFAULT_LM_STUDIO_DIR="/Volumes/Extreem SSD 2TB/LM-Studio/models"
DEFAULT_ANYTHING_LLM_DIR="${HOME}/Library/Application Support/anythingllm-desktop/storage/models"
LOG_DIR="${PROJECT_ROOT}/logs"

# Create log directory if it doesn't exist
mkdir -p "${LOG_DIR}"

# Log file with timestamp
LOG_FILE="${LOG_DIR}/model_manager_$(date +%Y%m%d_%H%M%S).log"

# Function to log messages
log_message() {
    local message="$(date +"%Y-%m-%d %H:%M:%S") - $1"
    echo "$message" | tee -a "$LOG_FILE"
}

# Create models directories if they don't exist
mkdir -p "${LM_STUDIO_MODELS_DIR}"
mkdir -p "${ANYTHING_LLM_MODELS_DIR}"

# Function to move existing models to project directory
move_lmstudio_models() {
    log_message "Moving existing LM Studio models to project directory..."
    
    if [ ! -d "$DEFAULT_LM_STUDIO_DIR" ]; then
        log_message "Custom LM Studio models directory not found at: $DEFAULT_LM_STUDIO_DIR"
        return 1
    fi
    
    # Find all model files in LM Studio directory
    find "$DEFAULT_LM_STUDIO_DIR" -type f -name "*.gguf" | while read -r model_file; do
        # Get relative path from DEFAULT_LM_STUDIO_DIR
        rel_path="${model_file#$DEFAULT_LM_STUDIO_DIR/}"
        
        # Create target path in project models directory
        target_path="${LM_STUDIO_MODELS_DIR}/${rel_path}"
        
        # Create parent directories
        mkdir -p "$(dirname "$target_path")"
        
        # Check if file already exists in target location
        if [ ! -f "$target_path" ]; then
            log_message "Moving model: $model_file -> $target_path"
            cp "$model_file" "$target_path"
        else
            log_message "Model already exists in target location: $target_path"
        fi
    done
    
    log_message "Finished moving LM Studio models."
}

# Function to move existing models to project directory
move_anythingllm_models() {
    log_message "Moving existing AnythingLLM models to project directory..."
    
    if [ ! -d "$DEFAULT_ANYTHING_LLM_DIR" ]; then
        log_message "Default AnythingLLM models directory not found. Run AnythingLLM at least once to create it."
        return 1
    fi
    
    # Find all model files in AnythingLLM directory
    find "$DEFAULT_ANYTHING_LLM_DIR" -type f -name "*.gguf" | while read -r model_file; do
        # Get relative path from DEFAULT_ANYTHING_LLM_DIR
        rel_path="${model_file#$DEFAULT_ANYTHING_LLM_DIR/}"
        
        # Create target path in project models directory
        target_path="${ANYTHING_LLM_MODELS_DIR}/${rel_path}"
        
        # Create parent directories
        mkdir -p "$(dirname "$target_path")"
        
        # Check if file already exists in target location
        if [ ! -f "$target_path" ]; then
            log_message "Moving model: $model_file -> $target_path"
            cp "$model_file" "$target_path"
        else
            log_message "Model already exists in target location: $target_path"
        fi
    done
    
    log_message "Finished moving AnythingLLM models."
}

# Function to directly configure LM Studio to use our project models directory
direct_lmstudio_config() {
    log_message "Configuring LM Studio to use the project models directory directly..."
    
    # First, ensure LM Studio CLI is available
    if ! command -v lms &> /dev/null; then
        log_message "LM Studio CLI not found. Attempting to bootstrap..."
        if [ -f "${HOME}/.lmstudio/bin/lms" ]; then
            "${HOME}/.lmstudio/bin/lms" bootstrap
            log_message "Bootstrapped LM Studio CLI. Please open a new terminal window after this script completes."
        else
            log_message "ERROR: LM Studio CLI not found at expected location. Please run LM Studio at least once."
            return 1
        fi
    fi
    
    # Import each model in our project directory to LM Studio
    log_message "Importing models to LM Studio..."
    find "${LM_STUDIO_MODELS_DIR}" -type f -name "*.gguf" | while read -r model_file; do
        log_message "Importing model: $model_file"
        lms import "$model_file" || log_message "WARNING: Failed to import $model_file"
    done
    
    # Now try to configure LM Studio to use our directory directly
    # Create a temp file to communicate with the LM Studio settings
    SETTINGS_FILE="${HOME}/.lmstudio/settings.json"
    if [ -f "$SETTINGS_FILE" ]; then
        # Create a backup
        cp "$SETTINGS_FILE" "${SETTINGS_FILE}.backup"
        
        # Update the settings file to point to our models directory
        tmp_file=$(mktemp)
        cat "$SETTINGS_FILE" | sed "s|\"modelsDirectory\": \".*\"|\"modelsDirectory\": \"${LM_STUDIO_MODELS_DIR}\"|g" > "$tmp_file"
        mv "$tmp_file" "$SETTINGS_FILE"
        
        log_message "Updated LM Studio settings to use ${LM_STUDIO_MODELS_DIR} as models directory."
        log_message "You will need to restart LM Studio for changes to take effect."
    else
        log_message "WARNING: LM Studio settings file not found at $SETTINGS_FILE"
        log_message "You will need to manually set the models directory in LM Studio:"
        log_message "1. Open LM Studio"
        log_message "2. Navigate to the 'My Models' tab"
        log_message "3. Click on the folder icon at the top"
        log_message "4. Select the directory: ${LM_STUDIO_MODELS_DIR}"
    fi
    
    log_message "Finished configuring LM Studio."
}

# Function to clean up the old dependency
cleanup_extreem_dependency() {
    log_message "Cleaning up dependency on Extreem SSD drive..."
    
    if [ -d "$DEFAULT_LM_STUDIO_DIR" ]; then
        # Instead of deleting, rename to prevent accidental data loss
        BACKUP_DIR="${DEFAULT_LM_STUDIO_DIR}_backup_complete_$(date +%Y%m%d_%H%M%S)"
        log_message "Moving original LM Studio models directory to backup: $BACKUP_DIR"
        mv "$DEFAULT_LM_STUDIO_DIR" "$BACKUP_DIR"
        
        # Create an empty directory so LM Studio doesn't complain
        mkdir -p "$DEFAULT_LM_STUDIO_DIR"
        
        # Create a README file explaining what happened
        echo "This directory was originally used for LM Studio models." > "${DEFAULT_LM_STUDIO_DIR}/README.txt"
        echo "Those models have been moved to: ${LM_STUDIO_MODELS_DIR}" >> "${DEFAULT_LM_STUDIO_DIR}/README.txt"
        echo "A complete backup was created at: ${BACKUP_DIR}" >> "${DEFAULT_LM_STUDIO_DIR}/README.txt"
        echo "This was done on: $(date)" >> "${DEFAULT_LM_STUDIO_DIR}/README.txt"
        
        log_message "Created README file explaining the migration."
    else
        log_message "LM Studio models directory not found at: $DEFAULT_LM_STUDIO_DIR"
        log_message "No cleanup needed."
    fi
    
    log_message "Finished cleanup."
}

# Function to check if paths are correct and accessible
check_paths() {
    log_message "Checking paths..."
    
    if [ ! -d "$PROJECT_ROOT" ]; then
        log_message "ERROR: Project root directory not found: $PROJECT_ROOT"
        return 1
    fi
    
    if [ ! -w "$PROJECT_ROOT" ]; then
        log_message "ERROR: Project root directory not writable: $PROJECT_ROOT"
        return 1
    fi
    
    # Check if LM Studio directory exists and is accessible
    if [ ! -d "$LM_STUDIO_MODELS_DIR" ]; then
        log_message "Creating LM Studio models directory: $LM_STUDIO_MODELS_DIR"
        mkdir -p "$LM_STUDIO_MODELS_DIR"
    fi
    
    if [ ! -w "$LM_STUDIO_MODELS_DIR" ]; then
        log_message "ERROR: LM Studio models directory not writable: $LM_STUDIO_MODELS_DIR"
        return 1
    fi
    
    log_message "Paths checked successfully."
    return 0
}

# Display usage information
show_usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  move-lmstudio      - Move existing LM Studio models to project directory"
    echo "  move-anythingllm   - Move existing AnythingLLM models to project directory"
    echo "  direct-config      - Configure LM Studio to use project models directory directly"
    echo "  cleanup            - Clean up dependency on Extreem SSD drive"
    echo "  check-paths        - Check if paths are correct and accessible"
    echo "  help               - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 move-lmstudio"
    echo "  $0 direct-config"
    echo "  $0 cleanup"
}

# Main script execution
case "$1" in
    move-lmstudio)
        check_paths && move_lmstudio_models
        ;;
    move-anythingllm)
        check_paths && move_anythingllm_models
        ;;
    direct-config)
        check_paths && direct_lmstudio_config
        ;;
    cleanup)
        check_paths && cleanup_extreem_dependency
        ;;
    check-paths)
        check_paths
        ;;
    help|--help|-h)
        show_usage
        exit 0
        ;;
    *)
        log_message "ERROR: Unknown command '$1'"
        show_usage
        exit 1
        ;;
esac

exit 0
