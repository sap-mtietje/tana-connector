"""MCP tool implementations wrapping existing services."""

from __future__ import annotations

from typing import Any, Dict

from app.mcp import formatters
from app.mcp.schemas import (
    CreateDraftInput,
    CreateEventInput,
    FindMeetingTimesInput,
    GetEmailsInput,
    GetEventsInput,
)
from app.mcp.service_factory import get_factory
from app.utils.date_utils import parse_date_keyword_to_range
from app.utils.timezone_utils import format_datetime_for_graph, get_system_timezone_name


async def outlook_get_events(arguments: Dict[str, Any]) -> str:
    """Get calendar events for a date range.

    Args:
        arguments: Tool arguments matching GetEventsInput schema.

    Returns:
        Formatted string of calendar events.
    """
    try:
        input_data = GetEventsInput(**arguments)
        factory = get_factory()
        calendar_service = factory.get_calendar_service()

        # Resolve date range
        if input_data.date_keyword:
            start_dt, end_dt = parse_date_keyword_to_range(input_data.date_keyword)
            start_date = format_datetime_for_graph(start_dt)
            end_date = format_datetime_for_graph(end_dt)
        elif input_data.start_date and input_data.end_date:
            start_date = input_data.start_date
            end_date = input_data.end_date
        else:
            return "Error: Must provide either date_keyword or both start_date and end_date"

        events = await calendar_service.get_calendar_view(
            start_date_time=start_date,
            end_date_time=end_date,
            top=input_data.max_results,
        )

        return formatters.format_events(events)

    except Exception as e:
        return formatters.format_error(e, "outlook_get_events")


async def outlook_create_event(arguments: Dict[str, Any]) -> str:
    """Create a new calendar event.

    Args:
        arguments: Tool arguments matching CreateEventInput schema.

    Returns:
        Confirmation of created event.
    """
    try:
        input_data = CreateEventInput(**arguments)
        factory = get_factory()
        calendar_service = factory.get_calendar_service()
        timezone_name = get_system_timezone_name()

        # Build start/end time dicts
        start = {"dateTime": input_data.start_time, "timeZone": timezone_name}
        end = {"dateTime": input_data.end_time, "timeZone": timezone_name}

        # Build attendees list if provided
        attendees = None
        if input_data.attendees:
            attendees = [
                {"emailAddress": {"address": email}, "type": "required"}
                for email in input_data.attendees
            ]

        # Build location dict if provided
        location = None
        if input_data.location:
            location = {"displayName": input_data.location}

        # Build body dict if provided
        body = None
        if input_data.body:
            body = {"contentType": "HTML", "content": input_data.body}

        event = await calendar_service.create_event(
            subject=input_data.subject,
            start=start,
            end=end,
            attendees=attendees,
            is_online_meeting=input_data.is_online_meeting,
            location=location,
            body=body,
        )

        return formatters.format_created_event(event)

    except Exception as e:
        return formatters.format_error(e, "outlook_create_event")


async def outlook_find_meeting_times(arguments: Dict[str, Any]) -> str:
    """Find available meeting times for attendees.

    Args:
        arguments: Tool arguments matching FindMeetingTimesInput schema.

    Returns:
        Formatted list of meeting time suggestions.
    """
    try:
        input_data = FindMeetingTimesInput(**arguments)
        factory = get_factory()
        availability_service = factory.get_availability_service()
        timezone_name = get_system_timezone_name()

        # Build attendees list
        attendees = [
            {"emailAddress": {"address": email}, "type": "required"}
            for email in input_data.attendees
        ]

        # Build time constraint if date range specified
        time_constraint = None
        if input_data.date_keyword:
            start_dt, end_dt = parse_date_keyword_to_range(input_data.date_keyword)
            time_constraint = {
                "activityDomain": "work",
                "timeSlots": [
                    {
                        "start": {
                            "dateTime": format_datetime_for_graph(start_dt),
                            "timeZone": timezone_name,
                        },
                        "end": {
                            "dateTime": format_datetime_for_graph(end_dt),
                            "timeZone": timezone_name,
                        },
                    }
                ],
            }
        elif input_data.start_date and input_data.end_date:
            time_constraint = {
                "activityDomain": "work",
                "timeSlots": [
                    {
                        "start": {
                            "dateTime": input_data.start_date,
                            "timeZone": timezone_name,
                        },
                        "end": {
                            "dateTime": input_data.end_date,
                            "timeZone": timezone_name,
                        },
                    }
                ],
            }

        result = await availability_service.find_meeting_times(
            attendees=attendees,
            time_constraint=time_constraint,
            meeting_duration=input_data.duration,
            max_candidates=input_data.max_candidates,
        )

        return formatters.format_meeting_suggestions(result)

    except Exception as e:
        return formatters.format_error(e, "outlook_find_meeting_times")


async def outlook_get_emails(arguments: Dict[str, Any]) -> str:
    """Get emails from a mail folder.

    Args:
        arguments: Tool arguments matching GetEmailsInput schema.

    Returns:
        Formatted list of emails.
    """
    try:
        input_data = GetEmailsInput(**arguments)
        factory = get_factory()
        mail_service = factory.get_mail_service()

        result = await mail_service.get_messages_delta(
            folder_id=input_data.folder,
            top=input_data.max_results,
            use_cache=False,  # MCP always fetches fresh
            follow_pagination=False,  # Single page for MCP
        )

        messages = result.get("value", [])
        return formatters.format_emails(messages)

    except Exception as e:
        return formatters.format_error(e, "outlook_get_emails")


async def outlook_create_draft(arguments: Dict[str, Any]) -> str:
    """Create a draft email.

    Args:
        arguments: Tool arguments matching CreateDraftInput schema.

    Returns:
        Confirmation of created draft.
    """
    try:
        input_data = CreateDraftInput(**arguments)
        factory = get_factory()
        mail_service = factory.get_mail_service()

        # Build recipients list
        to_recipients = [{"address": email} for email in input_data.to_recipients]
        cc_recipients = None
        if input_data.cc_recipients:
            cc_recipients = [{"address": email} for email in input_data.cc_recipients]

        draft = await mail_service.create_draft(
            subject=input_data.subject,
            body_content=input_data.body,
            body_content_type=input_data.body_type,
            to_recipients=to_recipients,
            cc_recipients=cc_recipients,
        )

        return formatters.format_created_draft(draft)

    except Exception as e:
        return formatters.format_error(e, "outlook_create_draft")


# Tool registry for the MCP server
TOOL_HANDLERS = {
    "outlook_get_events": outlook_get_events,
    "outlook_create_event": outlook_create_event,
    "outlook_find_meeting_times": outlook_find_meeting_times,
    "outlook_get_emails": outlook_get_emails,
    "outlook_create_draft": outlook_create_draft,
}
