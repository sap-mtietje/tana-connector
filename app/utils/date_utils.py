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


def parse_date_keyword_to_range(keyword: str) -> tuple[datetime, datetime]:
    """
    Parse date keyword to start/end datetime range.

    Returns (start_datetime, end_datetime) tuple.

    Keywords:
        - today: today 00:00 to 23:59:59
        - tomorrow: tomorrow 00:00 to 23:59:59
        - yesterday: yesterday 00:00 to 23:59:59
        - this-week: Monday 00:00 to Sunday 23:59:59
        - next-week: Next Monday 00:00 to next Sunday 23:59:59
        - this-month: 1st of month 00:00 to last day 23:59:59
        - monday-sunday: That day 00:00 to 23:59:59
    """
    keyword_lower = keyword.lower().strip()
    today = get_today()
    end_of_day = timedelta(hours=23, minutes=59, seconds=59)

    # Single day keywords
    if keyword_lower == "today":
        return today, today + end_of_day

    if keyword_lower == "tomorrow":
        start = today + timedelta(days=1)
        return start, start + end_of_day

    if keyword_lower == "yesterday":
        start = today - timedelta(days=1)
        return start, start + end_of_day

    # Week keywords
    if keyword_lower == "this-week":
        start = today - timedelta(days=today.weekday())  # Monday
        end = start + timedelta(days=6) + end_of_day  # Sunday
        return start, end

    if keyword_lower == "next-week":
        start = today + timedelta(days=7 - today.weekday())  # Next Monday
        end = start + timedelta(days=6) + end_of_day  # Next Sunday
        return start, end

    # Month keyword
    if keyword_lower == "this-month":
        start = today.replace(day=1)
        # Last day of month
        if today.month == 12:
            end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        return start, end + end_of_day

    # Weekday names
    if keyword_lower in WEEKDAYS:
        target_day = _get_next_weekday(today, WEEKDAYS.index(keyword_lower))
        return target_day, target_day + end_of_day

    raise ValueError(
        f"Invalid date keyword: '{keyword}'. "
        "Use: today, tomorrow, yesterday, this-week, next-week, this-month, or weekday names"
    )


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
