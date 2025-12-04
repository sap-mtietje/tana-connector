"""Calendar endpoints - MS Graph style API"""

from typing import Optional
from fastapi import APIRouter, Query, Body, HTTPException
from fastapi.responses import PlainTextResponse

from app.models.filters import Importance, Sensitivity, ShowAs, ResponseStatus
from app.models.query_params import resolve_calendar_view_params
from app.services.calendar_service import calendar_service
from app.services.template_service import template_service

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


# Shared docstrings for reuse
_DATE_PARAMS_DOC = """
## Required Parameters
- `startDateTime` — Start of time range (ISO 8601 format)
- `endDateTime` — End of time range (ISO 8601 format)

**OR use our convenience extension:**
- `_dateKeyword` — Relative date: `today`, `tomorrow`, `this-week`, `next-week`, `this-month`
"""

_QUERY_PARAMS_DOC = """
## Query Parameters
- `select` — Comma-separated fields: `subject,start,end,location,attendees`
- `orderby` — Sort field: `start/dateTime`, `subject`
- `top` — Maximum number of events (1-100)
- `skip` — Number of events to skip (pagination)
"""

_FILTER_PARAMS_DOC = """
## Filter Parameters (Friendly)
Use these instead of OData syntax:
- `_importance` — Filter by importance: `low`, `normal`, `high`
- `_sensitivity` — Filter by sensitivity: `normal`, `personal`, `private`, `confidential`
- `_showAs` — Filter by availability: `free`, `tentative`, `busy`, `oof`, `workingElsewhere`
- `_responseStatus` — Filter by response: `accepted`, `declined`, `tentativelyAccepted`, etc.
- `_isAllDay` — Filter all-day events: `true` or `false`
- `_isOnlineMeeting` — Filter online meetings: `true` or `false`
- `_isCancelled` — Filter cancelled events: `true` or `false`
- `_hasAttachments` — Filter events with attachments: `true` or `false`
- `_categories` — Filter by category names (comma-separated)

## Advanced Filter (OData)
- `filter` — Raw OData filter expression for complex queries
"""


@router.get(
    "/CalendarView",
    summary="Get calendar view",
    description=f"""
Retrieve calendar events within a time range. Mirrors Microsoft Graph API `/me/calendarView`.
{_DATE_PARAMS_DOC}
{_QUERY_PARAMS_DOC}
{_FILTER_PARAMS_DOC}

## Extension Parameters
- `_format` — Response format: `json` (default) or `tana`

## Examples
```
# Friendly filters
GET /me/CalendarView?_dateKeyword=this-week&_importance=high&_isOnlineMeeting=true

# Filter by category
GET /me/CalendarView?_dateKeyword=today&_categories=Work,Important

# Combine friendly + OData
GET /me/CalendarView?_dateKeyword=this-week&_importance=high&filter=contains(subject,'standup')

# Tana output with filters
GET /me/CalendarView?_dateKeyword=tomorrow&_showAs=busy&_format=tana
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
        default=None, ge=1, le=100, description="Maximum number of events to return"
    ),
    skip: Optional[int] = Query(
        default=None, ge=0, description="Number of events to skip (pagination)"
    ),
    # Extension params
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
    # Friendly filter params
    _importance: Optional[Importance] = Query(
        default=None, description="Filter by importance level"
    ),
    _sensitivity: Optional[Sensitivity] = Query(
        default=None, description="Filter by sensitivity level"
    ),
    _showAs: Optional[ShowAs] = Query(
        default=None, description="Filter by availability/free-busy status"
    ),
    _responseStatus: Optional[ResponseStatus] = Query(
        default=None, description="Filter by your response status"
    ),
    _isAllDay: Optional[bool] = Query(
        default=None, description="Filter all-day events (true) or timed events (false)"
    ),
    _isOnlineMeeting: Optional[bool] = Query(
        default=None, description="Filter online meetings (true) or in-person (false)"
    ),
    _isCancelled: Optional[bool] = Query(
        default=None, description="Filter cancelled events"
    ),
    _hasAttachments: Optional[bool] = Query(
        default=None, description="Filter events with attachments"
    ),
    _categories: Optional[str] = Query(
        default=None,
        description="Filter by category names (comma-separated)",
        examples=["Work", "Work,Personal", "Important"],
    ),
):
    # Resolve all params using shared logic
    params = resolve_calendar_view_params(
        startDateTime=startDateTime,
        endDateTime=endDateTime,
        select=select,
        filter=filter,
        orderby=orderby,
        top=top,
        skip=skip,
        _dateKeyword=_dateKeyword,
        _importance=_importance,
        _sensitivity=_sensitivity,
        _showAs=_showAs,
        _responseStatus=_responseStatus,
        _isAllDay=_isAllDay,
        _isOnlineMeeting=_isOnlineMeeting,
        _isCancelled=_isCancelled,
        _hasAttachments=_hasAttachments,
        _categories=_categories,
    )

    try:
        events = await calendar_service.get_calendar_view(
            start_date_time=params.start_date_time,
            end_date_time=params.end_date_time,
            select=params.select,
            filter=params.filter,
            orderby=params.orderby,
            top=params.top,
            skip=params.skip,
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
    "/CalendarView/render",
    summary="Get calendar view with template",
    description=f"""
Retrieve calendar events and render with a custom Jinja2 template.

Same parameters as GET, plus a Jinja2 template in the request body.
{_DATE_PARAMS_DOC}
{_QUERY_PARAMS_DOC}
{_FILTER_PARAMS_DOC}

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
{{% for event in events %}}
- {{{{event.subject}}}} #meeting
  - Start:: {{{{event.start.dateTime}}}}
  - Location:: {{{{event.location.displayName if event.location else ''}}}}
  {{% if event.attendees %}}
  - Attendees::
    {{% for att in event.attendees %}}
    - {{{{att.emailAddress.name}}}}
    {{% endfor %}}
  {{% endif %}}
{{% endfor %}}
```
""",
    response_class=PlainTextResponse,
)
async def post_calendar_view_with_template(
    template_body: str = Body(
        ..., media_type="text/plain", description="Jinja2 template string"
    ),
    # Same params as GET (without _format)
    startDateTime: Optional[str] = Query(default=None),
    endDateTime: Optional[str] = Query(default=None),
    select: Optional[str] = Query(default=None),
    filter: Optional[str] = Query(default=None, alias="$filter"),
    orderby: Optional[str] = Query(default=None),
    top: Optional[int] = Query(default=None, ge=1, le=100),
    skip: Optional[int] = Query(default=None, ge=0),
    _dateKeyword: Optional[str] = Query(default=None),
    # Friendly filter params
    _importance: Optional[Importance] = Query(default=None),
    _sensitivity: Optional[Sensitivity] = Query(default=None),
    _showAs: Optional[ShowAs] = Query(default=None),
    _responseStatus: Optional[ResponseStatus] = Query(default=None),
    _isAllDay: Optional[bool] = Query(default=None),
    _isOnlineMeeting: Optional[bool] = Query(default=None),
    _isCancelled: Optional[bool] = Query(default=None),
    _hasAttachments: Optional[bool] = Query(default=None),
    _categories: Optional[str] = Query(default=None),
):
    if not template_body or not template_body.strip():
        raise HTTPException(status_code=400, detail="Template body is required")

    # Resolve all params using shared logic
    params = resolve_calendar_view_params(
        startDateTime=startDateTime,
        endDateTime=endDateTime,
        select=select,
        filter=filter,
        orderby=orderby,
        top=top,
        skip=skip,
        _dateKeyword=_dateKeyword,
        _importance=_importance,
        _sensitivity=_sensitivity,
        _showAs=_showAs,
        _responseStatus=_responseStatus,
        _isAllDay=_isAllDay,
        _isOnlineMeeting=_isOnlineMeeting,
        _isCancelled=_isCancelled,
        _hasAttachments=_hasAttachments,
        _categories=_categories,
    )

    try:
        events = await calendar_service.get_calendar_view(
            start_date_time=params.start_date_time,
            end_date_time=params.end_date_time,
            select=params.select,
            filter=params.filter,
            orderby=params.orderby,
            top=params.top,
            skip=params.skip,
        )

        rendered = template_service.render_template(
            template_string=template_body,
            events=events,
            start_date=params.start_date_time,
            end_date=params.end_date_time,
        )

        return PlainTextResponse(content=rendered)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to render template: {str(e)}"
        )
