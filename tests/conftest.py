"""Test configuration and fixtures"""

import os
import pytest
from datetime import datetime
from fastapi.testclient import TestClient

# Set environment variables before importing the app
os.environ["CLIENT_ID"] = "test-client-id"
os.environ["TENANT_ID"] = "test-tenant-id"

from app.main import app


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def fixed_datetime(monkeypatch):
    """Fixture to freeze datetime.now() for testing"""
    fixed_date = datetime(2025, 10, 5, 12, 0, 0)  # Saturday, Oct 5, 2025

    class MockDatetime:
        @classmethod
        def now(cls):
            return fixed_date

        @classmethod
        def fromisoformat(cls, date_string):
            return datetime.fromisoformat(date_string)

        @classmethod
        def strptime(cls, date_string, format):
            return datetime.strptime(date_string, format)

    monkeypatch.setattr("app.utils.date_utils.datetime", MockDatetime)
    return fixed_date
