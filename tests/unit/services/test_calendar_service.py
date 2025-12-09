"""Unit tests for CalendarService"""

from unittest.mock import MagicMock
from app.services.calendar_service import CalendarService


class TestEventToDict:
    """Tests for CalendarService._event_to_dict method"""

    def setup_method(self):
        self.service = CalendarService()

    def test_basic_fields(self):
        """Test basic event fields are converted"""
        event = MagicMock()
        event.id = "test-123"
        event.subject = "Test Meeting"
        event.body_preview = "Preview text"
        event.body = None
        event.start = None
        event.end = None
        event.location = None
        event.locations = None
        event.attendees = None
        event.organizer = None
        event.response_status = None
        event.categories = None
        event.importance = None
        event.sensitivity = None
        event.show_as = None
        event.type = None
        event.is_all_day = False
        event.is_cancelled = False
        event.is_online_meeting = False
        event.has_attachments = False
        event.is_reminder_on = True
        event.reminder_minutes_before_start = 15
        event.online_meeting = None
        event.online_meeting_url = None
        event.web_link = "https://outlook.com/event/123"
        event.recurrence = None

        result = self.service._event_to_dict(event)

        assert result["id"] == "test-123"
        assert result["subject"] == "Test Meeting"
        assert result["bodyPreview"] == "Preview text"
        assert result["isAllDay"] is False
        assert result["isCancelled"] is False
        assert result["webLink"] == "https://outlook.com/event/123"

    def test_body_conversion(self):
        """Test body field conversion"""
        event = self._make_minimal_event()
        event.body = MagicMock()
        event.body.content_type = "html"
        event.body.content = "<p>Meeting notes</p>"

        result = self.service._event_to_dict(event)

        assert result["body"]["contentType"] == "html"
        assert result["body"]["content"] == "<p>Meeting notes</p>"

    def test_start_end_times(self):
        """Test start/end time conversion"""
        event = self._make_minimal_event()
        event.start = MagicMock()
        event.start.date_time = "2025-10-05T10:00:00"
        event.start.time_zone = "Europe/Berlin"
        event.end = MagicMock()
        event.end.date_time = "2025-10-05T11:00:00"
        event.end.time_zone = "Europe/Berlin"

        result = self.service._event_to_dict(event)

        assert result["start"]["dateTime"] == "2025-10-05T10:00:00"
        assert result["start"]["timeZone"] == "Europe/Berlin"
        assert result["end"]["dateTime"] == "2025-10-05T11:00:00"

    def test_location_conversion(self):
        """Test location field conversion"""
        event = self._make_minimal_event()
        event.location = MagicMock()
        event.location.display_name = "Conference Room A"
        event.location.location_type = "conferenceRoom"

        result = self.service._event_to_dict(event)

        assert result["location"]["displayName"] == "Conference Room A"
        assert result["location"]["locationType"] == "conferenceRoom"

    def test_multiple_locations(self):
        """Test multiple locations conversion"""
        event = self._make_minimal_event()
        loc1 = MagicMock()
        loc1.display_name = "Room A"
        loc2 = MagicMock()
        loc2.display_name = "Room B"
        event.locations = [loc1, loc2]

        result = self.service._event_to_dict(event)

        assert len(result["locations"]) == 2
        assert result["locations"][0]["displayName"] == "Room A"
        assert result["locations"][1]["displayName"] == "Room B"

    def test_attendees_conversion(self):
        """Test attendees field conversion"""
        event = self._make_minimal_event()
        att = MagicMock()
        att.type = "required"
        att.status = MagicMock()
        att.status.response = "accepted"
        att.status.time = MagicMock()
        att.status.time.isoformat.return_value = "2025-10-01T10:00:00"
        att.email_address = MagicMock()
        att.email_address.name = "John Doe"
        att.email_address.address = "john@example.com"
        event.attendees = [att]

        result = self.service._event_to_dict(event)

        assert len(result["attendees"]) == 1
        assert result["attendees"][0]["type"] == "required"
        assert result["attendees"][0]["emailAddress"]["name"] == "John Doe"

    def test_organizer_conversion(self):
        """Test organizer field conversion"""
        event = self._make_minimal_event()
        event.organizer = MagicMock()
        event.organizer.email_address = MagicMock()
        event.organizer.email_address.name = "Organizer"
        event.organizer.email_address.address = "org@example.com"

        result = self.service._event_to_dict(event)

        assert result["organizer"]["emailAddress"]["name"] == "Organizer"
        assert result["organizer"]["emailAddress"]["address"] == "org@example.com"

    def test_response_status_conversion(self):
        """Test response status conversion"""
        event = self._make_minimal_event()
        event.response_status = MagicMock()
        event.response_status.response = "accepted"
        event.response_status.time = MagicMock()
        event.response_status.time.isoformat.return_value = "2025-10-01T09:00:00"

        result = self.service._event_to_dict(event)

        assert result["responseStatus"]["response"] == "accepted"
        assert result["responseStatus"]["time"] == "2025-10-01T09:00:00"

    def test_categories_conversion(self):
        """Test categories field conversion"""
        event = self._make_minimal_event()
        event.categories = ["Work", "Important"]

        result = self.service._event_to_dict(event)

        assert result["categories"] == ["Work", "Important"]

    def test_enum_fields(self):
        """Test enum field conversions"""
        event = self._make_minimal_event()
        event.importance = "high"
        event.sensitivity = "private"
        event.show_as = "busy"
        event.type = "singleInstance"

        result = self.service._event_to_dict(event)

        assert result["importance"] == "high"
        assert result["sensitivity"] == "private"
        assert result["showAs"] == "busy"
        assert result["type"] == "singleInstance"

    def test_online_meeting_conversion(self):
        """Test online meeting fields"""
        event = self._make_minimal_event()
        event.is_online_meeting = True
        event.online_meeting = MagicMock()
        event.online_meeting.join_url = "https://teams.microsoft.com/meeting/123"
        event.online_meeting_url = "https://teams.microsoft.com/meeting/123"

        result = self.service._event_to_dict(event)

        assert result["isOnlineMeeting"] is True
        assert (
            result["onlineMeeting"]["joinUrl"]
            == "https://teams.microsoft.com/meeting/123"
        )
        assert result["onlineMeetingUrl"] == "https://teams.microsoft.com/meeting/123"

    def test_recurrence_conversion(self):
        """Test recurrence field conversion"""
        event = self._make_minimal_event()
        event.recurrence = MagicMock()
        event.recurrence.pattern = MagicMock()
        event.recurrence.pattern.type = "weekly"
        event.recurrence.pattern.interval = 1

        result = self.service._event_to_dict(event)

        assert result["recurrence"]["pattern"]["type"] == "weekly"
        assert result["recurrence"]["pattern"]["interval"] == 1

    def _make_minimal_event(self):
        """Create a minimal mock event with all required fields"""
        event = MagicMock()
        event.id = "test-123"
        event.subject = "Test"
        event.body_preview = ""
        event.body = None
        event.start = None
        event.end = None
        event.location = None
        event.locations = None
        event.attendees = None
        event.organizer = None
        event.response_status = None
        event.categories = None
        event.importance = None
        event.sensitivity = None
        event.show_as = None
        event.type = None
        event.is_all_day = False
        event.is_cancelled = False
        event.is_online_meeting = False
        event.has_attachments = False
        event.is_reminder_on = False
        event.reminder_minutes_before_start = 0
        event.online_meeting = None
        event.online_meeting_url = None
        event.web_link = None
        event.recurrence = None
        return event


class TestFormatAsTana:
    """Tests for CalendarService.format_as_tana method"""

    def setup_method(self):
        self.service = CalendarService()

    def test_empty_events(self):
        """Test formatting empty event list"""
        result = self.service.format_as_tana([])

        assert "%%tana%%" in result
        assert "No events found" in result

    def test_single_event(self):
        """Test formatting single event"""
        events = [
            {
                "subject": "Team Meeting",
                "start": {"dateTime": "2025-10-05T10:00:00"},
                "end": {"dateTime": "2025-10-05T11:00:00"},
                "location": {"displayName": "Room A"},
                "attendees": [],
                "categories": [],
            }
        ]

        result = self.service.format_as_tana(events)

        assert "%%tana%%" in result
        assert "Team Meeting #meeting" in result
        assert "Date::" in result
        assert "Location:: Room A" in result

    def test_event_with_attendees(self):
        """Test formatting event with attendees"""
        events = [
            {
                "subject": "Meeting",
                "start": {"dateTime": "2025-10-05T10:00:00"},
                "end": {"dateTime": "2025-10-05T11:00:00"},
                "location": {},
                "attendees": [
                    {
                        "emailAddress": {
                            "name": "John Doe",
                            "address": "john@example.com",
                        }
                    },
                    {"emailAddress": {"name": None, "address": "jane@example.com"}},
                ],
                "categories": [],
            }
        ]

        result = self.service.format_as_tana(events)

        assert "Attendees::" in result
        assert "John Doe" in result
        assert "jane@example.com" in result

    def test_event_with_categories(self):
        """Test formatting event with categories"""
        events = [
            {
                "subject": "Meeting",
                "start": {"dateTime": "2025-10-05T10:00:00"},
                "end": {"dateTime": "2025-10-05T11:00:00"},
                "location": {},
                "attendees": [],
                "categories": ["Work", "Important"],
            }
        ]

        result = self.service.format_as_tana(events)

        assert "Categories:: Work, Important" in result

    def test_custom_tag(self):
        """Test formatting with custom tag"""
        events = [
            {
                "subject": "Event",
                "start": {},
                "end": {},
                "location": {},
                "attendees": [],
                "categories": [],
            }
        ]

        result = self.service.format_as_tana(events, tag="event")

        assert "#event" in result

    def test_missing_subject(self):
        """Test formatting event without subject"""
        events = [
            {"start": {}, "end": {}, "location": {}, "attendees": [], "categories": []}
        ]

        result = self.service.format_as_tana(events)

        assert "Untitled #meeting" in result


class TestBuildAttendees:
    """Tests for CalendarService._build_attendees method"""

    def setup_method(self):
        self.service = CalendarService()

    def test_single_attendee_full_format(self):
        """Test building single attendee with full format"""
        attendees = [
            {
                "emailAddress": {"address": "john@example.com", "name": "John Doe"},
                "type": "required",
            }
        ]

        result = self.service._build_attendees(attendees)

        assert len(result) == 1
        assert result[0].email_address.address == "john@example.com"
        assert result[0].email_address.name == "John Doe"
        assert str(result[0].type) == "AttendeeType.Required"

    def test_attendee_string_email(self):
        """Test building attendee with string email address"""
        attendees = [{"emailAddress": "john@example.com"}]

        result = self.service._build_attendees(attendees)

        assert len(result) == 1
        assert result[0].email_address.address == "john@example.com"

    def test_attendee_optional_type(self):
        """Test building attendee with optional type"""
        attendees = [
            {"emailAddress": {"address": "john@example.com"}, "type": "optional"}
        ]

        result = self.service._build_attendees(attendees)

        assert str(result[0].type) == "AttendeeType.Optional"

    def test_attendee_resource_type(self):
        """Test building attendee with resource type"""
        attendees = [
            {"emailAddress": {"address": "room@example.com"}, "type": "resource"}
        ]

        result = self.service._build_attendees(attendees)

        assert str(result[0].type) == "AttendeeType.Resource"

    def test_attendee_default_type(self):
        """Test attendee defaults to required type"""
        attendees = [{"emailAddress": {"address": "john@example.com"}}]

        result = self.service._build_attendees(attendees)

        assert str(result[0].type) == "AttendeeType.Required"

    def test_multiple_attendees(self):
        """Test building multiple attendees"""
        attendees = [
            {"emailAddress": {"address": "john@example.com"}, "type": "required"},
            {"emailAddress": {"address": "jane@example.com"}, "type": "optional"},
        ]

        result = self.service._build_attendees(attendees)

        assert len(result) == 2
        assert result[0].email_address.address == "john@example.com"
        assert result[1].email_address.address == "jane@example.com"

    def test_empty_attendees(self):
        """Test building empty attendees list"""
        result = self.service._build_attendees([])

        assert len(result) == 0
