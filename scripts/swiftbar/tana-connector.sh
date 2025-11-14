#!/bin/bash

# <xbar.title>Tana Connector</xbar.title>
# <xbar.version>v1.0</xbar.version>
# <xbar.author>Marten Tietje</xbar.author>
# <xbar.author.github>sap-mtietje</xbar.author.github>
# <xbar.desc>Minimal Tana-Connector Server Manager</xbar.desc>
# <xbar.abouturl>https://github.com/sap-mtietje/tana-connector</xbar.abouturl>
# <swiftbar.hideLastUpdated>true</swiftbar.hideLastUpdated>
# <swiftbar.hideDisablePlugin>true</swiftbar.hideDisablePlugin>
# <swiftbar.hideSwiftBar>true</swiftbar.hideSwiftBar>

# Setup PATH for non-interactive shells (needed for SwiftBar)
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.cargo/bin:$HOME/.local/bin:$PATH"

# Auto-detect project root directory (resolves symlinks, goes up to repo root)
SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || readlink "${BASH_SOURCE[0]}" 2>/dev/null || echo "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_FILE="/tmp/tana-connector.log"

# Load .env file if it exists
if [ -f "$PROJECT_DIR/.env" ]; then
    source "$PROJECT_DIR/.env" 2>/dev/null || true
fi

PORT=${PORT:-8000}

# Check if server is running
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    # Server is running
    PID=$(lsof -Pi :$PORT -sTCP:LISTEN -t)

    # Menu bar - Running
    echo ":play.circle.fill: tana | sfcolor=green"

    # Dropdown menu
    echo "---"
    echo "Running | sfimage=checkmark.circle.fill"
    echo "PID: $PID"
    echo "Port: $PORT"

    echo "---"
    echo "Stop Server | bash='$PROJECT_DIR/scripts/swiftbar/tana-stop.sh' terminal=false refresh=true sfimage=stop.circle.fill"


else
    # Server is stopped
    echo ":stop.circle.fill: tana| sfcolor=red"

    echo "---"
    echo "Stopped | sfimage=xmark.circle.fill"

    # Check if .env exists
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        echo "---"
        echo "⚠ Missing .env | sfimage=exclamationmark.triangle.fill"
        echo "---"
        echo "Run Setup | bash='$PROJECT_DIR/start.sh' terminal=true sfimage=wrench.and.screwdriver.fill"
    else
        echo "---"
        echo "Start Server | bash='$PROJECT_DIR/scripts/swiftbar/tana-start-background.sh' terminal=false refresh=true sfimage=play.circle.fill"
        echo "Start with Update | bash='$PROJECT_DIR/scripts/swiftbar/tana-start-background.sh' param1='--update' terminal=false refresh=true sfimage=arrow.down.circle.fill"
    fi
fi


echo "---"
echo "Check Status | refresh=true sfimage=arrow.clockwise"
echo "View Logs | bash='open' param1='$LOG_FILE' terminal=false sfimage=doc.text.fill"
echo "---"
echo "Open API Docs | href=http://localhost:$PORT/docs sfimage=book.fill"
