"""Calendar events endpoints"""

from datetime import timedelta
from enum import Enum
from typing import Optional
from fastapi import APIRouter, HTTPException, Path, Query
from fastapi.responses import PlainTextResponse
from app.services.events_service import events_service
from app.utils.tana_formatter import TanaFormatter
from app.utils.date_utils import parse_relative_date, parse_field_tags, get_today

router = APIRouter(tags=["Calendar Events"])


class DescriptionMode(str, Enum):
    full = "full"
    clean = "clean"
    none = "none"


# Available fields for the fields parameter
AVAILABLE_FIELDS = [
    "id", "title", "date", "start", "end", "location", "status", 
    "attendees", "description", "calendar", "availability", "is_all_day",
    "organizer", "categories", "web_link", "is_cancelled", "is_online_meeting",
    "online_meeting_url", "importance", "sensitivity", "is_reminder_on",
    "reminder_minutes", "is_recurring", "recurrence_pattern", "has_attachments"
]

# Available date keywords
DATE_KEYWORDS = [
    "today", "tomorrow", "yesterday",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "this-week", "next-week", "this-month"
]


@router.get(
    "/events.{format}",
    summary="Get calendar events",
    description="""
Retrieve Outlook calendar events in JSON or Tana Paste format with filtering and formatting options.

## Available Fields
Use the `fields` parameter to select specific fields:
- **Time fields**: `date` (combined range), `start`, `end`
- **Basic info**: `title`, `location`, `status`, `calendar`
- **People**: `organizer`, `attendees`
- **Details**: `description`, `categories`, `importance`, `sensitivity`
- **Meeting info**: `is_online_meeting`, `online_meeting_url`, `web_link`
- **Flags**: `is_all_day`, `is_cancelled`, `is_recurring`, `has_attachments`
- **Other**: `availability`, `recurrence_pattern`, `reminder_minutes`

## Date Keywords
Use relative keywords instead of dates:
- **Days**: `today`, `tomorrow`, `yesterday`
- **Weekdays**: `monday`, `tuesday`, `wednesday`, `thursday`, `friday`, `saturday`, `sunday`
- **Periods**: `this-week`, `next-week`, `this-month`
- **Or use**: `YYYY-MM-DD` format (e.g., `2025-10-15`)
""",
)
async def get_events(
    format: str = Path(
        ..., 
        pattern="^(json|tana)$",
        description="Response format",
        examples=["json", "tana"]
    ),
    date: Optional[str] = Query(
        None, 
        description=f"Start date. Keywords: {', '.join(DATE_KEYWORDS)} or YYYY-MM-DD format",
        examples=["today", "tomorrow", "next-week", "2025-10-15"]
    ),
    offset: int = Query(
        1, 
        description="Number of days to fetch", 
        ge=1, 
        le=365,
        examples=[1, 7, 30]
    ),
    filterTitle: Optional[str] = Query(
        None, 
        description="Filter by title (case-insensitive substring match)",
        examples=["standup", "review"]
    ),
    filterAttendee: Optional[str] = Query(
        None, 
        description="Filter by attendee (comma-separated, case-insensitive)",
        examples=["john@company.com", "john,jane"]
    ),
    filterStatus: Optional[str] = Query(
        None, 
        description="Filter by response status (comma-separated). Options: Accepted, Tentative, Declined, No Response",
        examples=["Accepted", "Accepted,Tentative"]
    ),
    filterAvailability: Optional[str] = Query(
        None, 
        description="Filter by availability (comma-separated). Options: Free, Busy, Tentative, Out of Office, Working Elsewhere",
        examples=["Busy", "Busy,Tentative"]
    ),
    filterCategories: Optional[str] = Query(
        None, 
        description="Filter by categories (comma-separated, case-insensitive)",
        examples=["Work", "Personal,Work"]
    ),
    includeAllDay: Optional[bool] = Query(
        None, 
        description="Filter all-day events. true=only all-day, false=exclude all-day, null=include both",
        examples=[True, False, None]
    ),
    calendar: Optional[str] = Query(
        None, 
        description="Filter by calendar name",
        examples=["Calendar", "Work Calendar"]
    ),
    tag: str = Query(
        "meeting", 
        description="Base Tana tag for all events",
        examples=["meeting", "work", "personal"]
    ),
    includeCategoryTags: bool = Query(
        False, 
        description="Auto-convert categories to Tana tags instead of using base tag",
        examples=[True, False]
    ),
    fieldTags: Optional[str] = Query(
        None, 
        description="Tag specific fields in Tana format (field:tag,field:tag). Supported: attendees, organizer, categories, location",
        examples=["attendees:co-worker,organizer:manager", "location:office"]
    ),
    fields: Optional[str] = Query(
        None, 
        description=f"Include only these fields (comma-separated). Available: {', '.join(sorted(AVAILABLE_FIELDS))}",
        examples=["date,location,attendees", "start,end,title,status"]
    ),
    showEmpty: bool = Query(
        True, 
        description="Show fields even when empty",
        examples=[True, False]
    ),
    descriptionMode: DescriptionMode = Query(
        DescriptionMode.full, 
        description="Description processing: full=complete, clean=remove meeting links/HTML, none=omit",
        examples=["full", "clean", "none"]
    ),
    descriptionLength: Optional[int] = Query(
        None, 
        description="Max description length (1-5000 characters)",
        ge=1, 
        le=5000,
        examples=[100, 500, 1000]
    ),
):
    start_date = parse_relative_date(date) if date else get_today()
    end_date = start_date + timedelta(days=offset)
    
    try:
        events = await events_service.get_events(
            start_datetime=start_date,
            end_datetime=end_date,
            filter_title=[filterTitle] if filterTitle else None,
            filter_attendee=filterAttendee.split(",") if filterAttendee else None,
            filter_status=filterStatus.split(",") if filterStatus else None,
            filter_calendar=calendar,
            filter_availability=filterAvailability.split(",") if filterAvailability else None,
            filter_categories=filterCategories.split(",") if filterCategories else None,
            filter_all_day=includeAllDay,
        )
        
        for event in events:
            if event.get("description"):
                event["description"] = events_service.process_description(
                    event["description"],
                    mode=descriptionMode.value,
                    max_length=descriptionLength
                )
        
        if format == "json":
            if fields:
                field_list = [f.strip() for f in fields.split(",")]
                events = [{k: v for k, v in event.items() if k in field_list} for event in events]
            
            return {
                "success": True,
                "count": len(events),
                "metadata": {
                    "startDate": start_date.strftime("%Y-%m-%d"),
                    "endDate": end_date.strftime("%Y-%m-%d"),
                    "filters": {
                        "calendar": calendar,
                        "title": filterTitle,
                        "attendee": filterAttendee,
                        "status": filterStatus,
                        "availability": filterAvailability,
                        "categories": filterCategories,
                        "allDay": includeAllDay,
                    }
                },
                "events": events
            }
        
        tana_content = TanaFormatter.format_events(
            events,
            tag=tag,
            filter_fields=fields.split(",") if fields else None,
            include_category_tags=includeCategoryTags,
            show_empty=showEmpty,
            field_tags=parse_field_tags(fieldTags)
        )
        return PlainTextResponse(content=tana_content)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch events: {str(e)}")
