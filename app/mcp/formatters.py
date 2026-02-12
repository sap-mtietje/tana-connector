"""Response formatters for flattening MS Graph responses for MCP tools."""

from __future__ import annotations

import json
from typing import Any, Dict, List


def format_events(events: List[Dict[str, Any]]) -> str:
    """Format calendar events for readable output.

    Flattens nested MS Graph event structure into a concise format.
    """
    if not events:
        return "No events found."

    lines = []
    for i, event in enumerate(events, 1):
        subject = event.get("subject", "Untitled")
        start = event.get("start", {}).get("dateTime", "")
        end = event.get("end", {}).get("dateTime", "")
        location = event.get("location", {}).get("displayName", "")
        is_online = event.get("isOnlineMeeting", False)
        join_url = event.get("onlineMeeting", {}).get("joinUrl", "")

        lines.append(f"## {i}. {subject}")
        lines.append(f"- **When**: {start} to {end}")

        if location:
            lines.append(f"- **Where**: {location}")
        if is_online and join_url:
            lines.append(f"- **Teams Link**: {join_url}")

        # Attendees
        attendees = event.get("attendees", [])
        if attendees:
            names = []
            for att in attendees:
                email_info = att.get("emailAddress", {})
                name = email_info.get("name") or email_info.get("address", "")
                if name:
                    names.append(name)
            if names:
                lines.append(f"- **Attendees**: {', '.join(names)}")

        # Show as (availability)
        show_as = event.get("showAs")
        if show_as:
            lines.append(f"- **Status**: {show_as}")

        lines.append("")  # Blank line between events

    return "\n".join(lines)


def format_created_event(event: Dict[str, Any]) -> str:
    """Format a newly created event for confirmation output."""
    subject = event.get("subject", "Untitled")
    start = event.get("start", {}).get("dateTime", "")
    end = event.get("end", {}).get("dateTime", "")
    web_link = event.get("webLink", "")
    is_online = event.get("isOnlineMeeting", False)
    join_url = event.get("onlineMeeting", {}).get("joinUrl", "")

    lines = [
        f"Event created: **{subject}**",
        f"- **When**: {start} to {end}",
    ]

    if is_online and join_url:
        lines.append(f"- **Teams Link**: {join_url}")

    if web_link:
        lines.append(f"- **View in Outlook**: {web_link}")

    return "\n".join(lines)


def format_meeting_suggestions(result: Dict[str, Any]) -> str:
    """Format find meeting times results for readable output."""
    suggestions = result.get("meetingTimeSuggestions", [])

    if not suggestions:
        reason = result.get("emptySuggestionsReason", "No available times found")
        return f"No available meeting times found. Reason: {reason}"

    lines = ["## Available Meeting Times\n"]

    for i, sugg in enumerate(suggestions, 1):
        slot = sugg.get("meetingTimeSlot", {})
        start = slot.get("start", {}).get("dateTime", "")
        end = slot.get("end", {}).get("dateTime", "")
        confidence = sugg.get("confidence", 0)
        org_avail = sugg.get("organizerAvailability", "")

        lines.append(f"### Option {i}")
        lines.append(f"- **Time**: {start} to {end}")
        lines.append(f"- **Confidence**: {confidence}%")
        if org_avail:
            lines.append(f"- **Your availability**: {org_avail}")

        # Attendee availability
        att_avail = sugg.get("attendeeAvailability", [])
        if att_avail:
            for att in att_avail:
                attendee = att.get("attendee", {})
                email = attendee.get("emailAddress", {}).get("address", "")
                availability = att.get("availability", "")
                if email:
                    lines.append(f"  - {email}: {availability}")

        lines.append("")  # Blank line

    return "\n".join(lines)


def format_emails(messages: List[Dict[str, Any]]) -> str:
    """Format email messages for readable output."""
    if not messages:
        return "No emails found."

    lines = []
    for i, msg in enumerate(messages, 1):
        # Skip deleted messages
        if "@removed" in msg:
            continue

        subject = msg.get("subject", "(No subject)")
        from_addr = msg.get("from", {}).get("emailAddress", {})
        sender = from_addr.get("name") or from_addr.get("address", "Unknown")
        received = msg.get("receivedDateTime", "")
        is_read = msg.get("isRead", False)
        preview = msg.get("bodyPreview", "")[:150]
        if len(msg.get("bodyPreview", "")) > 150:
            preview += "..."

        read_status = "" if is_read else " 📩"
        lines.append(f"## {i}. {subject}{read_status}")
        lines.append(f"- **From**: {sender}")
        lines.append(f"- **Received**: {received}")
        if preview:
            lines.append(f"- **Preview**: {preview}")
        lines.append("")

    if not lines:
        return "No emails found (only deleted items in response)."

    return "\n".join(lines)


def format_created_draft(draft: Dict[str, Any]) -> str:
    """Format a newly created draft for confirmation output."""
    subject = draft.get("subject", "(No subject)")
    web_link = draft.get("webLink", "")

    to_recipients = draft.get("toRecipients", [])
    recipients = []
    for r in to_recipients:
        email = r.get("emailAddress", {}).get("address", "")
        if email:
            recipients.append(email)

    lines = [
        f"Draft created: **{subject}**",
        f"- **To**: {', '.join(recipients) if recipients else 'None'}",
    ]

    if web_link:
        lines.append(f"- **Open in Outlook**: {web_link}")

    return "\n".join(lines)


def format_error(error: Exception, tool_name: str) -> str:
    """Format an error for user-friendly output."""
    error_type = type(error).__name__
    return f"Error in {tool_name}: {error_type} - {str(error)}"


def to_json(data: Any) -> str:
    """Convert data to pretty JSON string."""
    return json.dumps(data, indent=2, default=str)
