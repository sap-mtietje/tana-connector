"""Utilities for processing event descriptions"""

import re
from typing import Optional

from app.constants import DESCRIPTION_CLEANUP_PATTERNS, HTML_ENTITIES, MEETING_DOMAINS


def process_description(
    description: str, mode: str = "full", max_length: Optional[int] = None
) -> str:
    """Process description: full (default), clean (remove meeting links/HTML), or none.

    Clean mode decodes HTML entities, removes meeting/conference details and links for
    known platforms, preserves non-meeting links by appending them under a "Links:" section,
    and performs aggressive whitespace cleanup. Truncation is applied at a word boundary.
    """
    if not description or mode == "none":
        return ""

    result = description

    # Decode HTML entities (for all modes)
    for entity, char in HTML_ENTITIES.items():
        result = result.replace(entity, char)

    # Decode numeric HTML entities (&#1234; and &#x1234;)
    result = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), result)
    result = re.sub(r"&#x([0-9a-fA-F]+);", lambda m: chr(int(m.group(1), 16)), result)

    if mode == "clean":
        # Step 1: Extract and preserve non-meeting links
        all_links = re.findall(r"https?://[^\s]+", result)
        preserved_links = []
        for link in all_links:
            is_meeting_link = any(domain in link.lower() for domain in MEETING_DOMAINS)
            if not is_meeting_link:
                preserved_links.append(link)

        # Step 2: Apply cleanup patterns
        for pattern in DESCRIPTION_CLEANUP_PATTERNS:
            result = re.sub(pattern, "", result, flags=re.IGNORECASE | re.DOTALL)

        # Step 3: Aggressive whitespace cleanup
        # Normalize line endings
        result = result.replace("\r\n", "\n").replace("\r", "\n")

        # Remove lines that are just whitespace
        lines = [line.rstrip() for line in result.split("\n")]
        result = "\n".join(lines)

        # Collapse multiple blank lines to max 1
        result = re.sub(r"\n\s*\n\s*\n+", "\n\n", result)

        # Remove multiple spaces
        result = re.sub(r" +", " ", result)

        # Remove trailing/leading whitespace on each line; drop empty lines
        lines = [line.strip() for line in result.split("\n")]
        result = "\n".join(line for line in lines if line)

        # Step 4: Add preserved links back (if any and if there's content)
        if preserved_links and result.strip():
            result = result.strip() + "\n\nLinks:\n" + "\n".join(preserved_links)
        elif preserved_links and not result.strip():
            # If no content but there are links, just show the links
            result = "Links:\n" + "\n".join(preserved_links)

    # Truncate if needed
    if max_length and len(result) > max_length:
        result = result[:max_length].rsplit(" ", 1)[0] + "..."

    return result.strip()
