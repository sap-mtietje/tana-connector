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
├── conftest.py              # Shared fixtures (TestClient, sample objects, time freeze)
├── fixtures/
│   └── factories.py         # Builders for events and Graph event mocks
├── unit/
│   ├── services/
│   │   ├── test_auth_service.py
│   │   ├── test_graph_service.py
│   │   ├── test_events_service.py
│   │   └── test_template_service.py
│   └── utils/
│       ├── test_date_utils.py
│       └── test_tana_formatter.py
└── integration/
    └── api/
        ├── test_health.py
        ├── test_events_json.py
        ├── test_events_tana.py
        ├── test_events_post.py
        ├── test_events_errors.py
        └── test_events_query_params.py
```

Conventions:
- Markers: `@pytest.mark.unit` for unit tests, `@pytest.mark.integration` for integration.
- Use parametrization for table-like cases (e.g., query parsing, description modes).
- Prefer factories for data setup over ad-hoc dicts.

Run with coverage and open report:

```bash
pytest --cov=app --cov-report=html && open htmlcov/index.html
```

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
