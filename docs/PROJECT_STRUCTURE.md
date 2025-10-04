# Project Structure Overview

## Directory Layout

```
tana-connector/
├── app/                          # Main application code
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # FastAPI app entry point
│   ├── config.py                # Configuration management
│   │
│   ├── routers/                 # API endpoints (routes)
│   │   ├── __init__.py
│   │   └── health.py            # Health check endpoints
│   │
│   ├── services/                # Business logic layer
│   │   ├── __init__.py
│   │   ├── auth_service.py      # MSAL authentication
│   │   └── graph_service.py     # Microsoft Graph API calls
│   │
│   ├── models/                  # Pydantic data models
│   │   ├── __init__.py
│   │   └── responses.py         # Response models
│   │
│   └── utils/                   # Utility functions
│       ├── __init__.py
│       └── tana_formatter.py    # Tana paste formatting
│
├── docs/                        # Documentation
│   ├── DEVELOPMENT.md           # Development guide
│   ├── PROJECT_STRUCTURE.md     # This file
│   ├── features/                # Feature specifications
│   └── graph_api_examples/      # Graph API test scripts
│
├── auth_records/                # Authentication cache (gitignored)
│   └── auth_record.json
│
├── app.py                       # Application entry point
├── pyproject.toml               # Project dependencies (uv)
├── uv.lock                      # Locked dependencies
├── README.md                    # Project readme
└── .env                         # Environment variables (gitignored)
```

## Core Components

### `app/main.py`
- FastAPI application instance
- Middleware configuration (CORS)
- Router registration
- Startup/shutdown events

### `app/config.py`
- Environment variable loading
- Configuration constants
- Configuration validation
- Path management

### `app/routers/`
- API endpoint definitions
- Request/response handling
- Query parameter parsing
- Format selection (JSON vs Tana paste)

**Pattern:**
```python
@router.get("/endpoint")
async def endpoint(format: str = Query("json")):
    # Get data from service
    # Format based on query param
    # Return response
```

### `app/services/`
- Business logic
- External API calls (Microsoft Graph)
- Data processing
- Authentication management

**Pattern:**
```python
class FeatureService:
    async def get_data(self):
        client = await graph_service.get_client()
        result = await client.api.call()
        return processed_result
```

### `app/models/`
- Pydantic models for type safety
- Request validation
- Response serialization
- Documentation generation

### `app/utils/`
- Shared utility functions
- Format converters (JSON → Tana paste)
- Helper functions
- Constants

## Design Principles

### 1. Separation of Concerns
- **Routers**: Handle HTTP requests/responses
- **Services**: Contain business logic
- **Models**: Define data structures
- **Utils**: Provide shared functionality

### 2. Single Responsibility
Each module/class has one clear purpose:
- `auth_service.py`: Authentication only
- `graph_service.py`: Graph API client only
- `tana_formatter.py`: Tana formatting only

### 3. Dependency Injection
Services are singleton instances that can be imported:
```python
from app.services.graph_service import graph_service
```

### 4. Configuration Management
All config in one place (`config.py`):
- Environment variables
- Paths
- Constants
- Validation

### 5. Error Handling
Use FastAPI's HTTPException:
```python
from fastapi import HTTPException

if not data:
    raise HTTPException(status_code=404, detail="Not found")
```

## Adding New Features

### Step 1: Create Feature Spec
Create `docs/features/[feature-name].md` documenting:
- Requirements
- Graph API endpoints
- Tana paste format
- Examples

### Step 2: Create Router
Create `app/routers/[feature].py`:
```python
from fastapi import APIRouter
router = APIRouter(prefix="/api/v1/[feature]", tags=["Feature"])

@router.get("/")
async def get_feature():
    # Implementation
    pass
```

### Step 3: Create Service (if needed)
Create `app/services/[feature]_service.py`:
```python
class FeatureService:
    async def process_data(self):
        # Logic here
        pass

feature_service = FeatureService()
```

### Step 4: Register Router
In `app/main.py`:
```python
from app.routers import feature
app.include_router(feature.router, tags=["Feature"])
```

### Step 5: Test
```bash
curl http://localhost:8000/api/v1/[feature]
```

## Best Practices

1. **Type Hints**: Use type hints everywhere
2. **Async/Await**: Use async for I/O operations
3. **Error Messages**: Make them helpful and specific
4. **Docstrings**: Document all public functions
5. **Keep It Simple**: Don't over-engineer

## Not Over-Engineered

We intentionally avoid:
- ❌ Complex dependency injection frameworks
- ❌ Unnecessary abstraction layers
- ❌ Over-complicated folder structures
- ❌ Premature optimization
- ❌ Too many configuration files

We focus on:
- ✅ Clear, readable code
- ✅ Standard FastAPI patterns
- ✅ Simple, flat structure
- ✅ Direct imports
- ✅ Practical solutions
