"""Test configuration and fixtures"""

import os
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

# Set environment variables before importing the app
os.environ["CLIENT_ID"] = "test-client-id"
os.environ["TENANT_ID"] = "test-tenant-id"

from app.main import app


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def mock_graph_client():
    """Mock Microsoft Graph client"""
    mock = MagicMock()
    mock.me = MagicMock()
    mock.me.calendar_view = MagicMock()
    mock.me.calendar_view.get = AsyncMock()
    return mock


@pytest.fixture
def sample_event():
    """Sample event data for testing"""
    return {
        "id": "test-event-123",
        "title": "Team Meeting",
        "start": "2025-10-05T10:00:00",
        "end": "2025-10-05T11:00:00",
        "date": "2025-10-05T10:00:00/2025-10-05T11:00:00",
        "location": "Conference Room A",
        "status": "Accepted",
        "attendees": ["John Doe", "jane@example.com"],
        "description": "Weekly team sync",
        "calendar": "Calendar",
        "availability": "Busy",
        "is_all_day": False,
        "organizer": "organizer@example.com",
        "categories": ["Work", "Important"],
        "web_link": "https://outlook.office.com/event/123",
        "is_cancelled": False,
        "is_online_meeting": True,
        "online_meeting_url": "https://teams.microsoft.com/meeting/123",
        "importance": "High",
        "sensitivity": "Normal",
        "is_reminder_on": True,
        "reminder_minutes": 15,
        "is_recurring": False,
        "recurrence_pattern": "",
        "has_attachments": False,
    }


@pytest.fixture
def sample_graph_event():
    """Sample Microsoft Graph API event object"""
    mock_event = MagicMock()
    
    # Basic properties
    mock_event.id = "graph-event-123"
    mock_event.subject = "Test Event"
    mock_event.is_all_day = False
    mock_event.is_cancelled = False
    mock_event.is_online_meeting = True
    mock_event.is_reminder_on = True
    mock_event.reminder_minutes_before_start = 15
    mock_event.has_attachments = False
    mock_event.web_link = "https://outlook.office.com/event/123"
    mock_event.categories = ["Work"]
    
    # Start and end times
    mock_event.start = MagicMock()
    mock_event.start.date_time = "2025-10-05T10:00:00"
    mock_event.end = MagicMock()
    mock_event.end.date_time = "2025-10-05T11:00:00"
    
    # Location
    mock_event.location = MagicMock()
    mock_event.location.display_name = "Room A"
    
    # Organizer
    mock_event.organizer = MagicMock()
    mock_event.organizer.email_address = MagicMock()
    mock_event.organizer.email_address.address = "organizer@example.com"
    
    # Attendees
    attendee1 = MagicMock()
    attendee1.email_address = MagicMock()
    attendee1.email_address.name = "John Doe"
    attendee1.email_address.address = "john@example.com"
    
    attendee2 = MagicMock()
    attendee2.email_address = MagicMock()
    attendee2.email_address.name = None
    attendee2.email_address.address = "jane@example.com"
    
    mock_event.attendees = [attendee1, attendee2]
    
    # Body/Description
    mock_event.body = MagicMock()
    mock_event.body.content = "<p>Meeting description</p>"
    
    # Response status
    mock_event.response_status = MagicMock()
    mock_event.response_status.response = "Accepted"
    
    # Show as (availability)
    mock_event.show_as = "Busy"
    
    # Importance and sensitivity
    mock_event.importance = "High"
    mock_event.sensitivity = "Normal"
    
    # Event type (for recurrence)
    mock_event.type = "Single"
    mock_event.recurrence = None
    
    # Online meeting
    mock_event.online_meeting = MagicMock()
    mock_event.online_meeting.join_url = "https://teams.microsoft.com/meeting/123"
    
    return mock_event


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

