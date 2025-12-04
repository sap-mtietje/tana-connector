"""OData filter enums and builder for MS Graph API"""

from enum import Enum
from typing import Optional, List


class Importance(str, Enum):
    """Event importance level"""

    low = "low"
    normal = "normal"
    high = "high"


class Sensitivity(str, Enum):
    """Event sensitivity level"""

    normal = "normal"
    personal = "personal"
    private = "private"
    confidential = "confidential"


class ShowAs(str, Enum):
    """Free/busy status"""

    free = "free"
    tentative = "tentative"
    busy = "busy"
    oof = "oof"
    workingElsewhere = "workingElsewhere"
    unknown = "unknown"


class ResponseStatus(str, Enum):
    """Attendee response status"""

    none = "none"
    organizer = "organizer"
    tentativelyAccepted = "tentativelyAccepted"
    accepted = "accepted"
    declined = "declined"
    notResponded = "notResponded"


def build_odata_filter(
    base_filter: Optional[str] = None,
    importance: Optional[Importance] = None,
    sensitivity: Optional[Sensitivity] = None,
    show_as: Optional[ShowAs] = None,
    is_all_day: Optional[bool] = None,
    is_cancelled: Optional[bool] = None,
    is_online_meeting: Optional[bool] = None,
    has_attachments: Optional[bool] = None,
    response_status: Optional[ResponseStatus] = None,
    categories: Optional[List[str]] = None,
) -> Optional[str]:
    """
    Build OData filter string from friendly params.

    Combines multiple conditions with AND.
    Wraps base_filter in parentheses if provided.

    Args:
        base_filter: Raw OData filter expression to include
        importance: Filter by importance level
        sensitivity: Filter by sensitivity level
        show_as: Filter by free/busy status
        is_all_day: Filter all-day events
        is_cancelled: Filter cancelled events
        is_online_meeting: Filter online meetings
        has_attachments: Filter events with attachments
        response_status: Filter by response status
        categories: Filter by category names (OR'd together)

    Returns:
        Combined OData filter string, or None if no filters
    """
    conditions = []

    if base_filter:
        conditions.append(f"({base_filter})")

    if importance:
        conditions.append(f"importance eq '{importance.value}'")

    if sensitivity:
        conditions.append(f"sensitivity eq '{sensitivity.value}'")

    if show_as:
        conditions.append(f"showAs eq '{show_as.value}'")

    if is_all_day is not None:
        conditions.append(f"isAllDay eq {str(is_all_day).lower()}")

    if is_cancelled is not None:
        conditions.append(f"isCancelled eq {str(is_cancelled).lower()}")

    if is_online_meeting is not None:
        conditions.append(f"isOnlineMeeting eq {str(is_online_meeting).lower()}")

    if has_attachments is not None:
        conditions.append(f"hasAttachments eq {str(has_attachments).lower()}")

    if response_status:
        conditions.append(f"responseStatus/response eq '{response_status.value}'")

    if categories:
        cat_conditions = [f"categories/any(c:c eq '{cat}')" for cat in categories]
        conditions.append(f"({' or '.join(cat_conditions)})")

    if not conditions:
        return None

    return " and ".join(conditions)
