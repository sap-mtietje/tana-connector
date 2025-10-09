"""Test factories for building common objects"""

from copy import deepcopy
from unittest.mock import MagicMock


BASE_EVENT = {
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


def make_event(**overrides):
    """Return a dict event based on BASE_EVENT with overrides applied."""
    event = deepcopy(BASE_EVENT)
    event.update(overrides)
    return event


def make_graph_event(**overrides):
    """Return a MagicMock that simulates a Microsoft Graph event object."""
    mock_event = MagicMock()

    # Basic properties
    mock_event.id = overrides.get("id", "graph-event-123")
    mock_event.subject = overrides.get("subject", "Test Event")
    mock_event.is_all_day = overrides.get("is_all_day", False)
    mock_event.is_cancelled = overrides.get("is_cancelled", False)
    mock_event.is_online_meeting = overrides.get("is_online_meeting", True)
    mock_event.is_reminder_on = overrides.get("is_reminder_on", True)
    mock_event.reminder_minutes_before_start = overrides.get(
        "reminder_minutes_before_start", 15
    )
    mock_event.has_attachments = overrides.get("has_attachments", False)
    mock_event.web_link = overrides.get(
        "web_link", "https://outlook.office.com/event/123"
    )
    mock_event.categories = overrides.get("categories", ["Work"])  # list[str]

    # Start and end times
    mock_event.start = MagicMock()
    mock_event.start.date_time = overrides.get("start", "2025-10-05T10:00:00")
    mock_event.end = MagicMock()
    mock_event.end.date_time = overrides.get("end", "2025-10-05T11:00:00")

    # Location
    mock_event.location = MagicMock()
    mock_event.location.display_name = overrides.get("location", "Room A")

    # Organizer
    mock_event.organizer = MagicMock()
    mock_event.organizer.email_address = MagicMock()
    mock_event.organizer.email_address.address = overrides.get(
        "organizer", "organizer@example.com"
    )

    # Attendees
    attendee1 = MagicMock()
    attendee1.email_address = MagicMock()
    attendee1.email_address.name = overrides.get("attendee1_name", "John Doe")
    attendee1.email_address.address = overrides.get(
        "attendee1_email", "john@example.com"
    )

    attendee2 = MagicMock()
    attendee2.email_address = MagicMock()
    attendee2.email_address.name = overrides.get("attendee2_name", None)
    attendee2.email_address.address = overrides.get(
        "attendee2_email", "jane@example.com"
    )

    mock_event.attendees = overrides.get("attendees", [attendee1, attendee2])

    # Body/Description
    mock_event.body = MagicMock()
    mock_event.body.content = overrides.get(
        "body_content", "<p>Meeting description</p>"
    )

    # Response status
    mock_event.response_status = MagicMock()
    mock_event.response_status.response = overrides.get("response", "Accepted")

    # Show as (availability)
    mock_event.show_as = overrides.get("show_as", "Busy")

    # Importance and sensitivity
    mock_event.importance = overrides.get("importance", "High")
    mock_event.sensitivity = overrides.get("sensitivity", "Normal")

    # Event type (for recurrence)
    mock_event.type = overrides.get("type", "Single")
    mock_event.recurrence = overrides.get("recurrence", None)

    # Online meeting
    mock_event.online_meeting = MagicMock()
    mock_event.online_meeting.join_url = overrides.get(
        "online_meeting_url", "https://teams.microsoft.com/meeting/123"
    )

    return mock_event
