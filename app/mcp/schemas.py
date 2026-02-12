"""Pydantic schemas for MCP tool inputs with Claude-friendly descriptions."""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


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
        description="Event body/description in HTML format.",
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
    body_type: Literal["HTML", "Text"] = Field(
        default="HTML",
        description="Content type of the email body.",
    )
