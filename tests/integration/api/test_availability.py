"""
Tests for POST /me/findMeetingTimes and POST /me/events endpoints.

Tests cover:
- Find meeting times with various parameters
- Tana format output
- Template rendering
- Create event endpoint
- Error handling
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient


class TestFindMeetingTimes:
    """Tests for POST /me/findMeetingTimes endpoint"""

    def test_find_meeting_times_basic(self, client, mock_availability_service):
        """Test basic find meeting times request"""
        mock_availability_service.return_value = {
            "meetingTimeSuggestions": [
                {
                    "confidence": 100,
                    "order": 1,
                    "meetingTimeSlot": {
                        "start": {"dateTime": "2025-12-10T09:00:00"},
                        "end": {"dateTime": "2025-12-10T10:00:00"},
                    },
                }
            ],
            "emptySuggestionsReason": "",
        }

        response = client.post(
            "/me/findMeetingTimes",
            json={
                "attendees": [
                    {
                        "emailAddress": {"address": "test@example.com"},
                        "type": "required",
                    }
                ],
                "timeConstraint": {
                    "activityDomain": "work",
                    "timeSlots": [
                        {
                            "start": {"dateTime": "2025-12-10T09:00:00"},
                            "end": {"dateTime": "2025-12-10T17:00:00"},
                        }
                    ],
                },
                "meetingDuration": "PT1H",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "meetingTimeSuggestions" in data
        assert len(data["meetingTimeSuggestions"]) == 1

    def test_find_meeting_times_with_date_keyword(
        self, client, mock_availability_service
    ):
        """Test find meeting times with _dateKeyword"""
        mock_availability_service.return_value = {
            "meetingTimeSuggestions": [],
            "emptySuggestionsReason": "OrganizerUnavailable",
        }

        response = client.post(
            "/me/findMeetingTimes?_dateKeyword=tomorrow",
            json={
                "attendees": [
                    {
                        "emailAddress": {"address": "test@example.com"},
                        "type": "required",
                    }
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "emptySuggestionsReason" in data

    def test_find_meeting_times_tana_format(self, client, mock_availability_service):
        """Test find meeting times with Tana format"""
        mock_availability_service.return_value = {
            "meetingTimeSuggestions": [
                {
                    "confidence": 100,
                    "order": 1,
                    "meetingTimeSlot": {
                        "start": {"dateTime": "2025-12-10T09:00:00"},
                        "end": {"dateTime": "2025-12-10T10:00:00"},
                    },
                }
            ],
            "emptySuggestionsReason": "",
        }

        response = client.post(
            "/me/findMeetingTimes?_format=tana",
            json={
                "attendees": [
                    {
                        "emailAddress": {"address": "test@example.com"},
                        "type": "required",
                    }
                ],
                "timeConstraint": {
                    "activityDomain": "work",
                    "timeSlots": [
                        {
                            "start": {"dateTime": "2025-12-10T09:00:00"},
                            "end": {"dateTime": "2025-12-10T17:00:00"},
                        }
                    ],
                },
            },
        )

        assert response.status_code == 200
        assert "%%tana%%" in response.text

    def test_find_meeting_times_missing_attendees_returns_422(self, client):
        """Test that missing attendees field returns 422 validation error"""
        response = client.post(
            "/me/findMeetingTimes",
            json={
                "timeConstraint": {
                    "activityDomain": "work",
                    "timeSlots": [
                        {
                            "start": {"dateTime": "2025-12-10T09:00:00"},
                            "end": {"dateTime": "2025-12-10T17:00:00"},
                        }
                    ],
                },
            },
        )

        assert response.status_code == 422

    def test_find_meeting_times_service_error(self, client, mock_availability_service):
        """Test error handling when service fails"""
        mock_availability_service.side_effect = Exception("API Error")

        response = client.post(
            "/me/findMeetingTimes",
            json={
                "attendees": [
                    {
                        "emailAddress": {"address": "test@example.com"},
                        "type": "required",
                    }
                ],
                "timeConstraint": {
                    "activityDomain": "work",
                    "timeSlots": [
                        {
                            "start": {"dateTime": "2025-12-10T09:00:00"},
                            "end": {"dateTime": "2025-12-10T17:00:00"},
                        }
                    ],
                },
            },
        )

        assert response.status_code == 500


class TestFindMeetingTimesRender:
    """Tests for POST /me/findMeetingTimes/render endpoint"""

    def test_render_meeting_times(self, client, mock_availability_service):
        """Test template rendering for meeting times"""
        mock_availability_service.return_value = {
            "meetingTimeSuggestions": [
                {
                    "confidence": 100,
                    "order": 1,
                    "meetingTimeSlot": {
                        "start": {"dateTime": "2025-12-10T09:00:00"},
                        "end": {"dateTime": "2025-12-10T10:00:00"},
                    },
                }
            ],
            "emptySuggestionsReason": "",
        }

        template = "Found {{count}} suggestions"

        response = client.post(
            "/me/findMeetingTimes/render?attendees=test@example.com&_dateKeyword=tomorrow",
            content=template,
            headers={"Content-Type": "text/plain"},
        )

        assert response.status_code == 200
        assert "Found 1 suggestions" in response.text

    def test_render_meeting_times_no_attendees_returns_422(self, client):
        """Test that missing attendees returns 422 validation error"""
        response = client.post(
            "/me/findMeetingTimes/render?_dateKeyword=tomorrow",
            content="template",
            headers={"Content-Type": "text/plain"},
        )

        # FastAPI returns 422 for missing required query params
        assert response.status_code == 422


class TestCreateEvent:
    """Tests for POST /me/events endpoint"""

    def test_create_event_basic(self, client, mock_create_event):
        """Test basic event creation"""
        mock_create_event.return_value = {
            "id": "event-123",
            "subject": "Test Meeting",
            "start": {"dateTime": "2025-12-10T09:00:00", "timeZone": "Europe/Berlin"},
            "end": {"dateTime": "2025-12-10T10:00:00", "timeZone": "Europe/Berlin"},
        }

        response = client.post(
            "/me/events",
            json={
                "subject": "Test Meeting",
                "start": {
                    "dateTime": "2025-12-10T09:00:00",
                    "timeZone": "Europe/Berlin",
                },
                "end": {"dateTime": "2025-12-10T10:00:00", "timeZone": "Europe/Berlin"},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert data["value"]["subject"] == "Test Meeting"

    def test_create_event_with_attendees(self, client, mock_create_event):
        """Test event creation with attendees"""
        mock_create_event.return_value = {
            "id": "event-123",
            "subject": "Team Meeting",
            "attendees": [
                {
                    "emailAddress": {"address": "test@example.com"},
                    "type": "required",
                }
            ],
        }

        response = client.post(
            "/me/events",
            json={
                "subject": "Team Meeting",
                "start": {"dateTime": "2025-12-10T09:00:00"},
                "end": {"dateTime": "2025-12-10T10:00:00"},
                "attendees": [
                    {
                        "emailAddress": {"address": "test@example.com"},
                        "type": "required",
                    }
                ],
            },
        )

        assert response.status_code == 200

    def test_create_event_with_body_and_location(self, client, mock_create_event):
        """Test event creation with body and location"""
        mock_create_event.return_value = {
            "id": "event-123",
            "subject": "Meeting",
            "body": {"contentType": "HTML", "content": "<p>Notes</p>"},
            "location": {"displayName": "Room A"},
        }

        response = client.post(
            "/me/events",
            json={
                "subject": "Meeting",
                "start": {"dateTime": "2025-12-10T09:00:00"},
                "end": {"dateTime": "2025-12-10T10:00:00"},
                "body": {"contentType": "HTML", "content": "<p>Notes</p>"},
                "location": {"displayName": "Room A"},
            },
        )

        assert response.status_code == 200

    def test_create_event_online_meeting(self, client, mock_create_event):
        """Test creating Teams meeting"""
        mock_create_event.return_value = {
            "id": "event-123",
            "subject": "Teams Call",
            "isOnlineMeeting": True,
            "onlineMeeting": {"joinUrl": "https://teams.microsoft.com/..."},
        }

        response = client.post(
            "/me/events",
            json={
                "subject": "Teams Call",
                "start": {"dateTime": "2025-12-10T09:00:00"},
                "end": {"dateTime": "2025-12-10T10:00:00"},
                "isOnlineMeeting": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["value"]["isOnlineMeeting"] is True

    def test_create_event_service_error(self, client, mock_create_event):
        """Test error handling when service fails"""
        mock_create_event.side_effect = Exception("API Error")

        response = client.post(
            "/me/events",
            json={
                "subject": "Test",
                "start": {"dateTime": "2025-12-10T09:00:00"},
                "end": {"dateTime": "2025-12-10T10:00:00"},
            },
        )

        assert response.status_code == 500


# -------------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------------


@pytest.fixture
def mock_availability_service():
    """Mock the availability_service.find_meeting_times method"""
    with patch(
        "app.routers.graph.availability.availability_service.find_meeting_times",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


@pytest.fixture
def mock_create_event():
    """Mock the calendar_service.create_event method"""
    with patch(
        "app.routers.graph.calendar.calendar_service.create_event",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


@pytest.fixture
def client():
    """FastAPI test client"""
    import os

    os.environ["CLIENT_ID"] = "test-client-id"
    os.environ["TENANT_ID"] = "test-tenant-id"

    from app.main import app

    return TestClient(app)
