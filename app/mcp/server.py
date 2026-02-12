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
                "Use date_keyword for common ranges (today, tomorrow, this-week, next-week, this-month) "
                "or provide explicit start_date and end_date in ISO format."
            ),
            inputSchema=_get_json_schema(GetEventsInput),
        ),
        Tool(
            name="outlook_create_event",
            description=(
                "Create a new calendar event in Microsoft Outlook. "
                "Specify subject, start_time, and end_time (ISO format). "
                "Optionally add attendees (email addresses), set is_online_meeting=true for Teams, "
                "and include location or body content."
            ),
            inputSchema=_get_json_schema(CreateEventInput),
        ),
        Tool(
            name="outlook_find_meeting_times",
            description=(
                "Find available meeting times when all specified attendees are free. "
                "Provide a list of attendee email addresses and optionally constrain the search "
                "with date_keyword or start_date/end_date. Returns ranked suggestions with confidence scores."
            ),
            inputSchema=_get_json_schema(FindMeetingTimesInput),
        ),
        Tool(
            name="outlook_get_emails",
            description=(
                "Get emails from a Microsoft Outlook mail folder. "
                "Specify folder (inbox, sent, drafts, deleted, junk, archive) and max_results. "
                "Returns subject, sender, received date, and preview for each email."
            ),
            inputSchema=_get_json_schema(GetEmailsInput),
        ),
        Tool(
            name="outlook_create_draft",
            description=(
                "Create a draft email in Microsoft Outlook without sending. "
                "Specify subject, body content, and to_recipients (email addresses). "
                "Optionally add cc_recipients and set body_type (HTML or Text)."
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
