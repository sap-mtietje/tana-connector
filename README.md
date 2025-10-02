# Tana-Connector

A local FastAPI server that enables integration between [Tana](https://tana.inc) and Microsoft Graph API.

## Features

- 📅 Fetch Outlook calendar events and paste into Tana
- ✉️ Draft emails based on Tana content
- 🔄 Dual format support: JSON and Tana Paste
- 🔐 Secure MSAL authentication with persistent tokens

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
python app.py

# Or directly with uvicorn
uvicorn app.main:app --reload
```

The server will start at `http://localhost:8000`

- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`


## API Endpoints

### Health

- `GET /` - Root endpoint
- `GET /health` - Health check

### Events (EventLink Compatible)

- `GET /events.json` - Get calendar events in JSON format
- `GET /events.tana` - Get calendar events in Tana Paste format

**Examples:**

```bash
# Get today's events in Tana format
curl "http://localhost:8000/events.tana"

# Get next 7 days, exclude Status and Availability fields
curl "http://localhost:8000/events.tana?offset=7&filterField=Status,Availability"

# Get confirmed meetings only with custom tag
curl "http://localhost:8000/events.tana?filterStatus=Confirmed&tag=work"
```

**Query Parameters:**
- `date` - Specific date (YYYY-MM-DD, default: today)
- `offset` - Number of days to fetch (default: 1)
- `tag` - Custom tag for Tana output (default: meeting)
- `timingField` - Custom timing field name (default: Timing)
- `filterField` - Comma-separated fields to exclude
- `filterTitle` - Filter by event title
- `filterAttendee` - Filter by attendee name
- `filterStatus` - Filter by status (Confirmed, Tentative, etc)
- `filterAllDay` - Filter all-day events (true/false)
- `truncate` - Remove video call links (true/false)

See `docs/EVENTS_ENDPOINT.md` for full documentation.

## Authentication

On first run, the server will open a browser for Microsoft authentication. The authentication token is cached securely in your OS keychain, so subsequent runs won't require re-authentication.

## License

MIT


