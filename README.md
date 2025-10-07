# Tana-Connector

A local FastAPI server that enables integration between [Tana](https://tana.inc) and Microsoft Graph API.

## Features

- 📅 Fetch Outlook calendar events and paste into Tana
- ✉️ Draft emails based on Tana content


## Quick Start

Use the startup script that handles all prerequisites:

```bash
./start.sh
```


## Setup

1. **Install dependencies** (using uv):
   ```bash
   uv sync
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your Azure AD credentials
   ```

3. **Azure AD Setup**:
   - Go to [Azure Portal](https://portal.azure.com)
   - Navigate to "App registrations" → "New registration"
   - Set redirect URI: `http://localhost:8000` (or your chosen port)
   - Copy CLIENT_ID and TENANT_ID to `.env`
   - Grant API permissions:
     - `Calendars.Read`, `Calendars.ReadWrite`
     - `Mail.Read`, `Mail.Send`

## Running the Server

```bash
# Using the entry point
uv run app.py
```

The server will start at `http://localhost:8000`

- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`


## Authentication

On first run, the server will open a browser for Microsoft authentication. The authentication token is cached securely in your OS keychain, so subsequent runs won't require re-authentication.

## Testing

### Running Tests

```bash
# Install dev dependencies
uv sync --all-extras

# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=app --cov-report=html

# Run only unit tests
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration

# Run specific test file
uv run pytest tests/test_date_utils.py
```

## Project Structure

```
tana-connector/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration management
│   ├── routers/                # API endpoints
│   ├── services/               # Business logic (auth, Graph API)
│   ├── models/                 # Pydantic models
│   └── utils/                  # Utilities (Tana formatting)
├── docs/
│   └── features/               # Feature specifications
├── app.py                      # Entry point
└── .env.example                # Environment variables template
```
