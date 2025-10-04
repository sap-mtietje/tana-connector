# Test Suite

This directory contains the test suite for the Tana-Connector application.

## Setup

Install dev dependencies:

```bash
uv sync --all-extras
# or
uv pip install -e ".[dev]"
```

## Running Tests

Run all tests:

```bash
pytest
```

Run with coverage report:

```bash
pytest --cov=app --cov-report=html
```

Run only unit tests:

```bash
pytest -m unit
```

Run only integration tests:

```bash
pytest -m integration
```

Run a specific test file:

```bash
pytest tests/test_date_utils.py
```

Run a specific test:

```bash
pytest tests/test_date_utils.py::TestParseRelativeDate::test_today_keyword
```

Run with verbose output:

```bash
pytest -v
```

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_date_utils.py       # Unit tests for date utilities (24 tests)
├── test_tana_formatter.py   # Unit tests for Tana formatting (39 tests)
├── test_events_service.py   # Unit tests for events service (32 tests)
├── test_auth_service.py     # Unit tests for authentication (14 tests)
├── test_graph_service.py    # Unit tests for Graph API (7 tests)
└── test_api_endpoints.py    # Integration tests for API endpoints (38 tests)
```

**Total: 154 tests**

See [GRAPH_API_TESTS.md](./GRAPH_API_TESTS.md) for detailed documentation on Graph API and authentication tests.

## Test Coverage

After running tests with coverage, open the HTML report:

```bash
open htmlcov/index.html
```

## Writing New Tests

### Unit Tests

Mark unit tests with the `@pytest.mark.unit` decorator:

```python
@pytest.mark.unit
def test_my_function():
    result = my_function()
    assert result == expected
```

### Integration Tests

Mark integration tests with the `@pytest.mark.integration` decorator:

```python
@pytest.mark.integration
def test_api_endpoint(client):
    response = client.get("/endpoint")
    assert response.status_code == 200
```

### Using Fixtures

Common fixtures are available in `conftest.py`:

- `client`: FastAPI TestClient for API testing
- `sample_event`: Sample event data
- `sample_graph_event`: Mock Microsoft Graph event object
- `fixed_datetime`: Freeze time for date testing

## Continuous Integration

The test suite is designed to run in CI/CD pipelines. All tests mock external dependencies (Microsoft Graph API) so they don't require real credentials.
