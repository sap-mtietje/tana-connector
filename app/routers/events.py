"""Calendar events endpoints - EventLink compatible"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from app.services.events_service import events_service
from app.utils.tana_formatter import TanaFormatter

router = APIRouter()


@router.get("/events.{format}")
async def get_events(
    format: str,
    filterField: Optional[str] = None,
    filterTitle: Optional[str] = None,
    filterAttendee: Optional[str] = None,
    filterStatus: Optional[str] = None,
    filterCalendar: Optional[str] = None,
    tag: str = "meeting",
    date: Optional[str] = None,
    offset: int = 1,
    truncate: bool = False,
    filterAvailability: Optional[str] = None,
    selectCalendar: Optional[str] = None,
    filterAllDay: Optional[bool] = None,
    timingField: str = "Timing",
):
    """Get calendar events in JSON or Tana Paste format (EventLink compatible)"""
    
    if format not in ["json", "tana"]:
        raise HTTPException(status_code=400, detail="Format must be 'json' or 'tana'")
    
    if date:
        try:
            start_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    end_date = start_date + timedelta(days=offset)
    
    try:
        events = await events_service.get_events(
            start_datetime=start_date,
            end_datetime=end_date,
            filter_title=filterTitle.split(",") if filterTitle else None,
            filter_attendee=filterAttendee.split(",") if filterAttendee else None,
            filter_status=filterStatus.split(",") if filterStatus else None,
            filter_calendar=filterCalendar or selectCalendar,
            filter_availability=filterAvailability.split(",") if filterAvailability else None,
            filter_all_day=filterAllDay,
        )
        
        if truncate:
            for event in events:
                if event.get("description"):
                    event["description"] = events_service.truncate_description(event["description"])
        
        if format == "json":
            if filterField:
                fields = filterField.split(",")
                events = [{k: v for k, v in event.items() if k in fields} for event in events]
            
            return {"success": True, "count": len(events), "events": events}
        
        tana_content = TanaFormatter.format_events(
            events,
            tag=tag,
            timing_field=timingField,
            filter_fields=filterField.split(",") if filterField else None
        )
        return PlainTextResponse(content=tana_content)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch events: {str(e)}")

