"""Availability endpoints - Find meeting times via MS Graph API."""

from typing import List, Optional

from fastapi import APIRouter, Body, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from app.constants import DEFAULT_MEETING_DURATION
from app.dependencies import AvailabilityServiceDep, TemplateServiceDep
from app.exceptions import GraphAPIError
from app.models import (
    AttendeeModel,
    LocationConstraintModel,
    TimeConstraintModel,
)
from app.utils.date_utils import parse_date_keyword_to_range

router = APIRouter(tags=["Availability"])


# --- Pydantic Models for Request/Response ---


class FindMeetingTimesRequest(BaseModel):
    """Request body for findMeetingTimes endpoint"""

    attendees: List[AttendeeModel] = Field(
        ..., description="List of attendees to find meeting times for"
    )
    timeConstraint: Optional[TimeConstraintModel] = Field(
        default=None,
        description="Time constraint with activity domain and time slots",
    )
    locationConstraint: Optional[LocationConstraintModel] = Field(
        default=None, description="Location preferences and constraints"
    )
    meetingDuration: Optional[str] = Field(
        default=DEFAULT_MEETING_DURATION,
        description="Meeting duration in ISO 8601 format",
        examples=["PT30M", "PT1H", "PT1H30M", "PT2H"],
    )
    maxCandidates: Optional[int] = Field(
        default=None,
        ge=1,
        le=50,
        description="Maximum number of suggestions to return",
    )
    isOrganizerOptional: Optional[bool] = Field(
        default=False, description="Whether organizer attendance is optional"
    )
    returnSuggestionReasons: Optional[bool] = Field(
        default=True, description="Include reason for each suggestion"
    )
    minimumAttendeePercentage: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Minimum percentage of attendees that must be available",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "attendees": [
                        {
                            "emailAddress": {
                                "address": "colleague@company.com",
                                "name": "Colleague Name",
                            },
                            "type": "required",
                        }
                    ],
                    "timeConstraint": {
                        "activityDomain": "work",
                        "timeSlots": [
                            {
                                "start": {
                                    "dateTime": "2024-12-10T09:00:00",
                                    "timeZone": "Europe/Berlin",
                                },
                                "end": {
                                    "dateTime": "2024-12-10T17:00:00",
                                    "timeZone": "Europe/Berlin",
                                },
                            }
                        ],
                    },
                    "meetingDuration": "PT1H",
                    "returnSuggestionReasons": True,
                }
            ]
        }
    }


# --- Shared Documentation ---

_FIND_MEETING_TIMES_DOC = """
Find available meeting times based on attendee availability and constraints.

Mirrors Microsoft Graph API `POST /me/findMeetingTimes`.

## Request Body
- `attendees` — List of attendees with email addresses and type (required/optional)
- `timeConstraint` — Time slots to search within and activity domain (work/personal)
- `locationConstraint` — Location preferences (optional)
- `meetingDuration` — Duration in ISO 8601 format (default: PT1H = 1 hour)
- `maxCandidates` — Maximum suggestions to return (1-50)
- `isOrganizerOptional` — Whether organizer must attend
- `returnSuggestionReasons` — Include explanation for each suggestion
- `minimumAttendeePercentage` — Minimum % of attendees that must be available

## Extension Parameters (Query)
- `_dateKeyword` — Convenience: `today`, `tomorrow`, `this-week` (auto-generates timeConstraint)
- `_format` — Response format: `json` (default) or `tana`

## Response
Returns meeting time suggestions with:
- `meetingTimeSlot` — Suggested start/end times
- `confidence` — Likelihood all attendees can attend (0-100)
- `attendeeAvailability` — Each attendee's availability status
- `suggestionReason` — Why this time was suggested
"""


@router.post(
    "/findMeetingTimes",
    summary="Find available meeting times",
    description=f"""{_FIND_MEETING_TIMES_DOC}

## Example Request
```json
{{
  "attendees": [
    {{"emailAddress": {{"address": "colleague@company.com"}}, "type": "required"}}
  ],
  "timeConstraint": {{
    "activityDomain": "work",
    "timeSlots": [{{
      "start": {{"dateTime": "2024-12-10T09:00:00", "timeZone": "Europe/Berlin"}},
      "end": {{"dateTime": "2024-12-10T17:00:00", "timeZone": "Europe/Berlin"}}
    }}]
  }},
  "meetingDuration": "PT1H"
}}
```

## Example with _dateKeyword
```
POST /me/findMeetingTimes?_dateKeyword=this-week
{{
  "attendees": [{{"emailAddress": {{"address": "colleague@company.com"}}}}]
}}
```
""",
)
async def find_meeting_times(
    availability_service: AvailabilityServiceDep,
    request: FindMeetingTimesRequest,
    _dateKeyword: Optional[str] = Query(
        default=None,
        description="Convenience date range. Auto-generates timeConstraint if not provided.",
        examples=["today", "tomorrow", "this-week", "next-week"],
    ),
    _format: str = Query(
        default="json",
        description="Response format",
        examples=["json", "tana"],
        pattern="^(json|tana)$",
    ),
):
    # Build time constraint from _dateKeyword if not provided
    time_constraint = None
    if request.timeConstraint:
        time_constraint = request.timeConstraint.model_dump()
    elif _dateKeyword:
        start_dt, end_dt = parse_date_keyword_to_range(_dateKeyword)
        time_constraint = {
            "activityDomain": "work",
            "timeSlots": [
                {
                    "start": {"dateTime": start_dt.isoformat()},
                    "end": {"dateTime": end_dt.isoformat()},
                }
            ],
        }

    # Build location constraint
    location_constraint = None
    if request.locationConstraint:
        location_constraint = request.locationConstraint.model_dump()

    try:
        result = await availability_service.find_meeting_times(
            attendees=[att.model_dump() for att in request.attendees],
            time_constraint=time_constraint,
            location_constraint=location_constraint,
            meeting_duration=request.meetingDuration or DEFAULT_MEETING_DURATION,
            max_candidates=request.maxCandidates,
            is_organizer_optional=request.isOrganizerOptional or False,
            return_suggestion_reasons=request.returnSuggestionReasons
            if request.returnSuggestionReasons is not None
            else True,
            minimum_attendee_percentage=request.minimumAttendeePercentage,
        )

        if _format == "tana":
            tana_output = availability_service.format_as_tana(result)
            return PlainTextResponse(content=tana_output)

        return result

    except Exception as e:
        # Wrap unexpected errors in GraphAPIError for consistent handling
        raise GraphAPIError(
            message=f"Failed to find meeting times: {str(e)}",
            details={"error_type": type(e).__name__},
        )


@router.post(
    "/findMeetingTimes/render",
    summary="Find meeting times with template",
    description=f"""{_FIND_MEETING_TIMES_DOC}

## Template Rendering
Pass a Jinja2 template in the request body to customize output.

## Template Context
- `suggestions` — List of meeting time suggestions
- `count` — Number of suggestions
- `emptySuggestionsReason` — Reason if no suggestions found
- `attendees` — Original attendee list (for reference)
- `duration` — Meeting duration string

## Suggestion Fields
Each suggestion has:
- `meetingTimeSlot.start.dateTime`, `meetingTimeSlot.end.dateTime`
- `confidence` — 0-100
- `order` — Suggestion rank
- `organizerAvailability` — free, tentative, busy, etc.
- `attendeeAvailability` — List of attendee availability
- `suggestionReason` — Why suggested
- `locations` — Suggested locations

## Example Template
```jinja2
%%tana%%
- Meeting proposal #meeting-proposal
  - Duration:: {{{{duration}}}}
  {{% for sugg in suggestions %}}
  - Option {{{{sugg.order}}}}:: [[date:{{{{sugg.meetingTimeSlot.start.dateTime}}}}]]
    - Confidence:: {{{{sugg.confidence}}}}%
    - End:: {{{{sugg.meetingTimeSlot.end.dateTime}}}}
    {{% if sugg.suggestionReason %}}
    - Reason:: {{{{sugg.suggestionReason}}}}
    {{% endif %}}
  {{% endfor %}}
```
""",
    response_class=PlainTextResponse,
)
async def find_meeting_times_with_template(
    availability_service: AvailabilityServiceDep,
    template_service: TemplateServiceDep,
    template_body: str = Body(
        ..., media_type="text/plain", description="Jinja2 template string"
    ),
    attendees: str = Query(
        ...,
        description="Comma-separated email addresses",
        examples=["user1@example.com,user2@example.com"],
    ),
    meetingDuration: str = Query(
        default=DEFAULT_MEETING_DURATION,
        description="Meeting duration in ISO 8601 format",
        examples=["PT30M", "PT1H"],
    ),
    _dateKeyword: Optional[str] = Query(
        default=None,
        description="Convenience date range",
        examples=["today", "tomorrow", "this-week"],
    ),
    startDateTime: Optional[str] = Query(
        default=None,
        description="Start of search range (ISO 8601)",
        examples=["2024-12-10T09:00:00"],
    ),
    endDateTime: Optional[str] = Query(
        default=None,
        description="End of search range (ISO 8601)",
        examples=["2024-12-10T17:00:00"],
    ),
    activityDomain: str = Query(
        default="work",
        description="Activity domain",
        examples=["work", "personal", "unrestricted"],
    ),
    maxCandidates: Optional[int] = Query(
        default=None, ge=1, le=50, description="Maximum suggestions"
    ),
    minimumAttendeePercentage: Optional[float] = Query(
        default=None, ge=0, le=100, description="Minimum attendee availability %"
    ),
):
    if not template_body or not template_body.strip():
        raise HTTPException(status_code=400, detail="Template body is required")

    # Parse attendees from comma-separated string
    attendee_list = [
        {"emailAddress": {"address": email.strip()}}
        for email in attendees.split(",")
        if email.strip()
    ]

    if not attendee_list:
        raise HTTPException(status_code=400, detail="At least one attendee is required")

    # Build time constraint
    time_constraint = None
    if _dateKeyword:
        start_dt, end_dt = parse_date_keyword_to_range(_dateKeyword)
        time_constraint = {
            "activityDomain": activityDomain,
            "timeSlots": [
                {
                    "start": {"dateTime": start_dt.isoformat()},
                    "end": {"dateTime": end_dt.isoformat()},
                }
            ],
        }
    elif startDateTime and endDateTime:
        time_constraint = {
            "activityDomain": activityDomain,
            "timeSlots": [
                {"start": {"dateTime": startDateTime}, "end": {"dateTime": endDateTime}}
            ],
        }

    # Find meeting times and render template
    # TemplateError propagates to global handler for 400 response
    # Other exceptions wrapped in GraphAPIError for 502 response
    result = await availability_service.find_meeting_times(
        attendees=attendee_list,
        time_constraint=time_constraint,
        meeting_duration=meetingDuration,
        max_candidates=maxCandidates,
        return_suggestion_reasons=True,
        minimum_attendee_percentage=minimumAttendeePercentage,
    )

    rendered = template_service.render(
        template_string=template_body,
        suggestions=result.get("meetingTimeSuggestions", []),
        count=len(result.get("meetingTimeSuggestions", [])),
        emptySuggestionsReason=result.get("emptySuggestionsReason", ""),
        attendees=attendee_list,
        duration=meetingDuration,
    )

    return PlainTextResponse(content=rendered)
