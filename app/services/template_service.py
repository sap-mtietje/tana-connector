"""Template rendering service using Jinja2."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from jinja2 import Environment, TemplateSyntaxError, UndefinedError

from app.exceptions import TemplateError
from app.utils.description_utils import process_description


class TemplateService:
    """Handles Jinja2 template rendering for MS Graph data (events, messages, etc.)"""

    def __init__(self):
        """Initialize Jinja2 environment with custom filters"""
        self.env = Environment(
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Register custom filters
        self.env.filters["clean"] = self._clean_filter
        self.env.filters["truncate"] = self._truncate_filter
        self.env.filters["date_format"] = self._date_format_filter

    def render_template(
        self,
        template_string: str,
        events: List[Dict[str, Any]],
        start_date: str,
        end_date: str,
    ) -> str:
        """
        Render a Jinja2 template with events data (legacy method for calendar).

        Args:
            template_string: Jinja2 template as string
            events: List of event dictionaries
            start_date: Start date string (YYYY-MM-DD)
            end_date: End date string (YYYY-MM-DD)

        Returns:
            Rendered template as string

        Raises:
            TemplateSyntaxError: If template has syntax errors
            UndefinedError: If template references undefined variables
            ValueError: If template rendering fails
        """
        return self.render(
            template_string=template_string,
            events=events,
            count=len(events),
            start_date=start_date,
            end_date=end_date,
        )

    def render(self, template_string: str, **context) -> str:
        """
        Render a Jinja2 template with arbitrary context.

        This is the generic method that supports any data type.
        Use this for mail messages, or any other MS Graph data.

        Args:
            template_string: Jinja2 template as string
            **context: Arbitrary keyword arguments passed to template
                       Common patterns:
                       - messages=[], count=N for mail
                       - events=[], count=N, start_date, end_date for calendar

        Returns:
            Rendered template as string

        Raises:
            TemplateError: If template has syntax errors or rendering fails

        Example:
            # For mail messages
            template_service.render(
                template_string=template,
                messages=messages,
                count=len(messages),
                folder="inbox",
            )
        """
        try:
            template = self.env.from_string(template_string)
            rendered = template.render(**context)
            return rendered

        except TemplateSyntaxError as e:
            raise TemplateError(
                message=f"Template syntax error: {e.message}",
                line_number=e.lineno,
                details={
                    "template_snippet": template_string[:200]
                    if template_string
                    else None
                },
            )
        except UndefinedError as e:
            raise TemplateError(
                message=f"Undefined variable in template: {str(e)}",
                details={
                    "template_snippet": template_string[:200]
                    if template_string
                    else None
                },
            )
        except Exception as e:
            raise TemplateError(
                message=f"Template rendering failed: {str(e)}",
                details={"error_type": type(e).__name__},
            )

    @staticmethod
    def _clean_filter(text: str) -> str:
        """
        Clean description text (equivalent to descriptionMode=clean)

        Usage in template: {{ event.description | clean }}
        """
        if not text:
            return ""
        return process_description(text, mode="clean")

    @staticmethod
    def _truncate_filter(text: str, length: int = 100) -> str:
        """
        Truncate text to specified length

        Usage in template: {{ event.description | truncate(200) }}
        """
        if not text:
            return ""
        if len(text) <= length:
            return text
        return text[:length].rsplit(" ", 1)[0] + "..."

    @staticmethod
    def _date_format_filter(
        date_string: str, format_spec: str = "%Y-%m-%d %H:%M"
    ) -> str:
        """
        Format datetime string

        Usage in template: {{ event.start | date_format("%Y-%m-%d") }}
        """
        if not date_string:
            return ""

        try:
            # Handle ISO format from Graph API
            clean_str = date_string.replace("Z", "").replace(".0000000", "")
            if "T" in clean_str:
                dt = datetime.fromisoformat(clean_str)
                return dt.strftime(format_spec)
            return date_string
        except Exception:
            return date_string
