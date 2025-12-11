"""Utilities for building MS Graph attendee objects."""

from typing import Any, Dict, List, TypeVar

from msgraph.generated.models.attendee import Attendee
from msgraph.generated.models.attendee_base import AttendeeBase
from msgraph.generated.models.attendee_type import AttendeeType
from msgraph.generated.models.email_address import EmailAddress


T = TypeVar("T", Attendee, AttendeeBase)

ATTENDEE_TYPE_MAP = {
    "required": AttendeeType.Required,
    "optional": AttendeeType.Optional,
    "resource": AttendeeType.Resource,
}


def build_email_address(email_data: Dict[str, Any] | str) -> EmailAddress:
    """
    Build EmailAddress from dict or string.

    Args:
        email_data: Either a string email address or a dict with 'address' and 'name' keys.

    Returns:
        EmailAddress object populated with the provided data.
    """
    email_address = EmailAddress()
    if isinstance(email_data, str):
        email_address.address = email_data
    else:
        email_address.address = email_data.get("address")
        email_address.name = email_data.get("name")
    return email_address


def build_attendees(
    attendees: List[Dict[str, Any]],
    attendee_class: type[T] = AttendeeBase,
) -> List[T]:
    """
    Build list of attendee objects from dicts.

    Args:
        attendees: List of attendee dicts with 'emailAddress' and optional 'type'.
            emailAddress can be a string or dict with 'address' and 'name'.
        attendee_class: Attendee or AttendeeBase class to instantiate.
            Use Attendee for calendar events, AttendeeBase for findMeetingTimes.

    Returns:
        List of attendee objects of the specified class.

    Example:
        >>> attendees = [
        ...     {"emailAddress": {"address": "user@example.com", "name": "User"}, "type": "required"},
        ...     {"emailAddress": "other@example.com"},
        ... ]
        >>> build_attendees(attendees, Attendee)
        [<Attendee>, <Attendee>]
    """
    result = []
    for att in attendees:
        attendee = attendee_class()

        # Email address
        email_data = att.get("emailAddress", {})
        attendee.email_address = build_email_address(email_data)

        # Attendee type
        att_type = att.get("type", "required").lower()
        attendee.type = ATTENDEE_TYPE_MAP.get(att_type, AttendeeType.Required)

        result.append(attendee)
    return result
