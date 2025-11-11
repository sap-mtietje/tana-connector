#!/bin/bash

# Tana-Connector Background Startup Script

# Setup PATH for non-interactive shells
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.cargo/bin:$HOME/.local/bin:$PATH"

# Auto-detect project root directory (resolves symlinks, goes up to repo root)
SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || readlink "${BASH_SOURCE[0]}" 2>/dev/null || echo "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_DIR"

LOG_FILE="/tmp/tana-connector.log"
PID_FILE="/tmp/tana-connector.pid"

# Parse command line arguments
SKIP_UPDATE=true  # Default to skip for quick starts
DEV_MODE=false
SKIP_DEPS=false

for arg in "$@"; do
    case $arg in
        --update)
            SKIP_UPDATE=false
            ;;
        --skip-deps)
            SKIP_DEPS=true
            ;;
        --dev)
            DEV_MODE=true
            ;;
    esac
done

# Function to check command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to send SwiftBar notification
notify_error() {
    local title="$1"
    local body="$2"
    open -g "swiftbar://notify?plugin=tana-connector&title=$(echo "$title" | sed 's/ /%20/g')&body=$(echo "$body" | sed 's/ /%20/g')&silent=false" 2>/dev/null || true
}

notify_success() {
    local title="$1"
    local body="$2"
    open -g "swiftbar://notify?plugin=tana-connector&title=$(echo "$title" | sed 's/ /%20/g')&body=$(echo "$body" | sed 's/ /%20/g')&silent=true" 2>/dev/null || true
}

echo "Starting Tana-Connector server..." | tee "$LOG_FILE"
echo "Log file: $LOG_FILE" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

PORT=${PORT:-8000}

# Check for uv (it will manage Python version automatically based on pyproject.toml)
if ! command_exists uv; then
    echo "Error: uv not found. Install from: https://docs.astral.sh/uv/" | tee -a "$LOG_FILE"
    echo "  macOS: curl -LsSf https://astral.sh/uv/install.sh | sh" | tee -a "$LOG_FILE"
    notify_error "Missing Dependency" "uv not found. Please install it first."
    exit 1
fi

echo "Using uv to manage dependencies and Python version" | tee -a "$LOG_FILE"

# Optional: Git update
if [ "$SKIP_UPDATE" = false ] && [ -d ".git" ]; then
    echo "Updating from git..." | tee -a "$LOG_FILE"
    if git diff-index --quiet HEAD -- 2>/dev/null; then
        git pull --rebase >> "$LOG_FILE" 2>&1
    else
        echo "Warning: Uncommitted changes, skipping git pull" | tee -a "$LOG_FILE"
    fi
fi

# Optional: Sync dependencies
if [ "$SKIP_DEPS" = false ]; then
    echo "Syncing dependencies..." | tee -a "$LOG_FILE"
    if [ "$DEV_MODE" = true ]; then
        uv sync --all-extras >> "$LOG_FILE" 2>&1
    else
        uv sync >> "$LOG_FILE" 2>&1
    fi
fi

# Create necessary directories
mkdir -p "$PROJECT_DIR/auth_records"

# Start the server in background
echo "Starting server on port $PORT..." | tee -a "$LOG_FILE"
echo "---" >> "$LOG_FILE"

nohup uv run python app.py >> "$LOG_FILE" 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > "$PID_FILE"

# Wait a moment and check if it started
sleep 2

if kill -0 $SERVER_PID 2>/dev/null; then
    echo "✓ Server started successfully (PID: $SERVER_PID)" | tee -a "$LOG_FILE"
    echo "  API: http://localhost:$PORT" | tee -a "$LOG_FILE"
    echo "  Docs: http://localhost:$PORT/docs" | tee -a "$LOG_FILE"
    echo "  Health: http://localhost:$PORT/health" | tee -a "$LOG_FILE"

    # Notify user of success (silent notification)
    notify_success "Server Started" "Tana-Connector running on port $PORT"

    # Refresh SwiftBar menu
    open -g "swiftbar://refreshplugin?plugin=tana-connector.sh" 2>/dev/null || true
    exit 0
else
    echo "✗ Server failed to start. Check log: $LOG_FILE" | tee -a "$LOG_FILE"
    rm -f "$PID_FILE"

    # Notify user of failure
    notify_error "Server Failed to Start" "Check logs for details"

    # Refresh SwiftBar menu (even on failure, to show stopped state)
    open -g "swiftbar://refreshplugin?plugin=tana-connector.sh" 2>/dev/null || true
    exit 1
fi
