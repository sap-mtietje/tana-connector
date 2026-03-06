"""Pydantic schemas for MCP tool inputs with Claude-friendly descriptions."""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

_TEMPLATE_DESCRIPTION = (
    "Optional Jinja2 template to control output format. "
    "If omitted, a sensible default template is used. "
    "Available filters: clean (strip HTML), truncate(n) (truncate to n chars), "
    "date_format(fmt) (format ISO datetime). "
    "Example: '{% for e in events %}{{ e.subject }}\\n{% endfor %}'."
)


class GetEventsInput(BaseModel):
    """Input schema for outlook_get_events tool."""

    date_keyword: Optional[
        Literal["today", "tomorrow", "this-week", "next-week", "this-month"]
    ] = Field(
        default=None,
        description="Convenience date range keyword. Use this OR start_date/end_date.",
    )
    start_date: Optional[str] = Field(
        default=None,
        description="Start date/time in ISO format (e.g., '2024-12-10T00:00:00'). Required if date_keyword not provided.",
    )
    end_date: Optional[str] = Field(
        default=None,
        description="End date/time in ISO format (e.g., '2024-12-10T23:59:59'). Required if date_keyword not provided.",
    )
    max_results: int = Field(
        default=25,
        ge=1,
        le=100,
        description="Maximum number of events to return.",
    )
    filter: Optional[str] = Field(
        default=None,
        description="Raw OData filter expression for advanced filtering (e.g., \"contains(subject, 'standup')\").",
    )
    orderby: Optional[List[str]] = Field(
        default=None,
        description="Sort fields (e.g., ['start/dateTime', 'subject']).",
    )
    skip: Optional[int] = Field(
        default=None,
        ge=0,
        description="Pagination offset — number of events to skip.",
    )
    importance: Optional[Literal["low", "normal", "high"]] = Field(
        default=None,
        description="Filter by importance level.",
    )
    sensitivity: Optional[Literal["normal", "personal", "private", "confidential"]] = (
        Field(
            default=None,
            description="Filter by sensitivity level.",
        )
    )
    show_as: Optional[
        Literal["free", "tentative", "busy", "oof", "workingElsewhere"]
    ] = Field(
        default=None,
        description="Filter by free/busy status.",
    )
    response_status: Optional[
        Literal[
            "none",
            "organizer",
            "tentativelyAccepted",
            "accepted",
            "declined",
            "notResponded",
        ]
    ] = Field(
        default=None,
        description="Filter by your response status.",
    )
    is_all_day: Optional[bool] = Field(
        default=None,
        description="Filter for all-day events (true) or timed events (false).",
    )
    is_online_meeting: Optional[bool] = Field(
        default=None,
        description="Filter for online meetings.",
    )
    is_cancelled: Optional[bool] = Field(
        default=None,
        description="Filter for cancelled events.",
    )
    has_attachments: Optional[bool] = Field(
        default=None,
        description="Filter for events with attachments.",
    )
    categories: Optional[List[str]] = Field(
        default=None,
        description="Filter by category names (OR logic — matches any listed category).",
    )
    template: Optional[str] = Field(
        default=None,
        description=_TEMPLATE_DESCRIPTION
        + " Context variables: events (list), count (int).",
    )


class CreateEventInput(BaseModel):
    """Input schema for outlook_create_event tool."""

    subject: str = Field(
        description="Event title/subject (required).",
    )
    start_time: str = Field(
        description="Start date/time in ISO format (e.g., '2024-12-10T09:00:00').",
    )
    end_time: str = Field(
        description="End date/time in ISO format (e.g., '2024-12-10T10:00:00').",
    )
    attendees: Optional[List[str]] = Field(
        default=None,
        description="List of attendee email addresses.",
    )
    is_online_meeting: bool = Field(
        default=False,
        description="Create as Teams online meeting.",
    )
    location: Optional[str] = Field(
        default=None,
        description="Meeting location (room name or address).",
    )
    body: Optional[str] = Field(
        default=None,
        description="Event body/description content.",
    )
    body_type: Literal["HTML", "Text"] = Field(
        default="HTML",
        description="Content type of the body field.",
    )
    is_all_day: bool = Field(
        default=False,
        description="Create as an all-day event.",
    )
    categories: Optional[List[str]] = Field(
        default=None,
        description="Category names to assign to the event.",
    )
    importance: Optional[Literal["low", "normal", "high"]] = Field(
        default=None,
        description="Event importance level.",
    )
    sensitivity: Optional[Literal["normal", "personal", "private", "confidential"]] = (
        Field(
            default=None,
            description="Event sensitivity/privacy level.",
        )
    )
    show_as: Optional[
        Literal["free", "tentative", "busy", "oof", "workingElsewhere"]
    ] = Field(
        default=None,
        description="How to show the time on your calendar.",
    )
    reminder_minutes_before_start: Optional[int] = Field(
        default=None,
        ge=0,
        description="Minutes before event to trigger a reminder.",
    )
    template: Optional[str] = Field(
        default=None,
        description=_TEMPLATE_DESCRIPTION + " Context variables: event (dict).",
    )


class FindMeetingTimesInput(BaseModel):
    """Input schema for outlook_find_meeting_times tool."""

    attendees: List[str] = Field(
        description="List of attendee email addresses (required).",
    )
    date_keyword: Optional[Literal["today", "tomorrow", "this-week", "next-week"]] = (
        Field(
            default=None,
            description="Convenience date range to search within.",
        )
    )
    start_date: Optional[str] = Field(
        default=None,
        description="Start of search window in ISO format. Used if date_keyword not provided.",
    )
    end_date: Optional[str] = Field(
        default=None,
        description="End of search window in ISO format. Used if date_keyword not provided.",
    )
    duration: str = Field(
        default="PT1H",
        description="Meeting duration in ISO 8601 format (e.g., 'PT30M' for 30 min, 'PT1H' for 1 hour).",
    )
    max_candidates: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of meeting time suggestions to return.",
    )
    is_organizer_optional: bool = Field(
        default=False,
        description="Whether the organizer's attendance is optional.",
    )
    return_suggestion_reasons: bool = Field(
        default=True,
        description="Include reason text explaining why each time was suggested.",
    )
    minimum_attendee_percentage: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Minimum percentage of attendees that must be available (0-100).",
    )
    activity_domain: Literal["work", "personal", "unrestricted"] = Field(
        default="work",
        description="Activity domain for the time constraint — controls which hours are considered.",
    )
    template: Optional[str] = Field(
        default=None,
        description=_TEMPLATE_DESCRIPTION
        + " Context variables: suggestions (list), count (int), empty_suggestions_reason (str).",
    )


class GetEmailsInput(BaseModel):
    """Input schema for outlook_get_emails tool."""

    folder: Literal["inbox", "sent", "drafts", "deleted", "junk", "archive"] = Field(
        default="inbox",
        description="Mail folder to retrieve emails from.",
    )
    max_results: int = Field(
        default=25,
        ge=1,
        le=100,
        description="Maximum number of emails to return.",
    )
    filter: Optional[str] = Field(
        default=None,
        description="OData filter expression for server-side filtering (e.g., \"importance eq 'high'\").",
    )
    post_filter: Optional[str] = Field(
        default=None,
        description=(
            "Post-fetch filter using field:operator:value syntax. "
            "Operators: eq, ne, contains, startswith, endswith, gt, lt, exists. "
            "Multiple conditions comma-separated (AND logic). "
            "Examples: 'isRead:eq:false', 'from.emailAddress.address:contains:@sap.com', "
            "'categories:eq:important,hasAttachments:eq:true'."
        ),
    )
    use_cache: bool = Field(
        default=False,
        description="Use delta token caching for incremental sync.",
    )
    follow_pagination: bool = Field(
        default=False,
        description="Follow pagination links to retrieve all pages of results.",
    )
    template: Optional[str] = Field(
        default=None,
        description=_TEMPLATE_DESCRIPTION
        + " Context variables: messages (list), count (int), folder (str).",
    )


class CreateDraftInput(BaseModel):
    """Input schema for outlook_create_draft tool."""

    subject: str = Field(
        description="Email subject line (required).",
    )
    body: str = Field(
        description="Email body content in HTML or plain text (required).",
    )
    to_recipients: List[str] = Field(
        description="List of recipient email addresses (required).",
    )
    cc_recipients: Optional[List[str]] = Field(
        default=None,
        description="List of CC recipient email addresses.",
    )
    bcc_recipients: Optional[List[str]] = Field(
        default=None,
        description="List of BCC recipient email addresses.",
    )
    body_type: Literal["HTML", "Text"] = Field(
        default="HTML",
        description="Content type of the email body.",
    )
    importance: Optional[Literal["low", "normal", "high"]] = Field(
        default=None,
        description="Email importance/priority level.",
    )
    template: Optional[str] = Field(
        default=None,
        description=_TEMPLATE_DESCRIPTION + " Context variables: draft (dict).",
    )
