"""Calendar endpoints - MS Graph style API"""

from typing import Optional
from fastapi import APIRouter, Query, Body, HTTPException
from fastapi.responses import PlainTextResponse

from app.services.calendar_service import calendar_service
from app.services.template_service import template_service
from app.utils.date_utils import parse_date_keyword_to_range

router = APIRouter(tags=["Calendar"])

# MS Graph field names available for $select
CALENDAR_VIEW_FIELDS = [
    "id",
    "subject",
    "bodyPreview",
    "body",
    "start",
    "end",
    "location",
    "locations",
    "attendees",
    "organizer",
    "categories",
    "importance",
    "sensitivity",
    "showAs",
    "isAllDay",
    "isCancelled",
    "isOnlineMeeting",
    "onlineMeeting",
    "onlineMeetingUrl",
    "webLink",
    "responseStatus",
    "recurrence",
    "type",
    "hasAttachments",
    "isReminderOn",
    "reminderMinutesBeforeStart",
]


@router.get(
    "/calendarView",
    summary="Get calendar view",
    description="""
Retrieve calendar events within a time range. Mirrors Microsoft Graph API `/me/calendarView`.

## Required Parameters
- `startDateTime` — Start of time range (ISO 8601 format)
- `endDateTime` — End of time range (ISO 8601 format)

**OR use our convenience extension:**
- `_dateKeyword` — Relative date: `today`, `tomorrow`, `this-week`, `next-week`, `this-month`

## OData Query Parameters
- `select` — Comma-separated fields: `subject,start,end,location,attendees`
- `filter` — OData filter expression: `importance eq 'high'`
- `orderby` — Sort field: `start/dateTime`, `subject`
- `top` — Maximum number of events (1-100)
- `skip` — Number of events to skip (pagination)

## Extension Parameters
- `_format` — Response format: `json` (default) or `tana`
- `_dateKeyword` — Convenience date range: `today`, `tomorrow`, `this-week`, etc.

## Examples
```
# Standard MS Graph style
GET /me/calendarView?startDateTime=2024-12-01T00:00:00&endDateTime=2024-12-07T23:59:59&select=subject,start,location

# With date keyword extension
GET /me/calendarView?_dateKeyword=this-week&select=subject,start,location

# Tana output
GET /me/calendarView?_dateKeyword=tomorrow&_format=tana
```
""",
)
async def get_calendar_view(
    # MS Graph standard params
    startDateTime: Optional[str] = Query(
        default=None,
        description="Start of time range (ISO 8601). Required unless _dateKeyword is provided.",
        examples=["2024-12-01T00:00:00", "2024-12-01T00:00:00Z"],
    ),
    endDateTime: Optional[str] = Query(
        default=None,
        description="End of time range (ISO 8601). Required unless _dateKeyword is provided.",
        examples=["2024-12-07T23:59:59", "2024-12-07T23:59:59Z"],
    ),
    select: Optional[str] = Query(
        default=None,
        description=f"Comma-separated fields to return. Available: {', '.join(CALENDAR_VIEW_FIELDS[:10])}...",
        examples=["subject,start,end,location", "subject,start,attendees,organizer"],
    ),
    filter: Optional[str] = Query(
        default=None,
        alias="$filter",
        description="OData filter expression",
        examples=["importance eq 'high'", "sensitivity eq 'normal'"],
    ),
    orderby: Optional[str] = Query(
        default=None,
        description="Sort field(s), comma-separated",
        examples=["start/dateTime", "start/dateTime desc"],
    ),
    top: Optional[int] = Query(
        default=None,
        ge=1,
        le=100,
        description="Maximum number of events to return",
        examples=[10, 25, 50],
    ),
    skip: Optional[int] = Query(
        default=None,
        ge=0,
        description="Number of events to skip (pagination)",
        examples=[0, 10, 20],
    ),
    # Our extensions (prefixed with _)
    _dateKeyword: Optional[str] = Query(
        default=None,
        description="Convenience date range. Overrides startDateTime/endDateTime if provided.",
        examples=["today", "tomorrow", "this-week", "next-week", "this-month"],
    ),
    _format: str = Query(
        default="json",
        description="Response format",
        examples=["json", "tana"],
        pattern="^(json|tana)$",
    ),
):
    # Resolve date range
    if _dateKeyword:
        try:
            start_dt, end_dt = parse_date_keyword_to_range(_dateKeyword)
            startDateTime = start_dt.isoformat()
            endDateTime = end_dt.isoformat()
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    if not startDateTime or not endDateTime:
        raise HTTPException(
            status_code=400,
            detail="Either startDateTime/endDateTime or _dateKeyword is required",
        )

    # Parse list params
    select_list = [s.strip() for s in select.split(",")] if select else None
    orderby_list = [o.strip() for o in orderby.split(",")] if orderby else None

    try:
        events = await calendar_service.get_calendar_view(
            start_date_time=startDateTime,
            end_date_time=endDateTime,
            select=select_list,
            filter=filter,
            orderby=orderby_list,
            top=top,
            skip=skip,
        )

        if _format == "tana":
            tana_output = calendar_service.format_as_tana(events)
            return PlainTextResponse(content=tana_output)

        return {
            "value": events,
            "@odata.count": len(events),
            "@odata.context": "$metadata#users('me')/calendarView",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch calendar view: {str(e)}"
        )


@router.post(
    "/calendarView",
    summary="Get calendar view with template",
    description="""
Retrieve calendar events and render with a custom Jinja2 template.

Same parameters as GET, plus a Jinja2 template in the request body.

## Template Context
- `events` — List of event objects (MS Graph format)
- `count` — Number of events
- `start_date` — Start date string
- `end_date` — End date string

## Event Fields (MS Graph format)
- `subject`, `bodyPreview`, `body.content`
- `start.dateTime`, `end.dateTime`
- `location.displayName`, `attendees`, `organizer`
- `categories`, `importance`, `sensitivity`, `showAs`
- `isAllDay`, `isCancelled`, `isOnlineMeeting`

## Example Template
```jinja2
%%tana%%
{% for event in events %}
- {{event.subject}} #meeting
  - Start:: {{event.start.dateTime}}
  - Location:: {{event.location.displayName if event.location else ''}}
  {% if event.attendees %}
  - Attendees::
    {% for att in event.attendees %}
    - {{att.emailAddress.name}}
    {% endfor %}
  {% endif %}
{% endfor %}
```
""",
    response_class=PlainTextResponse,
)
async def post_calendar_view_with_template(
    template_body: str = Body(
        ...,
        media_type="text/plain",
        description="Jinja2 template string",
    ),
    # Same params as GET
    startDateTime: Optional[str] = Query(default=None),
    endDateTime: Optional[str] = Query(default=None),
    select: Optional[str] = Query(default=None),
    filter: Optional[str] = Query(default=None, alias="$filter"),
    orderby: Optional[str] = Query(default=None),
    top: Optional[int] = Query(default=None, ge=1, le=100),
    skip: Optional[int] = Query(default=None, ge=0),
    _dateKeyword: Optional[str] = Query(default=None),
):
    if not template_body or not template_body.strip():
        raise HTTPException(
            status_code=400,
            detail="Template body is required",
        )

    # Resolve date range
    if _dateKeyword:
        try:
            start_dt, end_dt = parse_date_keyword_to_range(_dateKeyword)
            startDateTime = start_dt.isoformat()
            endDateTime = end_dt.isoformat()
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    if not startDateTime or not endDateTime:
        raise HTTPException(
            status_code=400,
            detail="Either startDateTime/endDateTime or _dateKeyword is required",
        )

    # Parse list params
    select_list = [s.strip() for s in select.split(",")] if select else None
    orderby_list = [o.strip() for o in orderby.split(",")] if orderby else None

    try:
        events = await calendar_service.get_calendar_view(
            start_date_time=startDateTime,
            end_date_time=endDateTime,
            select=select_list,
            filter=filter,
            orderby=orderby_list,
            top=top,
            skip=skip,
        )

        # Render template
        rendered = template_service.render_template(
            template_string=template_body,
            events=events,
            start_date=startDateTime,
            end_date=endDateTime,
        )

        return PlainTextResponse(content=rendered)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to render template: {str(e)}"
        )
