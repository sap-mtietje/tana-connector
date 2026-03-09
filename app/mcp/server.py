"""MCP server with stdio transport for Outlook integration."""

from __future__ import annotations

from mcp.server.lowlevel import Server
from mcp.types import TextContent, Tool

from app.mcp.schemas import (
    CreateDraftInput,
    CreateEventInput,
    FindMeetingTimesInput,
    GetEmailsInput,
    GetEventsInput,
)
from app.mcp.tools import TOOL_HANDLERS

# Create the MCP server instance
mcp_server = Server("outlook-mcp")


def _get_json_schema(model) -> dict:
    """Get JSON schema from a Pydantic model, compatible with MCP."""
    schema = model.model_json_schema()
    # Remove title and description from root to keep it clean
    schema.pop("title", None)
    return schema


@mcp_server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """Return the list of available tools."""
    return [
        Tool(
            name="outlook_get_events",
            description=(
                "Get calendar events from Microsoft Outlook for a specified date range. "
                "Returns all event fields (id, subject, body, attendees with RSVP status, "
                "organizer, categories, importance, sensitivity, recurrence, webLink, etc.) "
                "rendered via a default template. Body HTML is cleaned and truncated automatically. "
                "Use date_keyword for common ranges (today, tomorrow, this-week, next-week, this-month) "
                "or provide explicit start_date and end_date in ISO format. "
                "Supports filtering by importance, sensitivity, show_as, response_status, "
                "is_all_day, is_online_meeting, is_cancelled, has_attachments, and categories. "
                "Pass a custom Jinja2 template to control the output format."
            ),
            inputSchema=_get_json_schema(GetEventsInput),
        ),
        Tool(
            name="outlook_create_event",
            description=(
                "Create a new calendar event in Microsoft Outlook. "
                "Specify subject, start_time, and end_time (ISO format). "
                "Optionally add attendees (email addresses), set is_online_meeting=true for Teams, "
                "include location, body content, categories, importance, sensitivity, show_as, "
                "is_all_day, and reminder_minutes_before_start. "
                "Returns the created event including its id. "
                "Pass a custom Jinja2 template to control the output format."
            ),
            inputSchema=_get_json_schema(CreateEventInput),
        ),
        Tool(
            name="outlook_find_meeting_times",
            description=(
                "Find available meeting times when all specified attendees are free. "
                "Provide a list of attendee email addresses and optionally constrain the search "
                "with date_keyword or start_date/end_date. "
                "Supports is_organizer_optional, minimum_attendee_percentage, and activity_domain. "
                "Returns ranked suggestions with confidence scores, attendee availability, "
                "suggestion reasons, and locations. "
                "Pass a custom Jinja2 template to control the output format."
            ),
            inputSchema=_get_json_schema(FindMeetingTimesInput),
        ),
        Tool(
            name="outlook_get_emails",
            description=(
                "Get emails from a Microsoft Outlook mail folder. "
                "Returns all message fields (id, subject, full body cleaned of HTML, "
                "sender, recipients, importance, categories, hasAttachments, webLink, timestamps, etc.) "
                "rendered via a default template. Body HTML is cleaned and truncated automatically. "
                "Specify folder (inbox, sent, drafts, deleted, junk, archive) and max_results. "
                "Supports OData filter for server-side filtering and post_filter for client-side "
                "filtering using field:operator:value syntax "
                "(e.g., 'isRead:eq:false', 'from.emailAddress.address:contains:@sap.com'). "
                "Pass a custom Jinja2 template to control the output format."
            ),
            inputSchema=_get_json_schema(GetEmailsInput),
        ),
        Tool(
            name="outlook_create_draft",
            description=(
                "Create a draft email in Microsoft Outlook without sending. "
                "Specify subject, body content, and to_recipients (email addresses). "
                "Optionally add cc_recipients, bcc_recipients, set body_type (HTML or Text), "
                "and importance. "
                "Returns the created draft including its id. "
                "Pass a custom Jinja2 template to control the output format."
            ),
            inputSchema=_get_json_schema(CreateDraftInput),
        ),
    ]


@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute the requested tool and return results."""
    handler = TOOL_HANDLERS.get(name)

    if handler is None:
        return [TextContent(type="text", text=f"Error: Unknown tool '{name}'")]

    result = await handler(arguments)
    return [TextContent(type="text", text=result)]
