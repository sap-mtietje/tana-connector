"""Unit tests for AvailabilityService"""

from datetime import timedelta
from unittest.mock import MagicMock

from app.services.availability_service import AvailabilityService


class TestBuildAttendees:
    """Tests for AvailabilityService._build_attendees method"""

    def setup_method(self):
        self.service = AvailabilityService()

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


class TestBuildTimeConstraint:
    """Tests for AvailabilityService._build_time_constraint method"""

    def setup_method(self):
        self.service = AvailabilityService()

    def test_work_activity_domain(self):
        """Test time constraint with work activity domain"""
        constraint = {
            "activityDomain": "work",
            "timeSlots": [
                {
                    "start": {"dateTime": "2024-12-10T09:00:00"},
                    "end": {"dateTime": "2024-12-10T17:00:00"},
                }
            ],
        }

        result = self.service._build_time_constraint(constraint, "Europe/Berlin")

        assert str(result.activity_domain) == "ActivityDomain.Work"
        assert len(result.time_slots) == 1

    def test_personal_activity_domain(self):
        """Test time constraint with personal activity domain"""
        constraint = {
            "activityDomain": "personal",
            "timeSlots": [
                {
                    "start": {"dateTime": "2024-12-10T09:00:00"},
                    "end": {"dateTime": "2024-12-10T17:00:00"},
                }
            ],
        }

        result = self.service._build_time_constraint(constraint, "Europe/Berlin")

        assert str(result.activity_domain) == "ActivityDomain.Personal"

    def test_unrestricted_activity_domain(self):
        """Test time constraint with unrestricted activity domain"""
        constraint = {
            "activityDomain": "unrestricted",
            "timeSlots": [
                {
                    "start": {"dateTime": "2024-12-10T09:00:00"},
                    "end": {"dateTime": "2024-12-10T17:00:00"},
                }
            ],
        }

        result = self.service._build_time_constraint(constraint, "Europe/Berlin")

        assert str(result.activity_domain) == "ActivityDomain.Unrestricted"

    def test_time_slot_with_timezone(self):
        """Test time slot with explicit timezone"""
        constraint = {
            "activityDomain": "work",
            "timeSlots": [
                {
                    "start": {
                        "dateTime": "2024-12-10T09:00:00",
                        "timeZone": "Pacific Standard Time",
                    },
                    "end": {
                        "dateTime": "2024-12-10T17:00:00",
                        "timeZone": "Pacific Standard Time",
                    },
                }
            ],
        }

        result = self.service._build_time_constraint(constraint, "Europe/Berlin")

        assert result.time_slots[0].start.time_zone == "Pacific Standard Time"
        assert result.time_slots[0].end.time_zone == "Pacific Standard Time"

    def test_time_slot_default_timezone(self):
        """Test time slot uses default timezone when not specified"""
        constraint = {
            "activityDomain": "work",
            "timeSlots": [
                {
                    "start": {"dateTime": "2024-12-10T09:00:00"},
                    "end": {"dateTime": "2024-12-10T17:00:00"},
                }
            ],
        }

        result = self.service._build_time_constraint(constraint, "Europe/Berlin")

        assert result.time_slots[0].start.time_zone == "Europe/Berlin"
        assert result.time_slots[0].end.time_zone == "Europe/Berlin"

    def test_multiple_time_slots(self):
        """Test multiple time slots"""
        constraint = {
            "activityDomain": "work",
            "timeSlots": [
                {
                    "start": {"dateTime": "2024-12-10T09:00:00"},
                    "end": {"dateTime": "2024-12-10T12:00:00"},
                },
                {
                    "start": {"dateTime": "2024-12-10T14:00:00"},
                    "end": {"dateTime": "2024-12-10T17:00:00"},
                },
            ],
        }

        result = self.service._build_time_constraint(constraint, "Europe/Berlin")

        assert len(result.time_slots) == 2


class TestBuildLocationConstraint:
    """Tests for AvailabilityService._build_location_constraint method"""

    def setup_method(self):
        self.service = AvailabilityService()

    def test_basic_location_constraint(self):
        """Test basic location constraint"""
        constraint = {
            "isRequired": True,
            "suggestLocation": False,
            "locations": [{"displayName": "Conference Room A"}],
        }

        result = self.service._build_location_constraint(constraint)

        assert result.is_required is True
        assert result.suggest_location is False
        assert len(result.locations) == 1
        assert result.locations[0].display_name == "Conference Room A"

    def test_location_with_resolve_availability(self):
        """Test location with resolve availability flag"""
        constraint = {
            "isRequired": False,
            "suggestLocation": True,
            "locations": [
                {"displayName": "Room A", "resolveAvailability": True},
                {"displayName": "Room B", "resolveAvailability": False},
            ],
        }

        result = self.service._build_location_constraint(constraint)

        assert result.locations[0].resolve_availability is True
        assert result.locations[1].resolve_availability is False

    def test_empty_locations(self):
        """Test location constraint with no locations"""
        constraint = {"isRequired": False, "suggestLocation": True, "locations": []}

        result = self.service._build_location_constraint(constraint)

        assert len(result.locations) == 0


class TestParseDuration:
    """Tests for AvailabilityService._parse_duration method"""

    def setup_method(self):
        self.service = AvailabilityService()

    def test_one_hour(self):
        """Test parsing PT1H"""
        result = self.service._parse_duration("PT1H")
        assert result == timedelta(hours=1)

    def test_thirty_minutes(self):
        """Test parsing PT30M"""
        result = self.service._parse_duration("PT30M")
        assert result == timedelta(minutes=30)

    def test_one_hour_thirty_minutes(self):
        """Test parsing PT1H30M"""
        result = self.service._parse_duration("PT1H30M")
        assert result == timedelta(hours=1, minutes=30)

    def test_two_hours(self):
        """Test parsing PT2H"""
        result = self.service._parse_duration("PT2H")
        assert result == timedelta(hours=2)

    def test_lowercase(self):
        """Test parsing lowercase duration"""
        result = self.service._parse_duration("pt1h")
        assert result == timedelta(hours=1)

    def test_invalid_format_defaults_to_one_hour(self):
        """Test invalid format defaults to 1 hour"""
        result = self.service._parse_duration("invalid")
        assert result == timedelta(hours=1)


class TestResultToDict:
    """Tests for AvailabilityService._result_to_dict method"""

    def setup_method(self):
        self.service = AvailabilityService()

    def test_empty_result(self):
        """Test converting empty result"""
        result = MagicMock()
        result.meeting_time_suggestions = []
        result.empty_suggestions_reason = "No available times"

        output = self.service._result_to_dict(result)

        assert output["meetingTimeSuggestions"] == []
        assert output["emptySuggestionsReason"] == "No available times"

    def test_suggestion_basic_fields(self):
        """Test converting suggestion with basic fields"""
        suggestion = MagicMock()
        suggestion.confidence = 100
        suggestion.order = 1
        suggestion.organizer_availability = "free"
        suggestion.suggestion_reason = "All attendees available"
        suggestion.meeting_time_slot = None
        suggestion.attendee_availability = None
        suggestion.locations = None

        result = MagicMock()
        result.meeting_time_suggestions = [suggestion]
        result.empty_suggestions_reason = ""

        output = self.service._result_to_dict(result)

        assert len(output["meetingTimeSuggestions"]) == 1
        assert output["meetingTimeSuggestions"][0]["confidence"] == 100
        assert output["meetingTimeSuggestions"][0]["order"] == 1
        assert output["meetingTimeSuggestions"][0]["organizerAvailability"] == "free"
        assert (
            output["meetingTimeSuggestions"][0]["suggestionReason"]
            == "All attendees available"
        )

    def test_suggestion_with_meeting_time_slot(self):
        """Test converting suggestion with meeting time slot"""
        suggestion = MagicMock()
        suggestion.confidence = 100
        suggestion.order = 1
        suggestion.organizer_availability = None
        suggestion.suggestion_reason = None
        suggestion.attendee_availability = None
        suggestion.locations = None

        suggestion.meeting_time_slot = MagicMock()
        suggestion.meeting_time_slot.start = MagicMock()
        suggestion.meeting_time_slot.start.date_time = "2024-12-10T09:00:00"
        suggestion.meeting_time_slot.start.time_zone = "Europe/Berlin"
        suggestion.meeting_time_slot.end = MagicMock()
        suggestion.meeting_time_slot.end.date_time = "2024-12-10T10:00:00"
        suggestion.meeting_time_slot.end.time_zone = "Europe/Berlin"

        result = MagicMock()
        result.meeting_time_suggestions = [suggestion]
        result.empty_suggestions_reason = ""

        output = self.service._result_to_dict(result)

        slot = output["meetingTimeSuggestions"][0]["meetingTimeSlot"]
        # DateTime now includes timezone offset (ISO format)
        assert slot["start"]["dateTime"].startswith("2024-12-10T09:00:00")
        assert slot["start"]["timeZone"] == "Europe/Berlin"
        assert slot["end"]["dateTime"].startswith("2024-12-10T10:00:00")

    def test_suggestion_with_attendee_availability(self):
        """Test converting suggestion with attendee availability"""
        attendee_avail = MagicMock()
        attendee_avail.availability = "free"
        attendee_avail.attendee = MagicMock()
        attendee_avail.attendee.email_address = MagicMock()
        attendee_avail.attendee.email_address.address = "john@example.com"
        attendee_avail.attendee.email_address.name = "John Doe"

        suggestion = MagicMock()
        suggestion.confidence = 100
        suggestion.order = 1
        suggestion.organizer_availability = None
        suggestion.suggestion_reason = None
        suggestion.meeting_time_slot = None
        suggestion.locations = None
        suggestion.attendee_availability = [attendee_avail]

        result = MagicMock()
        result.meeting_time_suggestions = [suggestion]
        result.empty_suggestions_reason = ""

        output = self.service._result_to_dict(result)

        att_avail = output["meetingTimeSuggestions"][0]["attendeeAvailability"][0]
        assert att_avail["availability"] == "free"
        assert att_avail["attendee"]["emailAddress"]["address"] == "john@example.com"

    def test_suggestion_with_locations(self):
        """Test converting suggestion with locations"""
        location = MagicMock()
        location.display_name = "Conference Room A"

        suggestion = MagicMock()
        suggestion.confidence = 100
        suggestion.order = 1
        suggestion.organizer_availability = None
        suggestion.suggestion_reason = None
        suggestion.meeting_time_slot = None
        suggestion.attendee_availability = None
        suggestion.locations = [location]

        result = MagicMock()
        result.meeting_time_suggestions = [suggestion]
        result.empty_suggestions_reason = ""

        output = self.service._result_to_dict(result)

        assert (
            output["meetingTimeSuggestions"][0]["locations"][0]["displayName"]
            == "Conference Room A"
        )


class TestFormatAsTana:
    """Tests for AvailabilityService.format_as_tana method"""

    def setup_method(self):
        self.service = AvailabilityService()

    def test_empty_suggestions(self):
        """Test formatting empty suggestions"""
        result = {
            "meetingTimeSuggestions": [],
            "emptySuggestionsReason": "No available times",
        }

        output = self.service.format_as_tana(result)

        assert "%%tana%%" in output
        assert "No meeting times available" in output
        assert "No available times" in output

    def test_single_suggestion(self):
        """Test formatting single suggestion"""
        result = {
            "meetingTimeSuggestions": [
                {
                    "confidence": 100,
                    "order": 1,
                    "organizerAvailability": "free",
                    "suggestionReason": "All attendees available",
                    "meetingTimeSlot": {
                        "start": {"dateTime": "2024-12-10T09:00:00"},
                        "end": {"dateTime": "2024-12-10T10:00:00"},
                    },
                }
            ],
            "emptySuggestionsReason": "",
        }

        output = self.service.format_as_tana(result, subject="Team Meeting")

        assert "%%tana%%" in output
        assert "Team Meeting #meeting-proposal" in output
        assert "Option 1::" in output
        assert "Confidence:: 100%" in output
        assert "Organizer:: free" in output
        assert "Reason:: All attendees available" in output

    def test_multiple_suggestions(self):
        """Test formatting multiple suggestions"""
        result = {
            "meetingTimeSuggestions": [
                {
                    "confidence": 100,
                    "order": 1,
                    "meetingTimeSlot": {
                        "start": {"dateTime": "2024-12-10T09:00:00"},
                        "end": {"dateTime": "2024-12-10T10:00:00"},
                    },
                },
                {
                    "confidence": 80,
                    "order": 2,
                    "meetingTimeSlot": {
                        "start": {"dateTime": "2024-12-10T14:00:00"},
                        "end": {"dateTime": "2024-12-10T15:00:00"},
                    },
                },
            ],
            "emptySuggestionsReason": "",
        }

        output = self.service.format_as_tana(result)

        assert "Option 1::" in output
        assert "Option 2::" in output
        assert "Confidence:: 100%" in output
        assert "Confidence:: 80%" in output

    def test_custom_tag(self):
        """Test custom tag parameter"""
        result = {
            "meetingTimeSuggestions": [
                {
                    "confidence": 100,
                    "order": 1,
                    "meetingTimeSlot": {
                        "start": {"dateTime": "2024-12-10T09:00:00"},
                        "end": {"dateTime": "2024-12-10T10:00:00"},
                    },
                }
            ],
            "emptySuggestionsReason": "",
        }

        output = self.service.format_as_tana(result, tag="availability")

        assert "#availability" in output
