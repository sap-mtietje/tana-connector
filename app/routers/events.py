"""Calendar events endpoints"""

from datetime import timedelta
from fastapi import APIRouter, HTTPException, Path, Body, Depends
from fastapi.responses import PlainTextResponse
from app.services.events_service import events_service
from app.services.template_service import template_service
from app.utils.tana_formatter import TanaFormatter
from app.utils.date_utils import parse_relative_date, parse_field_tags, get_today
from app.routers.dependencies.events_params import (
    EventsQueryParams,
    events_query_params,
)

router = APIRouter(tags=["Calendar Events"])


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
        examples=["json", "tana"],
    ),
    params: EventsQueryParams = Depends(events_query_params),
):
    try:
        start_date = parse_relative_date(params.date) if params.date else get_today()
        end_date = start_date + timedelta(days=params.offset)

        events = await events_service.get_events(
            start_datetime=start_date,
            end_datetime=end_date,
            filter_title=params.parsed_filter_title,
            filter_attendee=params.parsed_filter_attendee,
            filter_status=params.parsed_filter_status,
            filter_calendar=params.calendar,
            filter_availability=params.parsed_filter_availability,
            filter_categories=params.parsed_filter_categories,
            filter_all_day=params.includeAllDay,
        )

        for event in events:
            if event.get("description"):
                event["description"] = events_service.process_description(
                    event["description"],
                    mode=params.descriptionMode.value,
                    max_length=params.descriptionLength,
                )

        if format == "json":
            if params.fields:
                field_list = [f.strip() for f in params.fields.split(",")]
                normalized_fields = []
                for f in field_list:
                    if f.lower() == "identifier":
                        normalized_fields.append("id")
                    elif f.lower() != "id":
                        normalized_fields.append(f)

                events = [
                    {k: v for k, v in event.items() if k in normalized_fields}
                    for event in events
                ]

            return {
                "success": True,
                "count": len(events),
                "metadata": {
                    "startDate": start_date.strftime("%Y-%m-%d"),
                    "endDate": end_date.strftime("%Y-%m-%d"),
                    "filters": {
                        "calendar": params.calendar,
                        "title": params.filterTitle,
                        "attendee": params.filterAttendee,
                        "status": params.filterStatus,
                        "availability": params.filterAvailability,
                        "categories": params.filterCategories,
                        "allDay": params.includeAllDay,
                    },
                },
                "events": events,
            }

        tana_content = TanaFormatter.format_events(
            events,
            tag=params.tag,
            filter_fields=params.fields.split(",") if params.fields else None,
            include_category_tags=params.includeCategoryTags,
            show_empty=params.showEmpty,
            field_tags=parse_field_tags(params.fieldTags),
        )
        return PlainTextResponse(content=tana_content)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch events: {str(e)}")


@router.post(
    "/events",
    summary="Render events with custom template",
    description="""
Render calendar events using a custom Jinja2 template.

## Request Body
Send a plain text Jinja2 template as the request body with `Content-Type: text/plain`.

## Template Context
Your template has access to:
- `events`: List of event objects
- `count`: Number of events
- `start_date`: Start date string (YYYY-MM-DD)
- `end_date`: End date string (YYYY-MM-DD)

## Event Fields
Each event in the `events` list has these fields:
- `id`, `title`, `start`, `end`, `date`
- `location`, `status`, `attendees`, `organizer`
- `description`, `categories`, `calendar`
- `availability`, `is_all_day`, `is_cancelled`
- `is_online_meeting`, `online_meeting_url`, `web_link`
- `importance`, `sensitivity`, `is_reminder_on`, `reminder_minutes`
- `is_recurring`, `recurrence_pattern`, `has_attachments`

## Custom Filters
- `clean`: Clean description (remove HTML, meeting links)
- `truncate(n)`: Truncate text to n characters
- `date_format(fmt)`: Format datetime string

## Query Parameters
Use the same query parameters as GET /events.{format} for filtering:
- Date/time: `date`, `offset`
- Filters: `filterTitle`, `filterAttendee`, `filterStatus`, `filterAvailability`, `filterCategories`, `includeAllDay`, `calendar`
- Options: `descriptionMode`, `descriptionLength`

## Template Examples

Simple:
```
{{event.title}} at {{event.location}}
```

Tana with loops:
```
%%tana%%
{% for event in events %}
- {{event.title}} #meeting
  - Date:: [[date:{{event.start}}/{{event.end}}]]
  - Attendees::
    {% for attendee in event.attendees %}
    - [[{{attendee}} #co-worker]]
    {% endfor %}
{% endfor %}
```

With conditionals:
```
{% for event in events %}
{{event.title}}
{% if event.location %}
Location: {{event.location}}
{% endif %}
{% endfor %}
```
""",
    response_class=PlainTextResponse,
)
async def post_events_with_template(
    template_body: str = Body(
        ...,
        media_type="text/plain",
        description="Jinja2 template string",
        examples=[
            "{% for event in events %}{{event.title}} at {{event.location}}\n{% endfor %}",
            "%%tana%%\n{% for event in events %}\n- {{event.title}} #meeting\n  - Date:: [[date:{{event.start}}/{{event.end}}]]\n{% endfor %}",
        ],
    ),
    params: EventsQueryParams = Depends(events_query_params),
):
    """Render events with a custom Jinja2 template"""
    # Validate template body
    if not template_body or not template_body.strip():
        raise HTTPException(
            status_code=400, detail="Template body is required and cannot be empty"
        )

    try:
        template_string = template_body

        # Parse date parameters
        start_date = parse_relative_date(params.date) if params.date else get_today()
        end_date = start_date + timedelta(days=params.offset)

        # Fetch events using the same logic as GET endpoint
        events = await events_service.get_events(
            start_datetime=start_date,
            end_datetime=end_date,
            filter_title=params.parsed_filter_title,
            filter_attendee=params.parsed_filter_attendee,
            filter_status=params.parsed_filter_status,
            filter_calendar=params.calendar,
            filter_availability=params.parsed_filter_availability,
            filter_categories=params.parsed_filter_categories,
            filter_all_day=params.includeAllDay,
        )

        # Process descriptions
        for event in events:
            if event.get("description"):
                event["description"] = events_service.process_description(
                    event["description"],
                    mode=params.descriptionMode.value,
                    max_length=params.descriptionLength,
                )

        # Render template
        rendered_output = template_service.render_template(
            template_string=template_string,
            events=events,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
        )

        return PlainTextResponse(content=rendered_output)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to render template: {str(e)}"
        )
