"""Utilities for processing event descriptions"""

import re
from typing import Optional

from bs4 import BeautifulSoup


def strip_html(html: str) -> str:
    """
    Strip HTML tags and extract clean text using BeautifulSoup.

    Handles:
    - Removes script/style tags and their content
    - Extracts text from all other tags
    - Preserves reasonable whitespace
    """
    if not html:
        return ""

    # Parse HTML (lxml is faster, falls back to html.parser)
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    # Remove script and style elements entirely
    for element in soup(["script", "style", "head", "meta", "link"]):
        element.decompose()

    # Get text with reasonable separator
    text = soup.get_text(separator=" ")

    return text


def process_description(
    description: str, mode: str = "full", max_length: Optional[int] = None
) -> str:
    """Process description: full (default), clean (strip HTML), or none.

    Clean mode:
    - Strips all HTML tags using BeautifulSoup
    - Removes # characters to prevent accidental Tana supertag creation
    - Performs whitespace cleanup
    - Truncation is applied at a word boundary
    """
    if not description or mode == "none":
        return ""

    result = description

    if mode == "clean":
        # Step 1: Strip HTML using BeautifulSoup
        result = strip_html(result)

        # Step 2: Replace newlines with spaces (critical for Tana Paste single-line fields)
        result = result.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")

        # Step 3: Add space after # to prevent Tana supertag creation
        result = result.replace("#", "# ")

        # Collapse multiple spaces
        result = re.sub(r" +", " ", result)

    # Truncate if needed
    if max_length and len(result) > max_length:
        result = result[:max_length].rsplit(" ", 1)[0] + "..."

    return result.strip()
