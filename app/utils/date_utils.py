"""Date parsing and manipulation utilities"""

from datetime import datetime, timedelta

WEEKDAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


def get_today() -> datetime:
    """Get today at midnight"""
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)


def parse_relative_date(date_str: str) -> datetime:
    """Parse relative date keywords to datetime"""
    date_str_lower = date_str.lower()
    today = get_today()

    relative_dates = {
        "today": today,
        "tomorrow": today + timedelta(days=1),
        "yesterday": today - timedelta(days=1),
        "this-week": today - timedelta(days=today.weekday()),
        "next-week": today + timedelta(days=7 - today.weekday()),
        "this-month": today.replace(day=1),
    }

    if date_str_lower in relative_dates:
        return relative_dates[date_str_lower]

    if date_str_lower in WEEKDAYS:
        return _get_next_weekday(today, WEEKDAYS.index(date_str_lower))

    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError(
            f"Invalid date format: '{date_str}'. "
            "Use YYYY-MM-DD or keywords like 'today', 'tomorrow', 'this-week'"
        )


def _get_next_weekday(today: datetime, target_weekday: int) -> datetime:
    """Get next occurrence of specified weekday"""
    current_weekday = today.weekday()
    days_ahead = target_weekday - current_weekday
    if days_ahead <= 0:
        days_ahead += 7
    return today + timedelta(days=days_ahead)


def parse_field_tags(field_tags_str: str | None) -> dict[str, str]:
    """Parse field tags from string format to dictionary

    Format: field1:tag1,field2:tag2
    Example: attendees:co-worker,organizer:manager
    """
    if not field_tags_str:
        return {}

    result = {}
    for pair in field_tags_str.split(","):
        if ":" in pair:
            field, tag = pair.split(":", 1)
            result[field.strip().lower()] = tag.strip()
    return result
