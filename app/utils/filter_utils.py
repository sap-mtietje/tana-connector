"""Post-fetch filtering utilities for MS Graph data."""

from typing import Any, Dict, List, Optional


def get_nested_value(obj: Dict[str, Any], path: str) -> Any:
    """
    Get a nested value from a dict using dot notation.

    Examples:
        get_nested_value(msg, "subject") -> msg["subject"]
        get_nested_value(msg, "from.emailAddress.name") -> msg["from"]["emailAddress"]["name"]
    """
    keys = path.split(".")
    value = obj
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return None
        if value is None:
            return None
    return value


def matches_filter(item: Dict[str, Any], field: str, operator: str, value: str) -> bool:
    """
    Check if an item matches a single filter condition.

    Operators:
        eq      - equals (exact match, or item in list)
        ne      - not equals
        contains - string contains (case-insensitive)
        startswith - string starts with (case-insensitive)
        endswith - string ends with (case-insensitive)
        gt      - greater than (for numbers/dates)
        lt      - less than (for numbers/dates)
        exists  - field exists and is not None/empty
    """
    actual = get_nested_value(item, field)

    # Handle 'exists' operator
    if operator == "exists":
        exists = actual is not None and actual != "" and actual != []
        return exists if value.lower() in ("true", "1", "yes") else not exists

    # Handle None values
    if actual is None:
        return operator == "ne"

    # Handle list fields (e.g., categories)
    if isinstance(actual, list):
        if operator == "eq":
            return value in actual
        elif operator == "ne":
            return value not in actual
        elif operator == "contains":
            return any(value.lower() in str(item).lower() for item in actual)
        return False

    # Convert to string for comparison
    actual_str = str(actual).lower()
    value_lower = value.lower()

    if operator == "eq":
        return actual_str == value_lower
    elif operator == "ne":
        return actual_str != value_lower
    elif operator == "contains":
        return value_lower in actual_str
    elif operator == "startswith":
        return actual_str.startswith(value_lower)
    elif operator == "endswith":
        return actual_str.endswith(value_lower)
    elif operator in ("gt", "lt"):
        try:
            actual_num = float(actual)
            value_num = float(value)
            return (
                actual_num > value_num if operator == "gt" else actual_num < value_num
            )
        except (ValueError, TypeError):
            # Fall back to string comparison for dates
            return (
                actual_str > value_lower
                if operator == "gt"
                else actual_str < value_lower
            )

    return False


def parse_filter_expression(filter_expr: str) -> List[tuple]:
    """
    Parse a filter expression into conditions.

    Format: field:operator:value or field:value (defaults to 'eq')
    Multiple conditions separated by comma (AND logic)

    Examples:
        "categories:tana" -> [("categories", "eq", "tana")]
        "categories:eq:tana" -> [("categories", "eq", "tana")]
        "isRead:eq:false" -> [("isRead", "eq", "false")]
        "from.emailAddress.address:contains:@sap.com" -> [("from.emailAddress.address", "contains", "@sap.com")]
        "categories:tana,isRead:eq:false" -> [("categories", "eq", "tana"), ("isRead", "eq", "false")]
    """
    conditions = []

    # Split by comma, but handle values that might contain commas
    parts = filter_expr.split(",")

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Split by colon
        segments = part.split(":")

        if len(segments) == 2:
            # field:value format (default to 'eq')
            field, value = segments
            conditions.append((field.strip(), "eq", value.strip()))
        elif len(segments) >= 3:
            # field:operator:value format (value might contain colons)
            field = segments[0].strip()
            operator = segments[1].strip().lower()
            value = ":".join(segments[2:]).strip()  # Rejoin in case value had colons
            conditions.append((field, operator, value))

    return conditions


def apply_filter(
    items: List[Dict[str, Any]], filter_expr: Optional[str], match_all: bool = True
) -> List[Dict[str, Any]]:
    """
    Apply post-fetch filter to a list of items.

    Args:
        items: List of message/event dicts
        filter_expr: Filter expression string
        match_all: If True, all conditions must match (AND). If False, any condition (OR).

    Returns:
        Filtered list of items

    Examples:
        apply_filter(messages, "categories:tana")
        apply_filter(messages, "isRead:eq:false")
        apply_filter(messages, "from.emailAddress.address:contains:@sap.com")
        apply_filter(messages, "categories:tana,isRead:eq:false")  # AND
    """
    if not filter_expr or not items:
        return items

    conditions = parse_filter_expression(filter_expr)
    if not conditions:
        return items

    result = []
    for item in items:
        matches = [
            matches_filter(item, field, op, val) for field, op, val in conditions
        ]

        if match_all and all(matches):
            result.append(item)
        elif not match_all and any(matches):
            result.append(item)

    return result
