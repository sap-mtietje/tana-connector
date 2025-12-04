"""Calendar service - MS Graph style responses via Kiota SDK"""

from typing import Optional, List, Dict, Any
from msgraph.generated.users.item.calendar_view.calendar_view_request_builder import (
    CalendarViewRequestBuilder,
)
from kiota_abstractions.base_request_configuration import RequestConfiguration

from app.services.graph_service import graph_service
from app.utils.timezone_utils import get_system_timezone_name


class CalendarService:
    """Calendar operations using Kiota SDK, returning MS Graph format"""

    async def get_calendar_view(
        self,
        start_date_time: str,
        end_date_time: str,
        select: Optional[List[str]] = None,
        filter: Optional[str] = None,
        orderby: Optional[List[str]] = None,
        top: Optional[int] = None,
        skip: Optional[int] = None,
        expand: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get calendar view (events in time range) via Kiota SDK.

        Returns events in MS Graph JSON format (not normalized).
        """
        client = await graph_service.get_client()

        query_params = (
            CalendarViewRequestBuilder.CalendarViewRequestBuilderGetQueryParameters(
                start_date_time=start_date_time,
                end_date_time=end_date_time,
                select=select,
                filter=filter,
                orderby=orderby,
                top=top,
                skip=skip,
                expand=expand,
            )
        )

        # Set timezone preference
        timezone_name = get_system_timezone_name()
        request_config = RequestConfiguration(query_parameters=query_params)
        request_config.headers.add("Prefer", f'outlook.timezone="{timezone_name}"')

        result = await client.me.calendar_view.get(request_configuration=request_config)

        if not result or not result.value:
            return []

        # Convert Kiota objects to dicts (MS Graph format)
        return [self._event_to_dict(event) for event in result.value]

    def _event_to_dict(self, event) -> Dict[str, Any]:
        """
        Convert Kiota Event object to dict matching MS Graph JSON format.

        Preserves original field names (subject, not title; showAs, not availability).
        """
        result = {
            "id": event.id,
            "subject": event.subject,
            "bodyPreview": event.body_preview,
        }

        # Body
        if event.body:
            result["body"] = {
                "contentType": str(event.body.content_type)
                if event.body.content_type
                else None,
                "content": event.body.content,
            }

        # Start/End times
        if event.start:
            result["start"] = {
                "dateTime": event.start.date_time,
                "timeZone": event.start.time_zone,
            }
        if event.end:
            result["end"] = {
                "dateTime": event.end.date_time,
                "timeZone": event.end.time_zone,
            }

        # Location
        if event.location:
            result["location"] = {
                "displayName": event.location.display_name,
                "locationType": str(event.location.location_type)
                if event.location.location_type
                else None,
            }

        # Locations (multiple)
        if event.locations:
            result["locations"] = [
                {"displayName": loc.display_name} for loc in event.locations
            ]

        # Attendees
        if event.attendees:
            result["attendees"] = [
                {
                    "type": str(att.type) if att.type else None,
                    "status": {
                        "response": str(att.status.response)
                        if att.status and att.status.response
                        else None,
                        "time": att.status.time.isoformat()
                        if att.status and att.status.time
                        else None,
                    }
                    if att.status
                    else None,
                    "emailAddress": {
                        "name": att.email_address.name if att.email_address else None,
                        "address": att.email_address.address
                        if att.email_address
                        else None,
                    }
                    if att.email_address
                    else None,
                }
                for att in event.attendees
            ]

        # Organizer
        if event.organizer and event.organizer.email_address:
            result["organizer"] = {
                "emailAddress": {
                    "name": event.organizer.email_address.name,
                    "address": event.organizer.email_address.address,
                }
            }

        # Response status
        if event.response_status:
            result["responseStatus"] = {
                "response": str(event.response_status.response)
                if event.response_status.response
                else None,
                "time": event.response_status.time.isoformat()
                if event.response_status.time
                else None,
            }

        # Categories
        result["categories"] = list(event.categories) if event.categories else []

        # Enum fields
        result["importance"] = str(event.importance) if event.importance else None
        result["sensitivity"] = str(event.sensitivity) if event.sensitivity else None
        result["showAs"] = str(event.show_as) if event.show_as else None
        result["type"] = str(event.type) if event.type else None

        # Boolean fields
        result["isAllDay"] = event.is_all_day
        result["isCancelled"] = event.is_cancelled
        result["isOnlineMeeting"] = event.is_online_meeting
        result["hasAttachments"] = event.has_attachments
        result["isReminderOn"] = event.is_reminder_on
        result["reminderMinutesBeforeStart"] = event.reminder_minutes_before_start

        # Online meeting
        if event.is_online_meeting and event.online_meeting:
            result["onlineMeeting"] = {
                "joinUrl": event.online_meeting.join_url,
            }
        result["onlineMeetingUrl"] = event.online_meeting_url

        # Web link
        result["webLink"] = event.web_link

        # Recurrence
        if event.recurrence:
            result["recurrence"] = {
                "pattern": {
                    "type": str(event.recurrence.pattern.type)
                    if event.recurrence.pattern and event.recurrence.pattern.type
                    else None,
                    "interval": event.recurrence.pattern.interval
                    if event.recurrence.pattern
                    else None,
                }
                if event.recurrence.pattern
                else None,
            }

        return result

    def format_as_tana(self, events: List[Dict[str, Any]], tag: str = "meeting") -> str:
        """
        Format MS Graph events as Tana Paste.

        Simple default format - for complex formatting, use POST with template.
        """
        if not events:
            return "%%tana%%\n- No events found"

        lines = ["%%tana%%"]
        for event in events:
            subject = event.get("subject", "Untitled")
            lines.append(f"- {subject} #{tag}")

            # Start/End
            start = event.get("start", {})
            end = event.get("end", {})
            if start.get("dateTime") and end.get("dateTime"):
                lines.append(
                    f"  - Date:: [[date:{start['dateTime']}/{end['dateTime']}]]"
                )

            # Location
            location = event.get("location", {})
            if location.get("displayName"):
                lines.append(f"  - Location:: {location['displayName']}")

            # Attendees
            attendees = event.get("attendees", [])
            if attendees:
                lines.append("  - Attendees::")
                for att in attendees:
                    email = att.get("emailAddress", {})
                    name = email.get("name") or email.get("address", "")
                    if name:
                        lines.append(f"    - {name}")

            # Categories
            categories = event.get("categories", [])
            if categories:
                lines.append(f"  - Categories:: {', '.join(categories)}")

        return "\n".join(lines)


calendar_service = CalendarService()
