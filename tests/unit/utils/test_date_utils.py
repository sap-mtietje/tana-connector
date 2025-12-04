"""Unit tests for date_utils module"""

import pytest
from datetime import datetime, timedelta
from app.utils.date_utils import (
    get_today,
    parse_relative_date,
    parse_date_keyword_to_range,
    parse_field_tags,
    _get_next_weekday,
)


@pytest.mark.unit
class TestGetToday:
    """Tests for get_today function"""

    def test_returns_datetime_at_midnight(self):
        """Should return current date at midnight"""
        result = get_today()
        assert isinstance(result, datetime)
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0
        assert result.microsecond == 0


@pytest.mark.unit
class TestParseRelativeDate:
    """Tests for parse_relative_date function"""

    def test_today_keyword(self, fixed_datetime):
        """Should parse 'today' keyword"""
        result = parse_relative_date("today")
        assert result == fixed_datetime.replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    def test_tomorrow_keyword(self, fixed_datetime):
        """Should parse 'tomorrow' keyword"""
        result = parse_relative_date("tomorrow")
        expected = fixed_datetime.replace(
            hour=0, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)
        assert result == expected

    def test_yesterday_keyword(self, fixed_datetime):
        """Should parse 'yesterday' keyword"""
        result = parse_relative_date("yesterday")
        expected = fixed_datetime.replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - timedelta(days=1)
        assert result == expected

    def test_this_week_keyword(self, fixed_datetime):
        """Should parse 'this-week' keyword (Monday of current week)"""
        result = parse_relative_date("this-week")
        # Oct 5, 2025 is Sunday (weekday=6), so Monday is 6 days back
        today = fixed_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
        expected = today - timedelta(days=today.weekday())  # Back to Monday
        assert result == expected
        assert result == datetime(2025, 9, 29, 0, 0, 0)  # Sep 29 is Monday

    def test_next_week_keyword(self, fixed_datetime):
        """Should parse 'next-week' keyword (Monday of next week)"""
        result = parse_relative_date("next-week")
        # Oct 5, 2025 is Sunday (weekday=6), next Monday is 7 - 6 = 1 day ahead
        today = fixed_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
        expected = today + timedelta(days=7 - today.weekday())  # Next Monday
        assert result == expected
        assert result == datetime(2025, 10, 6, 0, 0, 0)  # Oct 6 is Monday

    def test_this_month_keyword(self, fixed_datetime):
        """Should parse 'this-month' keyword (first day of month)"""
        result = parse_relative_date("this-month")
        expected = fixed_datetime.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        assert result == expected

    def test_weekday_monday(self, fixed_datetime):
        """Should parse 'monday' keyword to next Monday"""
        result = parse_relative_date("monday")
        # Oct 5 is Sunday (weekday=6), next Monday (weekday=0) is 1 day ahead
        # days_ahead = 0 - 6 = -6, add 7 = 1
        assert result == datetime(2025, 10, 6, 0, 0, 0)  # Oct 6 is Monday
        assert result.weekday() == 0  # Verify it's Monday

    def test_weekday_tuesday(self, fixed_datetime):
        """Should parse 'tuesday' keyword"""
        result = parse_relative_date("tuesday")
        # Oct 5 is Sunday (weekday=6), next Tuesday (weekday=1) is 2 days ahead
        # days_ahead = 1 - 6 = -5, add 7 = 2
        assert result == datetime(2025, 10, 7, 0, 0, 0)  # Oct 7 is Tuesday
        assert result.weekday() == 1  # Verify it's Tuesday

    def test_case_insensitive(self, fixed_datetime):
        """Should parse keywords case-insensitively"""
        assert parse_relative_date("TODAY") == parse_relative_date("today")
        assert parse_relative_date("Tomorrow") == parse_relative_date("tomorrow")
        assert parse_relative_date("MONDAY") == parse_relative_date("monday")

    def test_explicit_date_format(self):
        """Should parse explicit YYYY-MM-DD date"""
        result = parse_relative_date("2025-12-25")
        expected = datetime(2025, 12, 25, 0, 0, 0)
        assert result == expected

    def test_invalid_date_raises_error(self):
        """Should raise ValueError for invalid date format"""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_relative_date("invalid-date")

    def test_invalid_date_format_raises_error(self):
        """Should raise ValueError for invalid date string"""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_relative_date("2025/10/05")


@pytest.mark.unit
class TestGetNextWeekday:
    """Tests for _get_next_weekday function"""

    def test_next_weekday_same_day(self, fixed_datetime):
        """Should get next week's occurrence when target is same weekday"""
        # Oct 5 is Sunday (weekday=6)
        today = fixed_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
        result = _get_next_weekday(today, 6)  # Sunday
        # days_ahead = 6 - 6 = 0, then 0 <= 0 so add 7
        assert result == today + timedelta(days=7)
        assert result.weekday() == 6  # Should be Sunday

    def test_next_weekday_ahead(self, fixed_datetime):
        """Should get weekday ahead (wrapping to next week)"""
        # Oct 5 is Sunday (weekday=6), Monday is weekday=0
        today = fixed_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
        result = _get_next_weekday(today, 0)  # Next Monday
        # days_ahead = 0 - 6 = -6, add 7 = 1
        assert result == today + timedelta(days=1)
        assert result.weekday() == 0  # Should be Monday

    def test_next_weekday_behind(self, fixed_datetime):
        """Should get next week when target weekday is behind current"""
        # Oct 5 is Sunday (weekday=6), Friday is weekday=4
        today = fixed_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
        result = _get_next_weekday(today, 4)  # Next Friday
        # days_ahead = 4 - 6 = -2, add 7 = 5 days
        assert result == today + timedelta(days=5)
        assert result.weekday() == 4  # Should be Friday


@pytest.mark.unit
class TestParseDateKeywordToRange:
    """Tests for parse_date_keyword_to_range function"""

    def test_today_range(self, fixed_datetime):
        """Should return today's full day range"""
        start, end = parse_date_keyword_to_range("today")
        assert start == datetime(2025, 10, 5, 0, 0, 0)
        assert end == datetime(2025, 10, 5, 23, 59, 59)

    def test_tomorrow_range(self, fixed_datetime):
        """Should return tomorrow's full day range"""
        start, end = parse_date_keyword_to_range("tomorrow")
        assert start == datetime(2025, 10, 6, 0, 0, 0)
        assert end == datetime(2025, 10, 6, 23, 59, 59)

    def test_yesterday_range(self, fixed_datetime):
        """Should return yesterday's full day range"""
        start, end = parse_date_keyword_to_range("yesterday")
        assert start == datetime(2025, 10, 4, 0, 0, 0)
        assert end == datetime(2025, 10, 4, 23, 59, 59)

    def test_this_week_range(self, fixed_datetime):
        """Should return Monday to Sunday of current week"""
        start, end = parse_date_keyword_to_range("this-week")
        # Oct 5, 2025 is Sunday, so Monday is Sep 29
        assert start == datetime(2025, 9, 29, 0, 0, 0)
        assert end == datetime(2025, 10, 5, 23, 59, 59)

    def test_next_week_range(self, fixed_datetime):
        """Should return Monday to Sunday of next week"""
        start, end = parse_date_keyword_to_range("next-week")
        # Oct 5, 2025 is Sunday, next Monday is Oct 6
        assert start == datetime(2025, 10, 6, 0, 0, 0)
        assert end == datetime(2025, 10, 12, 23, 59, 59)

    def test_this_month_range(self, fixed_datetime):
        """Should return first to last day of current month"""
        start, end = parse_date_keyword_to_range("this-month")
        assert start == datetime(2025, 10, 1, 0, 0, 0)
        assert end == datetime(2025, 10, 31, 23, 59, 59)

    def test_weekday_range(self, fixed_datetime):
        """Should return full day range for weekday keyword"""
        start, end = parse_date_keyword_to_range("monday")
        # Oct 5 is Sunday, next Monday is Oct 6
        assert start == datetime(2025, 10, 6, 0, 0, 0)
        assert end == datetime(2025, 10, 6, 23, 59, 59)

    def test_invalid_keyword_raises_error(self, fixed_datetime):
        """Should raise ValueError for invalid keyword"""
        with pytest.raises(ValueError, match="Invalid date keyword"):
            parse_date_keyword_to_range("invalid-keyword")

    def test_case_insensitive(self, fixed_datetime):
        """Should handle case-insensitive keywords"""
        start1, end1 = parse_date_keyword_to_range("TODAY")
        start2, end2 = parse_date_keyword_to_range("today")
        assert start1 == start2
        assert end1 == end2


@pytest.mark.unit
class TestParseDateKeywordToRangeDecember:
    """Tests for parse_date_keyword_to_range with December edge case"""

    def test_this_month_december(self, monkeypatch):
        """Should handle December correctly (year rollover)"""
        fixed_date = datetime(2025, 12, 15, 12, 0, 0)

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

        start, end = parse_date_keyword_to_range("this-month")
        assert start == datetime(2025, 12, 1, 0, 0, 0)
        assert end == datetime(2025, 12, 31, 23, 59, 59)


@pytest.mark.unit
class TestParseFieldTags:
    """Tests for parse_field_tags function"""

    def test_parse_single_field_tag(self):
        """Should parse single field:tag pair"""
        result = parse_field_tags("attendees:co-worker")
        assert result == {"attendees": "co-worker"}

    def test_parse_multiple_field_tags(self):
        """Should parse multiple field:tag pairs"""
        result = parse_field_tags(
            "attendees:co-worker,organizer:manager,location:office"
        )
        assert result == {
            "attendees": "co-worker",
            "organizer": "manager",
            "location": "office",
        }

    def test_parse_with_spaces(self):
        """Should handle spaces in field tags"""
        result = parse_field_tags("attendees: co-worker , organizer: manager")
        assert result == {"attendees": "co-worker", "organizer": "manager"}

    def test_parse_empty_string(self):
        """Should return empty dict for empty string"""
        result = parse_field_tags("")
        assert result == {}

    def test_parse_none(self):
        """Should return empty dict for None"""
        result = parse_field_tags(None)
        assert result == {}

    def test_lowercase_field_names(self):
        """Should convert field names to lowercase"""
        result = parse_field_tags("Attendees:worker,ORGANIZER:boss")
        assert result == {"attendees": "worker", "organizer": "boss"}

    def test_tag_with_colon(self):
        """Should handle tags with colons by taking everything after first colon"""
        result = parse_field_tags("field:tag:with:colons")
        assert result == {"field": "tag:with:colons"}

    def test_ignore_pairs_without_colon(self):
        """Should ignore pairs without colon separator"""
        result = parse_field_tags("attendees:worker,invalid-pair,location:office")
        assert result == {"attendees": "worker", "location": "office"}
