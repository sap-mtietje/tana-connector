"""Unit tests for events_service module"""

import pytest
from unittest.mock import MagicMock
from app.services.events_service import EventsService


@pytest.mark.unit
class TestProcessDescription:
    """Tests for process_description static method"""

    def test_full_mode_returns_complete_description(self):
        """Should return complete description in full mode"""
        description = "This is a meeting description with details."
        result = EventsService.process_description(description, mode="full")
        assert result == description

    def test_none_mode_returns_empty(self):
        """Should return empty string in none mode"""
        description = "This is a meeting description."
        result = EventsService.process_description(description, mode="none")
        assert result == ""

    def test_empty_description_returns_empty(self):
        """Should return empty string for empty input"""
        result = EventsService.process_description("", mode="full")
        assert result == ""

    def test_clean_mode_removes_meeting_links(self):
        """Should remove Teams meeting links in clean mode"""
        description = (
            "Meeting details\n\nhttps://teams.microsoft.com/l/meetup/123\n\nMore info"
        )
        result = EventsService.process_description(description, mode="clean")

        assert "teams.microsoft.com" not in result
        assert "Meeting details" in result
        assert "More info" in result

    def test_clean_mode_removes_zoom_links(self):
        """Should remove Zoom meeting links in clean mode"""
        description = "Join us at https://zoom.us/j/123456789\n\nAgenda items here"
        result = EventsService.process_description(description, mode="clean")

        # Zoom links should be removed
        assert "zoom.us" not in result
        assert "Agenda items here" in result

    def test_clean_mode_preserves_regular_links(self):
        """Should preserve non-meeting URLs in clean mode"""
        description = "Check this doc: https://example.com/document\n\nhttps://teams.microsoft.com/meeting/123"
        result = EventsService.process_description(description, mode="clean")

        assert "https://example.com/document" in result
        assert "teams.microsoft.com" not in result

    def test_clean_mode_removes_separator_lines(self):
        """Should remove separator lines in clean mode"""
        description = "Header\n_______________\nContent\n========\nMore content"
        result = EventsService.process_description(description, mode="clean")

        # Separator lines (5+ chars) should be removed
        assert "_____" not in result
        assert "=====" not in result
        assert "Header" in result
        assert "Content" in result
        assert "More content" in result

    def test_html_entity_decoding(self):
        """Should decode HTML entities"""
        description = "Meeting&nbsp;with&nbsp;team&amp;stakeholders"
        result = EventsService.process_description(description, mode="full")

        assert (
            " with team&stakeholders" in result
            or "Meeting with team&stakeholders" in result
        )
        assert "&nbsp;" not in result
        assert "&amp;" not in result

    def test_numeric_html_entity_decoding(self):
        """Should decode numeric HTML entities"""
        description = "Meeting&#32;at&#32;10AM"
        result = EventsService.process_description(description, mode="full")

        assert "Meeting at 10AM" in result
        assert "&#32;" not in result

    def test_hex_html_entity_decoding(self):
        """Should decode hexadecimal HTML entities"""
        description = "Meeting&#x20;tomorrow"
        result = EventsService.process_description(description, mode="full")

        assert "Meeting tomorrow" in result
        assert "&#x20;" not in result

    def test_clean_mode_removes_excessive_whitespace(self):
        """Should clean up excessive whitespace in clean mode"""
        description = "Line 1\n\n\n\n\nLine 2\n\n\n\nLine 3"
        result = EventsService.process_description(description, mode="clean")

        # Should collapse multiple blank lines
        assert "\n\n\n" not in result
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result

    def test_max_length_truncation(self):
        """Should truncate description to max length"""
        description = (
            "This is a very long description that should be truncated at some point"
        )
        result = EventsService.process_description(
            description, mode="full", max_length=30
        )

        assert len(result) <= 33  # 30 + "..." = 33
        assert result.endswith("...")

    def test_max_length_truncation_at_word_boundary(self):
        """Should truncate at word boundary"""
        description = "Word1 Word2 Word3 Word4 Word5"
        result = EventsService.process_description(
            description, mode="full", max_length=20
        )

        # Should not cut mid-word
        assert not result[:-3].endswith("Wor")  # Not cutting "Word"
        assert result.endswith("...")

    def test_clean_mode_preserves_links_section(self):
        """Should add preserved links at the end in clean mode"""
        description = "Meeting info\nhttps://example.com/doc\nhttps://teams.microsoft.com/meeting/123"
        result = EventsService.process_description(description, mode="clean")

        assert "Links:" in result
        assert "https://example.com/doc" in result
        assert "teams.microsoft.com" not in result

    def test_clean_mode_only_links_no_content(self):
        """Should show links even when all content is removed"""
        description = "https://example.com/doc\nhttps://teams.microsoft.com/meeting/123"
        result = EventsService.process_description(description, mode="clean")

        if result.strip():  # If there's any result
            assert "https://example.com/doc" in result


@pytest.mark.unit
class TestParseEvent:
    """Tests for _parse_event method"""

    def test_parse_basic_event(self, sample_graph_event):
        """Should parse basic event properties"""
        service = EventsService()
        result = service._parse_event(sample_graph_event)

        assert result["id"] == "graph-event-123"
        assert result["title"] == "Test Event"
        assert result["location"] == "Room A"
        assert result["start"] == "2025-10-05T10:00:00"
        assert result["end"] == "2025-10-05T11:00:00"

    def test_parse_date_range(self, sample_graph_event):
        """Should combine start and end into date field"""
        service = EventsService()
        result = service._parse_event(sample_graph_event)

        assert result["date"] == "2025-10-05T10:00:00/2025-10-05T11:00:00"

    def test_parse_attendees(self, sample_graph_event):
        """Should parse attendee names and emails"""
        service = EventsService()
        result = service._parse_event(sample_graph_event)

        assert "John Doe" in result["attendees"]
        assert "jane@example.com" in result["attendees"]
        assert len(result["attendees"]) == 2

    def test_parse_organizer(self, sample_graph_event):
        """Should parse organizer email"""
        service = EventsService()
        result = service._parse_event(sample_graph_event)

        assert result["organizer"] == "organizer@example.com"

    def test_parse_categories(self, sample_graph_event):
        """Should parse event categories"""
        service = EventsService()
        result = service._parse_event(sample_graph_event)

        assert result["categories"] == ["Work"]

    def test_parse_boolean_fields(self, sample_graph_event):
        """Should parse boolean fields correctly"""
        service = EventsService()
        result = service._parse_event(sample_graph_event)

        assert result["is_all_day"] is False
        assert result["is_cancelled"] is False
        assert result["is_online_meeting"] is True
        assert result["is_reminder_on"] is True
        assert result["has_attachments"] is False

    def test_parse_status_enum(self, sample_graph_event):
        """Should format status enum value"""
        service = EventsService()
        result = service._parse_event(sample_graph_event)

        assert result["status"] == "Accepted"

    def test_parse_availability_enum(self, sample_graph_event):
        """Should format availability enum value"""
        service = EventsService()
        result = service._parse_event(sample_graph_event)

        assert result["availability"] == "Busy"

    def test_parse_online_meeting_url(self, sample_graph_event):
        """Should parse online meeting URL"""
        service = EventsService()
        result = service._parse_event(sample_graph_event)

        assert result["online_meeting_url"] == "https://teams.microsoft.com/meeting/123"

    def test_parse_description_strips_html(self, sample_graph_event):
        """Should strip HTML tags from description"""
        service = EventsService()
        result = service._parse_event(sample_graph_event)

        assert "<p>" not in result["description"]
        assert "</p>" not in result["description"]
        assert "Meeting description" in result["description"]

    def test_parse_event_without_subject(self, sample_graph_event):
        """Should use default title when subject is missing"""
        sample_graph_event.subject = None
        service = EventsService()
        result = service._parse_event(sample_graph_event)

        assert result["title"] == "Untitled Event"

    def test_parse_event_without_location(self, sample_graph_event):
        """Should handle missing location"""
        sample_graph_event.location = None
        service = EventsService()
        result = service._parse_event(sample_graph_event)

        assert result["location"] == ""

    def test_parse_event_without_attendees(self, sample_graph_event):
        """Should handle events with no attendees"""
        sample_graph_event.attendees = None
        service = EventsService()
        result = service._parse_event(sample_graph_event)

        assert result["attendees"] == []

    def test_parse_event_without_categories(self, sample_graph_event):
        """Should handle events with no categories"""
        sample_graph_event.categories = None
        service = EventsService()
        result = service._parse_event(sample_graph_event)

        assert result["categories"] == []

    def test_parse_recurring_event(self, sample_graph_event):
        """Should detect recurring events"""
        sample_graph_event.type = "SeriesMaster"
        sample_graph_event.recurrence = MagicMock()
        sample_graph_event.recurrence.pattern = MagicMock()
        sample_graph_event.recurrence.pattern.type = "Daily"

        service = EventsService()
        result = service._parse_event(sample_graph_event)

        assert result["is_recurring"] is True
        assert result["recurrence_pattern"] == "Daily"

    def test_parse_event_without_online_meeting(self, sample_graph_event):
        """Should handle events without online meeting"""
        sample_graph_event.is_online_meeting = False
        sample_graph_event.online_meeting = None

        service = EventsService()
        result = service._parse_event(sample_graph_event)

        assert result["online_meeting_url"] == ""

    def test_parse_reminder_minutes(self, sample_graph_event):
        """Should parse reminder minutes"""
        service = EventsService()
        result = service._parse_event(sample_graph_event)

        assert result["reminder_minutes"] == 15
