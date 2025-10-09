"""Template rendering service using Jinja2"""

from typing import Any, Dict, List
from jinja2 import Environment, StrictUndefined, TemplateSyntaxError, UndefinedError
from app.services.events_service import events_service


class TemplateService:
    """Handles Jinja2 template rendering for events data"""

    def __init__(self):
        """Initialize Jinja2 environment with custom filters"""
        self.env = Environment(
            undefined=StrictUndefined,  # Fail on undefined variables
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
        Render a Jinja2 template with events data

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
        try:
            template = self.env.from_string(template_string)

            context = {
                "events": events,
                "count": len(events),
                "start_date": start_date,
                "end_date": end_date,
            }

            rendered = template.render(**context)
            return rendered

        except TemplateSyntaxError as e:
            raise ValueError(f"Template syntax error at line {e.lineno}: {e.message}")
        except UndefinedError as e:
            raise ValueError(f"Undefined variable in template: {str(e)}")
        except Exception as e:
            raise ValueError(f"Template rendering failed: {str(e)}")

    @staticmethod
    def _clean_filter(text: str) -> str:
        """
        Clean description text (equivalent to descriptionMode=clean)

        Usage in template: {{ event.description | clean }}
        """
        if not text:
            return ""
        return events_service.process_description(text, mode="clean")

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
            from datetime import datetime

            clean_str = date_string.replace("Z", "").replace(".0000000", "")
            if "T" in clean_str:
                dt = datetime.fromisoformat(clean_str)
                return dt.strftime(format_spec)
            return date_string
        except Exception:
            return date_string


template_service = TemplateService()
