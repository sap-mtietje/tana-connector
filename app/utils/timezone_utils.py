"""Timezone detection and conversion utilities"""

from datetime import datetime, timedelta, timezone


def get_system_timezone_name() -> str:
    """
    Get the system timezone name for Microsoft Graph API

    Auto-detects timezone based on system UTC offset.
    Returns Windows timezone name (e.g., "Central European Standard Time")
    Falls back to "UTC" if detection fails
    """
    try:
        # Get local timezone offset
        local_now = datetime.now()
        utc_now = datetime.now(timezone.utc).replace(tzinfo=None)
        offset = local_now - utc_now
        offset_hours = offset.total_seconds() / 3600

        # Round to nearest 0.5 hours to handle floating point precision
        # and support half-hour timezones like India (UTC+5:30)
        offset_hours = round(offset_hours * 2) / 2

        # Map common offsets to Windows timezone names
        # Reference: https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/default-time-zones
        timezone_map = {
            -12: "Dateline Standard Time",
            -11: "UTC-11",
            -10: "Hawaiian Standard Time",
            -9: "Alaskan Standard Time",
            -8: "Pacific Standard Time",
            -7: "Mountain Standard Time",
            -6: "Central Standard Time",
            -5: "Eastern Standard Time",
            -4: "Atlantic Standard Time",
            -3: "SA Eastern Standard Time",
            -2: "UTC-02",
            -1: "Azores Standard Time",
            0: "UTC",
            1: "W. Europe Standard Time",
            2: "Central European Standard Time",  # UTC+2 (CEST)
            3: "Russian Standard Time",
            4: "Arabian Standard Time",
            5: "West Asia Standard Time",
            5.5: "India Standard Time",
            6: "Central Asia Standard Time",
            7: "SE Asia Standard Time",
            8: "China Standard Time",
            9: "Tokyo Standard Time",
            9.5: "AUS Central Standard Time",
            10: "AUS Eastern Standard Time",
            11: "Central Pacific Standard Time",
            12: "New Zealand Standard Time",
        }

        return timezone_map.get(offset_hours, "UTC")
    except Exception:
        # If anything goes wrong, default to UTC
        return "UTC"


def format_datetime_for_graph(dt: datetime) -> str:
    """Format datetime for Graph API query parameters"""
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def convert_to_local_timezone(dt: datetime) -> datetime:
    """
    Convert a datetime to the local system timezone.

    If the datetime is naive (no tzinfo), assumes it's UTC.
    Returns a timezone-aware datetime in the local timezone.
    """
    if dt is None:
        return None

    # If naive, assume UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    # Get local timezone offset (rounded to nearest minute to avoid float precision issues)
    local_now = datetime.now()
    utc_now = datetime.now(timezone.utc).replace(tzinfo=None)
    offset_seconds = round((local_now - utc_now).total_seconds() / 60) * 60

    # Create a timezone with that offset
    local_tz = timezone(timedelta(seconds=offset_seconds))

    # Convert to local timezone
    return dt.astimezone(local_tz)


def format_datetime_local(dt: datetime) -> str:
    """
    Convert datetime to local timezone and format as ISO string.

    Returns ISO format string with the local timezone offset.
    """
    if dt is None:
        return None

    local_dt = convert_to_local_timezone(dt)
    return local_dt.isoformat()
