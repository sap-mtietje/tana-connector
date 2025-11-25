"""Events service - Fetches calendar events from Microsoft Graph API"""

import re
from datetime import datetime
from typing import Optional, List, Dict, Any
from msgraph.generated.users.item.calendar_view.calendar_view_request_builder import (
    CalendarViewRequestBuilder,
)
from kiota_abstractions.base_request_configuration import RequestConfiguration

from app.services.graph_service import graph_service
from app.constants import (
    format_enum,
)
from app.utils.timezone_utils import get_system_timezone_name, format_datetime_for_graph
from app.utils.description_utils import process_description as process_description_util


class EventsService:
    """Handles calendar event operations"""

    async def get_events(
        self,
        start_datetime: datetime,
        end_datetime: datetime,
        filter_title: Optional[List[str]] = None,
        filter_attendee: Optional[List[str]] = None,
        filter_status: Optional[List[str]] = None,
        filter_calendar: Optional[str] = None,
        filter_availability: Optional[List[str]] = None,
        filter_categories: Optional[List[str]] = None,
        filter_all_day: Optional[bool] = None,
        exclude_private: bool = True,
    ) -> List[Dict[str, Any]]:
        """Get calendar events from Microsoft Graph API in local timezone"""
        client = await graph_service.get_client()

        start_str = format_datetime_for_graph(start_datetime)
        end_str = format_datetime_for_graph(end_datetime)

        query_params = (
            CalendarViewRequestBuilder.CalendarViewRequestBuilderGetQueryParameters(
                start_date_time=start_str,
                end_date_time=end_str,
            )
        )

        # Auto-detect system timezone
        timezone_name = get_system_timezone_name()

        request_config = RequestConfiguration(query_parameters=query_params)
        request_config.headers.add("Prefer", f'outlook.timezone="{timezone_name}"')

        result = await client.me.calendar_view.get(request_configuration=request_config)

        if not result or not result.value:
            return []

        events = []
        for event in result.value:
            event_data = self._parse_event(event)

            if filter_title and not any(
                t.lower() in event_data["title"].lower() for t in filter_title
            ):
                continue

            if filter_attendee:
                attendees_lower = [a.lower() for a in event_data.get("attendees", [])]
                if not any(
                    att.lower() in attendee
                    for att in filter_attendee
                    for attendee in attendees_lower
                ):
                    continue

            if filter_status and event_data.get("status") not in filter_status:
                continue

            if (
                filter_availability
                and event_data.get("availability") not in filter_availability
            ):
                continue

            if filter_categories:
                event_categories = [
                    cat.lower() for cat in event_data.get("categories", [])
                ]
                filter_categories_lower = [
                    cat.lower().strip() for cat in filter_categories
                ]
                if not any(cat in event_categories for cat in filter_categories_lower):
                    continue

            if filter_all_day is not None:
                is_all_day = event_data.get("is_all_day", False)
                if filter_all_day != is_all_day:
                    continue

            if exclude_private and "private" in [
                cat.lower() for cat in event_data.get("categories", [])
            ]:
                continue

            events.append(event_data)

        return events

    def _parse_event(self, event) -> Dict[str, Any]:
        """Parse Graph API event object to our format"""
        attendees = []
        if event.attendees:
            for attendee in event.attendees:
                if attendee.email_address:
                    name = attendee.email_address.name or attendee.email_address.address
                    if name:
                        attendees.append(name)

        description = ""
        if event.body and event.body.content:
            description = re.sub(r"<[^>]+>", "", event.body.content).strip()

        status = (
            format_enum(str(event.response_status.response))
            if event.response_status and event.response_status.response
            else ""
        )
        availability = format_enum(str(event.show_as)) if event.show_as else ""
        importance = format_enum(str(event.importance)) if event.importance else ""
        sensitivity = format_enum(str(event.sensitivity)) if event.sensitivity else ""

        is_recurring = event.type and str(event.type).lower() in [
            "occurrence",
            "seriesmaster",
        ]
        recurrence_pattern = ""
        if (
            event.recurrence
            and event.recurrence.pattern
            and event.recurrence.pattern.type
        ):
            recurrence_pattern = str(event.recurrence.pattern.type).lower().capitalize()

        online_meeting_url = ""
        if (
            event.is_online_meeting
            and event.online_meeting
            and event.online_meeting.join_url
        ):
            online_meeting_url = event.online_meeting.join_url

        start_dt = event.start.date_time if event.start else None
        end_dt = event.end.date_time if event.end else None

        # Compute combined date range field
        date_range = f"{start_dt}/{end_dt}" if start_dt and end_dt else ""

        return {
            "id": event.id or "",
            "title": event.subject or "Untitled Event",
            "start": start_dt,
            "end": end_dt,
            "date": date_range,
            "location": event.location.display_name if event.location else "",
            "status": status,
            "attendees": attendees,
            "description": description,
            "calendar": "Calendar",
            "availability": availability,
            "is_all_day": event.is_all_day or False,
            "organizer": event.organizer.email_address.address
            if event.organizer and event.organizer.email_address
            else "",
            "categories": list(event.categories) if event.categories else [],
            "web_link": event.web_link or "",
            "is_cancelled": event.is_cancelled or False,
            "is_online_meeting": event.is_online_meeting or False,
            "online_meeting_url": online_meeting_url,
            "importance": importance,
            "sensitivity": sensitivity,
            "is_reminder_on": event.is_reminder_on or False,
            "reminder_minutes": event.reminder_minutes_before_start or 0,
            "is_recurring": is_recurring,
            "recurrence_pattern": recurrence_pattern,
            "has_attachments": event.has_attachments or False,
        }

    @staticmethod
    def process_description(
        description: str, mode: str = "full", max_length: Optional[int] = None
    ) -> str:
        """Delegate to description utility for processing descriptions."""
        return process_description_util(
            description=description, mode=mode, max_length=max_length
        )


events_service = EventsService()
