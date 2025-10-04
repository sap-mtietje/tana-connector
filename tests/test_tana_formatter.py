"""Unit tests for tana_formatter module"""

import pytest
from app.utils.tana_formatter import TanaFormatter


@pytest.mark.unit
class TestFormatNode:
    """Tests for format_node function"""

    def test_simple_node(self):
        """Should format a simple node with just a title"""
        result = TanaFormatter.format_node("My Task")
        assert result == "- My Task"

    def test_node_with_fields(self):
        """Should format a node with fields"""
        fields = {"Status": "Done", "Priority": "High"}
        result = TanaFormatter.format_node("My Task", fields=fields)
        expected = "- My Task\n  - Status:: Done\n  - Priority:: High"
        assert result == expected

    def test_node_with_children(self):
        """Should format a node with children"""
        children = ["- Child 1", "- Child 2"]
        result = TanaFormatter.format_node("Parent", children=children)
        expected = "- Parent\n  - Child 1\n  - Child 2"
        assert result == expected

    def test_node_with_fields_and_children(self):
        """Should format a node with both fields and children"""
        fields = {"Status": "Active"}
        children = ["- Child"]
        result = TanaFormatter.format_node("Parent", children=children, fields=fields)
        expected = "- Parent\n  - Status:: Active\n  - Child"
        assert result == expected


@pytest.mark.unit
class TestFormatList:
    """Tests for format_list function"""

    def test_empty_list(self):
        """Should handle empty list"""
        result = TanaFormatter.format_list([])
        assert result == ""

    def test_single_item(self):
        """Should format single item"""
        items = [{"title": "Task 1", "fields": {"Status": "Done"}}]
        result = TanaFormatter.format_list(items)
        assert "- Task 1" in result
        assert "Status:: Done" in result

    def test_multiple_items(self):
        """Should format multiple items"""
        items = [
            {"title": "Task 1", "fields": {"Status": "Done"}},
            {"title": "Task 2", "fields": {"Status": "Pending"}},
        ]
        result = TanaFormatter.format_list(items)
        assert "- Task 1" in result
        assert "- Task 2" in result


@pytest.mark.unit
class TestFormatEvents:
    """Tests for format_events function"""

    def test_basic_event(self, sample_event):
        """Should format a basic event"""
        result = TanaFormatter.format_events([sample_event])

        assert "- Team Meeting #[[meeting]]" in result
        assert "Identifier:: test-event-123" in result
        assert "Location:: Conference Room A" in result
        assert "Status:: Accepted" in result

    def test_event_with_custom_tag(self, sample_event):
        """Should use custom tag instead of default 'meeting'"""
        result = TanaFormatter.format_events([sample_event], tag="work")
        assert "#[[work]]" in result
        assert "#[[meeting]]" not in result

    def test_event_with_category_tags(self, sample_event):
        """Should use category tags when include_category_tags is True"""
        result = TanaFormatter.format_events([sample_event], include_category_tags=True)
        assert "#[[Work]]" in result
        assert "#[[Important]]" in result
        assert "#[[meeting]]" not in result

    def test_event_with_category_tags_no_categories(self, sample_event):
        """Should fallback to base tag when no categories exist"""
        sample_event["categories"] = []
        result = TanaFormatter.format_events(
            [sample_event], tag="meeting", include_category_tags=True
        )
        assert "#[[meeting]]" in result

    def test_filter_fields(self, sample_event):
        """Should only show specified fields"""
        result = TanaFormatter.format_events(
            [sample_event], filter_fields=["title", "date", "location"]
        )

        # These should be present
        assert "Team Meeting" in result
        assert "Location::" in result
        assert "Date::" in result

        # These should NOT be present
        assert "Status::" not in result
        assert "Attendees::" not in result

    def test_show_empty_false(self, sample_event):
        """Should hide empty fields when show_empty is False"""
        sample_event["location"] = ""
        sample_event["description"] = ""

        result = TanaFormatter.format_events([sample_event], show_empty=False)

        # Empty fields should not appear
        assert "Location::" not in result
        assert "Description::" not in result

        # Non-empty fields should appear
        assert "Status::" in result

    def test_show_empty_true(self, sample_event):
        """Should show empty fields when show_empty is True"""
        sample_event["location"] = ""

        result = TanaFormatter.format_events([sample_event], show_empty=True)
        assert "Location::" in result

    def test_field_tags_attendees(self, sample_event):
        """Should apply tags to attendees field"""
        field_tags = {"attendees": "co-worker"}
        result = TanaFormatter.format_events([sample_event], field_tags=field_tags)

        assert "John Doe #co-worker" in result
        assert "jane@example.com #co-worker" in result

    def test_field_tags_organizer(self, sample_event):
        """Should apply tag to organizer field"""
        field_tags = {"organizer": "manager"}
        result = TanaFormatter.format_events([sample_event], field_tags=field_tags)

        assert "[[organizer@example.com #manager]]" in result

    def test_field_tags_location(self, sample_event):
        """Should apply tag to location field"""
        field_tags = {"location": "office"}
        result = TanaFormatter.format_events([sample_event], field_tags=field_tags)

        assert "[[Conference Room A #office]]" in result

    def test_date_field_formatting(self, sample_event):
        """Should format date field as Tana date range"""
        result = TanaFormatter.format_events([sample_event])
        assert "Date:: [[date:2025-10-05 10:00/2025-10-05 11:00]]" in result

    def test_start_end_fields(self, sample_event):
        """Should format individual start and end fields"""
        result = TanaFormatter.format_events(
            [sample_event], filter_fields=["start", "end"]
        )

        assert "Start:: [[date:2025-10-05 10:00]]" in result
        assert "End:: [[date:2025-10-05 11:00]]" in result

    def test_attendees_list(self, sample_event):
        """Should format attendees as a list"""
        result = TanaFormatter.format_events([sample_event])

        assert "Attendees::" in result
        assert "- John Doe" in result
        assert "- jane@example.com" in result

    def test_categories_list(self, sample_event):
        """Should format categories with brackets"""
        result = TanaFormatter.format_events([sample_event])

        assert "Categories::" in result
        assert "- [[Work]]" in result
        assert "- [[Important]]" in result

    def test_boolean_fields(self, sample_event):
        """Should format boolean fields as lowercase strings"""
        result = TanaFormatter.format_events([sample_event])

        assert "Is Cancelled:: false" in result
        assert "Is Online Meeting:: true" in result
        assert "Is Recurring:: false" in result

    def test_reminder_field(self, sample_event):
        """Should format reminder when enabled"""
        result = TanaFormatter.format_events([sample_event])
        assert "Reminder:: 15 minutes before" in result

    def test_reminder_field_disabled(self, sample_event):
        """Should not show reminder when disabled and show_empty is False"""
        sample_event["is_reminder_on"] = False
        result = TanaFormatter.format_events([sample_event], show_empty=False)
        assert "Reminder::" not in result

    def test_description_multiline_converted_to_single(self, sample_event):
        """Should convert multiline description to single line"""
        sample_event["description"] = "Line 1\nLine 2\nLine 3"
        result = TanaFormatter.format_events([sample_event])

        assert "Description:: Line 1 Line 2 Line 3" in result

    def test_title_with_leading_number_escaped(self):
        """Should escape leading numbers in titles"""
        event = {
            "title": "1. First Item",
            "id": "test-123",
            "date": "",
            "start": "",
            "end": "",
            "location": "",
            "status": "",
            "attendees": [],
            "description": "",
            "calendar": "Calendar",
            "availability": "",
            "is_all_day": False,
            "organizer": "",
            "categories": [],
            "web_link": "",
            "is_cancelled": False,
            "is_online_meeting": False,
            "online_meeting_url": "",
            "importance": "",
            "sensitivity": "",
            "is_reminder_on": False,
            "reminder_minutes": 0,
            "is_recurring": False,
            "recurrence_pattern": "",
            "has_attachments": False,
        }
        result = TanaFormatter.format_events([event], show_empty=False)
        # The period after number should be escaped
        assert "- 1\\. First Item" in result

    def test_multiple_events(self, sample_event):
        """Should format multiple events"""
        event2 = sample_event.copy()
        event2["title"] = "Another Meeting"
        event2["id"] = "test-event-456"

        result = TanaFormatter.format_events([sample_event, event2])

        assert "- Team Meeting" in result
        assert "- Another Meeting" in result
        assert "test-event-123" in result
        assert "test-event-456" in result


@pytest.mark.unit
class TestFormatDatetime:
    """Tests for datetime formatting functions"""

    def test_format_timing_eventlink(self):
        """Should format datetime range correctly"""
        start = "2025-10-05T10:00:00"
        end = "2025-10-05T11:00:00"
        result = TanaFormatter._format_timing_eventlink(start, end)
        assert result == "[[date:2025-10-05 10:00/2025-10-05 11:00]]"

    def test_format_timing_with_microseconds(self):
        """Should handle datetimes with microseconds"""
        start = "2025-10-05T10:00:00.0000000"
        end = "2025-10-05T11:00:00.0000000"
        result = TanaFormatter._format_timing_eventlink(start, end)
        assert result == "[[date:2025-10-05 10:00/2025-10-05 11:00]]"

    def test_format_timing_with_z_suffix(self):
        """Should handle datetimes with Z suffix"""
        start = "2025-10-05T10:00:00Z"
        end = "2025-10-05T11:00:00Z"
        result = TanaFormatter._format_timing_eventlink(start, end)
        assert result == "[[date:2025-10-05 10:00/2025-10-05 11:00]]"

    def test_format_single_datetime(self):
        """Should format single datetime correctly"""
        dt_str = "2025-10-05T10:00:00"
        result = TanaFormatter._format_single_datetime(dt_str)
        assert result == "[[date:2025-10-05 10:00]]"

    def test_format_single_datetime_with_microseconds(self):
        """Should handle single datetime with microseconds"""
        dt_str = "2025-10-05T10:00:00.0000000"
        result = TanaFormatter._format_single_datetime(dt_str)
        assert result == "[[date:2025-10-05 10:00]]"

    def test_format_invalid_datetime_fallback(self):
        """Should fallback to original string if parsing fails"""
        dt_str = "invalid-datetime"
        result = TanaFormatter._format_single_datetime(dt_str)
        assert result == "[[date:invalid-datetime]]"


@pytest.mark.unit
class TestShouldDisplay:
    """Tests for _should_display helper function"""

    def test_field_in_filter_with_value(self):
        """Should display field when in filter and has value"""
        assert TanaFormatter._should_display("Status", "Accepted", ["status"], True)

    def test_field_not_in_filter(self):
        """Should not display field when not in filter"""
        assert not TanaFormatter._should_display(
            "Status", "Accepted", ["location"], True
        )

    def test_empty_field_show_empty_true(self):
        """Should display empty field when show_empty is True"""
        assert TanaFormatter._should_display("Status", "", [], True)

    def test_empty_field_show_empty_false(self):
        """Should not display empty field when show_empty is False"""
        assert not TanaFormatter._should_display("Status", "", [], False)

    def test_no_filter_specified(self):
        """Should display all fields when no filter is specified"""
        assert TanaFormatter._should_display("Status", "Accepted", [], True)


@pytest.mark.unit
class TestHasValue:
    """Tests for _has_value helper function"""

    def test_string_with_value(self):
        """Should return True for non-empty string"""
        assert TanaFormatter._has_value("text")

    def test_empty_string(self):
        """Should return False for empty string"""
        assert not TanaFormatter._has_value("")

    def test_whitespace_string(self):
        """Should return False for whitespace-only string"""
        assert not TanaFormatter._has_value("   ")

    def test_none_value(self):
        """Should return False for None"""
        assert not TanaFormatter._has_value(None)

    def test_empty_list(self):
        """Should return False for empty list"""
        assert not TanaFormatter._has_value([])

    def test_non_empty_list(self):
        """Should return True for non-empty list"""
        assert TanaFormatter._has_value(["item"])

    def test_zero_value(self):
        """Should return True for zero (it's a value)"""
        assert TanaFormatter._has_value(0)

    def test_false_boolean(self):
        """Should return True for False boolean (it's a value)"""
        assert TanaFormatter._has_value(False)
