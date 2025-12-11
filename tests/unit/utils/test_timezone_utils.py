"""Unit tests for timezone utilities"""

from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from app.utils.timezone_utils import (
    get_system_timezone_name,
    format_datetime_for_graph,
    convert_to_local_timezone,
    format_datetime_local,
)


class TestGetSystemTimezoneName:
    """Tests for get_system_timezone_name function"""

    def test_returns_string(self):
        """Test that function returns a string"""
        result = get_system_timezone_name()
        assert isinstance(result, str)
        assert len(result) > 0

    @patch("app.utils.timezone_utils.datetime")
    def test_utc_offset_zero(self, mock_datetime):
        """Test UTC timezone detection"""
        mock_datetime.now.side_effect = [
            datetime(2025, 10, 5, 12, 0, 0),  # local
            MagicMock(
                replace=MagicMock(return_value=datetime(2025, 10, 5, 12, 0, 0))
            ),  # utc
        ]

        result = get_system_timezone_name()
        assert result == "UTC"

    @patch("app.utils.timezone_utils.datetime")
    def test_utc_plus_1(self, mock_datetime):
        """Test UTC+1 timezone detection"""
        mock_datetime.now.side_effect = [
            datetime(2025, 10, 5, 13, 0, 0),  # local (UTC+1)
            MagicMock(
                replace=MagicMock(return_value=datetime(2025, 10, 5, 12, 0, 0))
            ),  # utc
        ]

        result = get_system_timezone_name()
        assert result == "W. Europe Standard Time"

    @patch("app.utils.timezone_utils.datetime")
    def test_utc_plus_2(self, mock_datetime):
        """Test UTC+2 timezone detection (Central European)"""
        mock_datetime.now.side_effect = [
            datetime(2025, 10, 5, 14, 0, 0),  # local (UTC+2)
            MagicMock(
                replace=MagicMock(return_value=datetime(2025, 10, 5, 12, 0, 0))
            ),  # utc
        ]

        result = get_system_timezone_name()
        assert result == "Central European Standard Time"

    @patch("app.utils.timezone_utils.datetime")
    def test_utc_minus_5(self, mock_datetime):
        """Test UTC-5 timezone detection (Eastern US)"""
        mock_datetime.now.side_effect = [
            datetime(2025, 10, 5, 7, 0, 0),  # local (UTC-5)
            MagicMock(
                replace=MagicMock(return_value=datetime(2025, 10, 5, 12, 0, 0))
            ),  # utc
        ]

        result = get_system_timezone_name()
        assert result == "Eastern Standard Time"

    @patch("app.utils.timezone_utils.datetime")
    def test_utc_minus_8(self, mock_datetime):
        """Test UTC-8 timezone detection (Pacific US)"""
        mock_datetime.now.side_effect = [
            datetime(2025, 10, 5, 4, 0, 0),  # local (UTC-8)
            MagicMock(
                replace=MagicMock(return_value=datetime(2025, 10, 5, 12, 0, 0))
            ),  # utc
        ]

        result = get_system_timezone_name()
        assert result == "Pacific Standard Time"

    @patch("app.utils.timezone_utils.datetime")
    def test_utc_plus_5_5_india(self, mock_datetime):
        """Test UTC+5:30 timezone detection (India)"""
        mock_datetime.now.side_effect = [
            datetime(2025, 10, 5, 17, 30, 0),  # local (UTC+5:30)
            MagicMock(
                replace=MagicMock(return_value=datetime(2025, 10, 5, 12, 0, 0))
            ),  # utc
        ]

        result = get_system_timezone_name()
        assert result == "India Standard Time"

    @patch("app.utils.timezone_utils.datetime")
    def test_unknown_offset_returns_utc(self, mock_datetime):
        """Test unknown offset falls back to UTC"""
        # UTC+13 is not in the timezone map
        mock_datetime.now.side_effect = [
            datetime(2025, 10, 6, 1, 0, 0),  # local (UTC+13)
            MagicMock(
                replace=MagicMock(return_value=datetime(2025, 10, 5, 12, 0, 0))
            ),  # utc
        ]

        result = get_system_timezone_name()
        assert result == "UTC"

    @patch("app.utils.timezone_utils.datetime")
    def test_exception_returns_utc(self, mock_datetime):
        """Test exception handling returns UTC"""
        mock_datetime.now.side_effect = Exception("Test error")

        result = get_system_timezone_name()
        assert result == "UTC"


class TestFormatDatetimeForGraph:
    """Tests for format_datetime_for_graph function"""

    def test_formats_datetime(self):
        """Test datetime formatting"""
        dt = datetime(2025, 10, 5, 14, 30, 45)
        result = format_datetime_for_graph(dt)
        assert result == "2025-10-05T14:30:45"

    def test_formats_midnight(self):
        """Test midnight formatting"""
        dt = datetime(2025, 10, 5, 0, 0, 0)
        result = format_datetime_for_graph(dt)
        assert result == "2025-10-05T00:00:00"

    def test_formats_end_of_day(self):
        """Test end of day formatting"""
        dt = datetime(2025, 10, 5, 23, 59, 59)
        result = format_datetime_for_graph(dt)
        assert result == "2025-10-05T23:59:59"


class TestConvertToLocalTimezone:
    """Tests for convert_to_local_timezone function"""

    def test_none_returns_none(self):
        """Test None input returns None"""
        result = convert_to_local_timezone(None)
        assert result is None

    def test_naive_datetime_assumed_utc(self):
        """Test naive datetime is assumed to be UTC"""
        dt = datetime(2025, 12, 9, 12, 0, 0)
        result = convert_to_local_timezone(dt)
        # Result should be timezone-aware
        assert result.tzinfo is not None

    def test_aware_datetime_converted(self):
        """Test timezone-aware datetime is converted"""
        dt = datetime(2025, 12, 9, 12, 0, 0, tzinfo=timezone.utc)
        result = convert_to_local_timezone(dt)
        # Result should be timezone-aware
        assert result.tzinfo is not None


class TestFormatDatetimeLocal:
    """Tests for format_datetime_local function"""

    def test_none_returns_none(self):
        """Test None input returns None"""
        result = format_datetime_local(None)
        assert result is None

    def test_formats_utc_datetime(self):
        """Test formatting UTC datetime"""
        dt = datetime(2025, 12, 9, 12, 0, 0, tzinfo=timezone.utc)
        result = format_datetime_local(dt)
        # Should be ISO format string
        assert isinstance(result, str)
        assert "2025-12-09" in result

    def test_formats_naive_datetime(self):
        """Test formatting naive datetime"""
        dt = datetime(2025, 12, 9, 12, 0, 0)
        result = format_datetime_local(dt)
        # Should be ISO format string
        assert isinstance(result, str)
        assert "2025-12-09" in result
