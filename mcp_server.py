#!/usr/bin/env python3
"""MCP server entry point for Outlook integration.

This script starts the MCP server with stdio transport, enabling Claude Code
to interact with Microsoft Graph API for Outlook calendar, mail, and contacts.

Usage:
    python mcp_server.py

Or via uv:
    uv run mcp_server.py

Claude Code configuration (.mcp.json):
    {
        "mcpServers": {
            "outlook": {
                "command": "uv",
                "args": ["--directory", "/path/to/tana-connector", "run", "mcp_server.py"]
            }
        }
    }
"""

import asyncio

import mcp.server.stdio
from mcp.server.models import InitializationOptions
from mcp.server.lowlevel import NotificationOptions

from app.config import validate_config
from app.mcp.server import mcp_server


async def main() -> None:
    """Run the MCP server with stdio transport."""
    # Validate configuration before starting
    validate_config()

    # Run the server with stdio transport
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="outlook-mcp",
                server_version="0.1.0",
                capabilities=mcp_server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
