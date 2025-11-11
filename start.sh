#!/bin/bash

# Tana-Connector Startup Script

set -e  # Exit on error

# Always run from the directory where this script lives
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Parse command line arguments
SKIP_UPDATE=false
DEV_MODE=false
SKIP_DEPS=false

for arg in "$@"; do
    case $arg in
        --skip-update)
            SKIP_UPDATE=true
            shift
            ;;
        --skip-deps)
            SKIP_DEPS=true
            shift
            ;;
        --dev)
            DEV_MODE=true
            shift
            ;;
        --help|-h)
            echo "Tana-Connector Startup Script"
            echo ""
            echo "Usage: ./start.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --skip-update    Skip git pull (faster startup)"
            echo "  --skip-deps      Skip dependency sync"
            echo "  --dev            Install dev dependencies"
            echo "  --help, -h       Show this help message"
            echo ""
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $arg${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Function to print colored output
print_step() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to check command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Tana-Connector Startup Script       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# 1. Check Python version
print_step "Checking Python version..."
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
        print_success "Python $PYTHON_VERSION (requires >=3.11)"
    else
        print_error "Python 3.11 or higher is required. Found: $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

# 2. Check and install uv
print_step "Checking for uv package manager..."
if command_exists uv; then
    UV_VERSION=$(uv --version | cut -d' ' -f2)
    print_success "uv is installed (version $UV_VERSION)"
else
    print_warning "uv is not installed. Installing..."
    if command_exists curl; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
        # Add uv to PATH for current session
        export PATH="$HOME/.cargo/bin:$PATH"

        if command_exists uv; then
            print_success "uv installed successfully"
        else
            print_error "Failed to install uv. Please install manually: https://docs.astral.sh/uv/"
            exit 1
        fi
    else
        print_error "curl is not available. Please install uv manually: https://docs.astral.sh/uv/"
        exit 1
    fi
fi

# 3. Check if we're in a git repository
print_step "Checking git repository..."
if [ ! -d ".git" ]; then
    print_warning "Not in a git repository. Skipping git operations."
    SKIP_UPDATE=true
else
    print_success "Git repository found"
fi

# 4. Pull latest changes
if [ "$SKIP_UPDATE" = false ]; then
    print_step "Pulling latest changes from git..."

    # Check if there are uncommitted changes
    if ! git diff-index --quiet HEAD -- 2>/dev/null; then
        print_warning "You have uncommitted changes. Skipping git pull."
        read -p "Do you want to stash your changes and pull? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git stash
            git pull --rebase
            print_success "Changes pulled and your work was stashed"
            print_warning "Don't forget to run 'git stash pop' to restore your changes"
        else
            print_warning "Continuing without updating..."
        fi
    else
        # Get current branch
        CURRENT_BRANCH=$(git branch --show-current)
        print_step "Pulling from branch: $CURRENT_BRANCH"

        if git pull --rebase; then
            print_success "Repository updated successfully"
        else
            print_error "Failed to pull changes. Please resolve conflicts manually."
            exit 1
        fi
    fi
else
    print_warning "Skipping git update (--skip-update flag used)"
fi

# 5. Install/sync dependencies
if [ "$SKIP_DEPS" = false ]; then
    print_step "Syncing dependencies..."
    if [ "$DEV_MODE" = true ]; then
        print_step "Installing with dev dependencies..."
        uv sync --all-extras
    else
        uv sync
    fi
    print_success "Dependencies synced"
else
    print_warning "Skipping dependency sync (--skip-deps flag used)"
fi

# 6. Create necessary directories
print_step "Checking directory structure..."
if [ ! -d "auth_records" ]; then
    mkdir -p auth_records
    print_success "Created auth_records directory"
else
    print_success "Directory structure OK"
fi

# 7. Handle .env file
print_step "Checking .env configuration..."
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating template..."
    cat > .env << 'EOF'
# Microsoft Azure AD Configuration
CLIENT_ID=your_client_id_here
TENANT_ID=your_tenant_id_here

# Server Configuration (optional)
HOST=0.0.0.0
PORT=8000
DEBUG=true
EOF
    print_error ".env file created with template. Please edit it with your Azure AD credentials:"
    read -p "Press Enter after configuring .env to continue, or Ctrl+C to exit..."
fi

# 8. Validate .env file
print_step "Validating .env configuration..."
if [ -f ".env" ]; then
    source .env 2>/dev/null || true

    if [ -z "$CLIENT_ID" ] || [ "$CLIENT_ID" = "your_client_id_here" ]; then
        print_error "CLIENT_ID is not set in .env file. Please configure it before starting."
        exit 1
    fi

    if [ -z "$TENANT_ID" ] || [ "$TENANT_ID" = "your_tenant_id_here" ]; then
        print_error "TENANT_ID is not set in .env file. Please configure it before starting."
        exit 1
    fi

    print_success "Configuration validated"
else
    print_error ".env file not found"
    exit 1
fi

# 9. Check if port is available
print_step "Checking if port ${PORT:-8000} is available..."
if command_exists lsof; then
    if lsof -Pi :${PORT:-8000} -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Port ${PORT:-8000} is already in use"
        read -p "Do you want to continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_error "Startup cancelled"
            exit 1
        fi
    else
        print_success "Port ${PORT:-8000} is available"
    fi
else
    print_warning "lsof not available, skipping port check"
fi

# 10. Start the server
echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Starting Tana-Connector Server      ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
print_step "Server will be available at:"
echo -e "  • API: ${BLUE}http://localhost:${PORT:-8000}${NC}"
echo -e "  • Docs: ${BLUE}http://localhost:${PORT:-8000}/docs${NC}"
echo -e "  • Health: ${BLUE}http://localhost:${PORT:-8000}/health${NC}"
echo ""
print_step "Press Ctrl+C to stop the server"
echo ""

# Start the server
if [ "$DEV_MODE" = true ]; then
    uv run python app.py
else
    uv run python app.py
fi
