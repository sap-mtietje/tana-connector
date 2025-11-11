#!/bin/bash

# Tana-Connector Stop Script
# Stops the Tana-Connector server gracefully

# Setup PATH for non-interactive shells (needed for SwiftBar)
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.cargo/bin:$HOME/.local/bin:$PATH"

# Auto-detect project root directory (resolves symlinks, goes up to repo root)
SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || readlink "${BASH_SOURCE[0]}" 2>/dev/null || echo "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_DIR"

# Function to send SwiftBar notification
notify_info() {
    local title="$1"
    local body="$2"
    open -g "swiftbar://notify?plugin=tana-connector&title=$(echo "$title" | sed 's/ /%20/g')&body=$(echo "$body" | sed 's/ /%20/g')&silent=true" 2>/dev/null || true
}

PORT=${PORT:-8000}
PID_FILE="/tmp/tana-connector.pid"

echo "Stopping Tana-Connector server..."

# Try to find process by port
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    PID=$(lsof -Pi :$PORT -sTCP:LISTEN -t)
    echo "Found server process: $PID"

    # Try graceful shutdown first (SIGTERM)
    kill -TERM $PID 2>/dev/null

    # Wait up to 10 seconds for graceful shutdown
    for i in {1..10}; do
        if ! kill -0 $PID 2>/dev/null; then
            echo "✓ Server stopped successfully"
            rm -f "$PID_FILE"

            # Notify user
            notify_info "Server Stopped" "Tana-Connector has been stopped"

            # Refresh SwiftBar menu
            open -g "swiftbar://refreshplugin?plugin=tana-connector.sh" 2>/dev/null || true
            exit 0
        fi
        sleep 1
    done

    # Force kill if still running
    echo "Forcing shutdown..."
    kill -9 $PID 2>/dev/null
    rm -f "$PID_FILE"
    echo "✓ Server forcefully stopped"

    # Notify user
    notify_info "Server Stopped" "Tana-Connector has been stopped"

    # Refresh SwiftBar menu
    open -g "swiftbar://refreshplugin?plugin=tana-connector.sh" 2>/dev/null || true
    exit 0
else
    echo "Server is not running"
    rm -f "$PID_FILE"

    # Refresh SwiftBar menu
    open -g "swiftbar://refreshplugin?plugin=tana-connector.sh" 2>/dev/null || true
    exit 0
fi
