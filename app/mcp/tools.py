"""MCP tool implementations wrapping existing services."""

from __future__ import annotations

import json
from typing import Any, Dict

from app.mcp import default_templates
from app.mcp.schemas import (
    CreateDraftInput,
    CreateEventInput,
    FindMeetingTimesInput,
    GetEmailsInput,
    GetEventsInput,
)
from app.mcp.service_factory import get_factory
from app.models.filters import (
    Importance,
    ResponseStatus,
    Sensitivity,
    ShowAs,
    build_odata_filter,
)
from app.utils.date_utils import parse_date_keyword_to_range
from app.utils.filter_utils import apply_filter
from app.utils.timezone_utils import format_datetime_for_graph, get_system_timezone_name


def _render(template_string: str, **context) -> str:
    """Render a Jinja2 template using the shared TemplateService."""
    factory = get_factory()
    template_service = factory.get_template_service()
    return template_service.render(template_string=template_string, **context)


def _error_json(error: Exception, tool_name: str) -> str:
    """Serialize an error as JSON for consistent MCP error responses."""
    return json.dumps(
        {
            "error": True,
            "tool": tool_name,
            "error_type": type(error).__name__,
            "message": str(error),
        },
        indent=2,
    )


async def outlook_get_events(arguments: Dict[str, Any]) -> str:
    """Get calendar events for a date range.

    Args:
        arguments: Tool arguments matching GetEventsInput schema.

    Returns:
        Rendered string of calendar events.
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
            return json.dumps(
                {
                    "error": True,
                    "message": "Must provide either date_keyword or both start_date and end_date",
                }
            )

        # Build OData filter from friendly params + raw filter
        combined_filter = build_odata_filter(
            base_filter=input_data.filter,
            importance=Importance(input_data.importance)
            if input_data.importance
            else None,
            sensitivity=Sensitivity(input_data.sensitivity)
            if input_data.sensitivity
            else None,
            show_as=ShowAs(input_data.show_as) if input_data.show_as else None,
            is_all_day=input_data.is_all_day,
            is_cancelled=input_data.is_cancelled,
            is_online_meeting=input_data.is_online_meeting,
            has_attachments=input_data.has_attachments,
            response_status=ResponseStatus(input_data.response_status)
            if input_data.response_status
            else None,
            categories=input_data.categories,
        )

        events = await calendar_service.get_calendar_view(
            start_date_time=start_date,
            end_date_time=end_date,
            filter=combined_filter,
            orderby=input_data.orderby,
            top=input_data.max_results,
            skip=input_data.skip,
        )

        template = input_data.template or default_templates.GET_EVENTS
        return _render(template, events=events, count=len(events))

    except Exception as e:
        return _error_json(e, "outlook_get_events")


async def outlook_create_event(arguments: Dict[str, Any]) -> str:
    """Create a new calendar event.

    Args:
        arguments: Tool arguments matching CreateEventInput schema.

    Returns:
        Rendered string of the created event.
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
            body = {"contentType": input_data.body_type, "content": input_data.body}

        event = await calendar_service.create_event(
            subject=input_data.subject,
            start=start,
            end=end,
            attendees=attendees,
            is_online_meeting=input_data.is_online_meeting,
            location=location,
            body=body,
            is_all_day=input_data.is_all_day,
            categories=input_data.categories,
            importance=input_data.importance,
            sensitivity=input_data.sensitivity,
            show_as=input_data.show_as,
            reminder_minutes_before_start=input_data.reminder_minutes_before_start,
        )

        template = input_data.template or default_templates.CREATE_EVENT
        return _render(template, event=event)

    except Exception as e:
        return _error_json(e, "outlook_create_event")


async def outlook_find_meeting_times(arguments: Dict[str, Any]) -> str:
    """Find available meeting times for attendees.

    Args:
        arguments: Tool arguments matching FindMeetingTimesInput schema.

    Returns:
        Rendered string of meeting time suggestions.
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
                "activityDomain": input_data.activity_domain,
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
                "activityDomain": input_data.activity_domain,
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
            is_organizer_optional=input_data.is_organizer_optional,
            return_suggestion_reasons=input_data.return_suggestion_reasons,
            minimum_attendee_percentage=input_data.minimum_attendee_percentage,
        )

        suggestions = result.get("meetingTimeSuggestions", [])
        empty_reason = result.get("emptySuggestionsReason", "")
        template = input_data.template or default_templates.FIND_MEETING_TIMES
        return _render(
            template,
            suggestions=suggestions,
            count=len(suggestions),
            empty_suggestions_reason=empty_reason,
        )

    except Exception as e:
        return _error_json(e, "outlook_find_meeting_times")


async def outlook_get_emails(arguments: Dict[str, Any]) -> str:
    """Get emails from a mail folder.

    Args:
        arguments: Tool arguments matching GetEmailsInput schema.

    Returns:
        Rendered string of email messages.
    """
    try:
        input_data = GetEmailsInput(**arguments)
        factory = get_factory()
        mail_service = factory.get_mail_service()

        result = await mail_service.get_messages_delta(
            folder_id=input_data.folder,
            filter=input_data.filter,
            top=input_data.max_results,
            use_cache=input_data.use_cache,
            follow_pagination=input_data.follow_pagination,
        )

        messages = result.get("value", [])

        # Apply post-fetch filter if specified
        if input_data.post_filter:
            messages = apply_filter(messages, input_data.post_filter)

        template = input_data.template or default_templates.GET_EMAILS
        return _render(
            template,
            messages=messages,
            count=len(messages),
            folder=input_data.folder,
        )

    except Exception as e:
        return _error_json(e, "outlook_get_emails")


async def outlook_create_draft(arguments: Dict[str, Any]) -> str:
    """Create a draft email.

    Args:
        arguments: Tool arguments matching CreateDraftInput schema.

    Returns:
        Rendered string of the created draft.
    """
    try:
        input_data = CreateDraftInput(**arguments)
        factory = get_factory()
        mail_service = factory.get_mail_service()

        # Build recipients lists
        to_recipients = [{"address": email} for email in input_data.to_recipients]
        cc_recipients = None
        if input_data.cc_recipients:
            cc_recipients = [{"address": email} for email in input_data.cc_recipients]
        bcc_recipients = None
        if input_data.bcc_recipients:
            bcc_recipients = [{"address": email} for email in input_data.bcc_recipients]

        draft = await mail_service.create_draft(
            subject=input_data.subject,
            body_content=input_data.body,
            body_content_type=input_data.body_type,
            to_recipients=to_recipients,
            cc_recipients=cc_recipients,
            bcc_recipients=bcc_recipients,
            importance=input_data.importance,
        )

        template = input_data.template or default_templates.CREATE_DRAFT
        return _render(template, draft=draft)

    except Exception as e:
        return _error_json(e, "outlook_create_draft")


# Tool registry for the MCP server
TOOL_HANDLERS = {
    "outlook_get_events": outlook_get_events,
    "outlook_create_event": outlook_create_event,
    "outlook_find_meeting_times": outlook_find_meeting_times,
    "outlook_get_emails": outlook_get_emails,
    "outlook_create_draft": outlook_create_draft,
}
