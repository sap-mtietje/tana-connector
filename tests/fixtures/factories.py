"""Test factories for building common objects"""

from copy import deepcopy


# MS Graph format (used by /me/CalendarView endpoints)
BASE_MS_GRAPH_EVENT = {
    "id": "graph-event-123",
    "subject": "Team Meeting",
    "bodyPreview": "Weekly team sync",
    "body": {
        "contentType": "html",
        "content": "<p>Weekly team sync</p>",
    },
    "start": {
        "dateTime": "2025-10-05T10:00:00",
        "timeZone": "Europe/Berlin",
    },
    "end": {
        "dateTime": "2025-10-05T11:00:00",
        "timeZone": "Europe/Berlin",
    },
    "location": {
        "displayName": "Conference Room A",
        "locationType": "default",
    },
    "attendees": [
        {
            "type": "required",
            "status": {"response": "accepted", "time": "2025-10-01T10:00:00"},
            "emailAddress": {"name": "John Doe", "address": "john@example.com"},
        },
        {
            "type": "optional",
            "status": {"response": "tentativelyAccepted", "time": None},
            "emailAddress": {"name": "Jane Smith", "address": "jane@example.com"},
        },
    ],
    "organizer": {
        "emailAddress": {"name": "Organizer", "address": "organizer@example.com"}
    },
    "responseStatus": {"response": "accepted", "time": "2025-10-01T10:00:00"},
    "categories": ["Work", "Important"],
    "importance": "high",
    "sensitivity": "normal",
    "showAs": "busy",
    "isAllDay": False,
    "isCancelled": False,
    "isOnlineMeeting": True,
    "onlineMeeting": {"joinUrl": "https://teams.microsoft.com/meeting/123"},
    "onlineMeetingUrl": "https://teams.microsoft.com/meeting/123",
    "webLink": "https://outlook.office.com/event/123",
    "hasAttachments": False,
    "isReminderOn": True,
    "reminderMinutesBeforeStart": 15,
    "recurrence": None,
    "type": "singleInstance",
}


def make_ms_graph_event(**overrides):
    """
    Return a dict event in MS Graph JSON format (as returned by calendar_service).
    This is the format used by the new /me/CalendarView endpoints.
    """
    event = deepcopy(BASE_MS_GRAPH_EVENT)

    # Handle nested updates
    for key, value in overrides.items():
        if key in event and isinstance(event[key], dict) and isinstance(value, dict):
            event[key].update(value)
        else:
            event[key] = value

    return event


def make_ms_graph_event_set():
    """
    Create a diverse set of MS Graph events for comprehensive filter testing.
    Returns a list of events with varying properties.
    """
    return [
        # Event 1: High importance, busy, online meeting, accepted
        make_ms_graph_event(
            id="event-1",
            subject="Important Strategy Meeting",
            importance="high",
            sensitivity="normal",
            showAs="busy",
            isAllDay=False,
            isOnlineMeeting=True,
            isCancelled=False,
            hasAttachments=True,
            categories=["Work", "Strategy"],
            responseStatus={"response": "accepted", "time": "2025-10-01T10:00:00"},
        ),
        # Event 2: Normal importance, free, in-person, tentative
        make_ms_graph_event(
            id="event-2",
            subject="Casual Lunch",
            importance="normal",
            sensitivity="personal",
            showAs="free",
            isAllDay=False,
            isOnlineMeeting=False,
            isCancelled=False,
            hasAttachments=False,
            categories=["Personal"],
            responseStatus={"response": "tentativelyAccepted", "time": None},
        ),
        # Event 3: Low importance, tentative, all-day, declined
        make_ms_graph_event(
            id="event-3",
            subject="Company Holiday",
            importance="low",
            sensitivity="normal",
            showAs="tentative",
            isAllDay=True,
            isOnlineMeeting=False,
            isCancelled=False,
            hasAttachments=False,
            categories=["Holiday"],
            responseStatus={"response": "declined", "time": "2025-10-02T08:00:00"},
        ),
        # Event 4: High importance, oof (out of office), cancelled
        make_ms_graph_event(
            id="event-4",
            subject="Cancelled Review",
            importance="high",
            sensitivity="private",
            showAs="oof",
            isAllDay=False,
            isOnlineMeeting=True,
            isCancelled=True,
            hasAttachments=False,
            categories=["Work"],
            responseStatus={"response": "notResponded", "time": None},
        ),
        # Event 5: Normal importance, workingElsewhere, organizer
        make_ms_graph_event(
            id="event-5",
            subject="Remote Work Day",
            importance="normal",
            sensitivity="confidential",
            showAs="workingElsewhere",
            isAllDay=True,
            isOnlineMeeting=False,
            isCancelled=False,
            hasAttachments=False,
            categories=["Work", "Remote"],
            responseStatus={"response": "organizer", "time": "2025-10-01T09:00:00"},
        ),
    ]
