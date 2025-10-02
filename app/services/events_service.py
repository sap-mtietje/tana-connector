"""Events service - Fetches calendar events from Microsoft Graph API"""

import re
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from msgraph.generated.users.item.calendar_view.calendar_view_request_builder import CalendarViewRequestBuilder
from kiota_abstractions.base_request_configuration import RequestConfiguration

from app.services.graph_service import graph_service

TIMEZONE_MAP = {
    'CEST': 'Central European Standard Time',
    'CET': 'Central European Standard Time',
    'PST': 'Pacific Standard Time',
    'PDT': 'Pacific Standard Time',
    'EST': 'Eastern Standard Time',
    'EDT': 'Eastern Standard Time',
}


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
        filter_all_day: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """Get calendar events from Microsoft Graph API with local timezone"""
        client = await graph_service.get_client()
        
        start_str = start_datetime.strftime("%Y-%m-%dT%H:%M:%S")
        end_str = end_datetime.strftime("%Y-%m-%dT%H:%M:%S")
        
        query_params = CalendarViewRequestBuilder.CalendarViewRequestBuilderGetQueryParameters(
            start_date_time=start_str,
            end_date_time=end_str,
        )
        
        tz_name = time.tzname[time.daylight]
        outlook_timezone = TIMEZONE_MAP.get(tz_name, 'Central European Standard Time')
        
        request_config = RequestConfiguration(query_parameters=query_params)
        request_config.headers.add('Prefer', f'outlook.timezone="{outlook_timezone}"')
        
        result = await client.me.calendar_view.get(request_configuration=request_config)
        
        if not result or not result.value:
            return []
        
        events = []
        for event in result.value:
            event_data = self._parse_event(event)
            
            if filter_title and not any(t.lower() in event_data["title"].lower() for t in filter_title):
                continue
            
            if filter_attendee:
                attendees_lower = [a.lower() for a in event_data.get("attendees", [])]
                if not any(att.lower() in attendee for att in filter_attendee for attendee in attendees_lower):
                    continue
            
            if filter_status and event_data.get("status") not in filter_status:
                continue
            
            if filter_availability and event_data.get("availability") not in filter_availability:
                continue
            
            if filter_all_day is not None:
                is_all_day = event_data.get("is_all_day", False)
                if filter_all_day != is_all_day:
                    continue
            
            events.append(event_data)
        
        return events
    
    def _parse_event(self, event) -> Dict[str, Any]:
        """Parse Graph API event object to our format"""
        start_dt = event.start.date_time if event.start else None
        end_dt = event.end.date_time if event.end else None
        
        attendees = []
        if event.attendees:
            for attendee in event.attendees:
                if attendee.email_address:
                    name = attendee.email_address.name or attendee.email_address.address
                    if name:
                        attendees.append(name)
        
        location = event.location.display_name if event.location else ""
        
        description = ""
        if event.body and event.body.content:
            description = re.sub(r'<[^>]+>', '', event.body.content).strip()
        
        status = "None"
        if event.response_status and event.response_status.response:
            response_map = {
                "accepted": "Confirmed",
                "tentativelyaccepted": "Tentative",
                "declined": "Canceled"
            }
            status = response_map.get(event.response_status.response.lower(), "None")
        
        availability = "Unknown"
        if event.show_as:
            availability_map = {
                "free": "Free",
                "busy": "Busy",
                "tentative": "Tentative",
                "oof": "Unavailable"
            }
            availability = availability_map.get(event.show_as.lower(), "Unknown")
        
        organizer = ""
        if event.organizer and event.organizer.email_address:
            organizer = event.organizer.email_address.address
        
        return {
            "id": event.id or "",
            "title": event.subject or "Untitled Event",
            "start": start_dt,
            "end": end_dt,
            "location": location,
            "status": status,
            "attendees": attendees,
            "description": description,
            "calendar": "Calendar",
            "availability": availability,
            "is_all_day": event.is_all_day or False,
            "organizer": organizer,
        }
    
    @staticmethod
    def truncate_description(description: str) -> str:
        """Truncate description to remove video call content"""
        patterns = [
            r'Join (Zoom|Teams|Meet) Meeting.*',
            r'Meeting ID:.*',
            r'Passcode:.*',
            r'https?://[^\s]+zoom\.us[^\s]*',
            r'https?://teams\.microsoft\.com[^\s]*',
            r'https?://meet\.google\.com[^\s]*',
        ]
        
        result = description
        for pattern in patterns:
            result = re.sub(pattern, '', result, flags=re.IGNORECASE | re.DOTALL)
        
        return result.strip()


events_service = EventsService()

