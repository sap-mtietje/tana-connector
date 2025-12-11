"""Availability service - Find meeting times via MS Graph Kiota SDK."""

from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict, List, Optional

from msgraph.generated.models.activity_domain import ActivityDomain
from msgraph.generated.models.attendee_base import AttendeeBase
from msgraph.generated.models.date_time_time_zone import DateTimeTimeZone
from msgraph.generated.models.location_constraint import LocationConstraint
from msgraph.generated.models.location_constraint_item import LocationConstraintItem
from msgraph.generated.models.time_constraint import TimeConstraint
from msgraph.generated.models.time_slot import TimeSlot
from msgraph.generated.users.item.find_meeting_times.find_meeting_times_post_request_body import (
    FindMeetingTimesPostRequestBody,
)

from app.services.graph_service import GraphService
from app.utils.attendee_utils import build_attendees
from app.utils.timezone_utils import format_graph_datetime, get_system_timezone_name


class AvailabilityService:
    """Find meeting times using Kiota SDK, returning MS Graph format.

    Args:
        graph_service: GraphService instance for MS Graph API calls (required).
    """

    def __init__(self, graph_service: GraphService) -> None:
        self._graph_service = graph_service

    async def find_meeting_times(
        self,
        attendees: List[Dict[str, Any]],
        time_constraint: Optional[Dict[str, Any]] = None,
        location_constraint: Optional[Dict[str, Any]] = None,
        meeting_duration: str = "PT1H",
        max_candidates: Optional[int] = None,
        is_organizer_optional: bool = False,
        return_suggestion_reasons: bool = True,
        minimum_attendee_percentage: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Find available meeting times for attendees.

        Args:
            attendees: List of attendee dicts with 'emailAddress' and optional 'type'
                       e.g., [{"emailAddress": {"address": "user@example.com", "name": "User"}, "type": "required"}]
            time_constraint: Time constraint with 'activityDomain' and 'timeSlots'
                            e.g., {"activityDomain": "work", "timeSlots": [{"start": {...}, "end": {...}}]}
            location_constraint: Location constraint with 'isRequired', 'suggestLocation', 'locations'
            meeting_duration: ISO 8601 duration (default "PT1H" = 1 hour)
            max_candidates: Maximum number of suggestions to return
            is_organizer_optional: Whether organizer attendance is optional
            return_suggestion_reasons: Include reason for each suggestion
            minimum_attendee_percentage: Minimum % of attendees that must be available (0-100)

        Returns:
            Dict with:
            - meetingTimeSuggestions: List of meeting time suggestions
            - emptySuggestionsReason: Reason if no suggestions found
        """
        client = await self._graph_service.get_client()
        timezone_name = get_system_timezone_name()

        # Build request body
        request_body = FindMeetingTimesPostRequestBody()

        # Attendees
        request_body.attendees = self._build_attendees(attendees)

        # Time constraint
        if time_constraint:
            request_body.time_constraint = self._build_time_constraint(
                time_constraint, timezone_name
            )

        # Location constraint
        if location_constraint:
            request_body.location_constraint = self._build_location_constraint(
                location_constraint
            )

        # Duration (parse ISO 8601 duration string to timedelta)
        request_body.meeting_duration = self._parse_duration(meeting_duration)

        # Other options
        request_body.is_organizer_optional = is_organizer_optional
        request_body.return_suggestion_reasons = return_suggestion_reasons

        if max_candidates is not None:
            request_body.max_candidates = max_candidates

        if minimum_attendee_percentage is not None:
            request_body.minimum_attendee_percentage = minimum_attendee_percentage

        # Execute request
        result = await client.me.find_meeting_times.post(request_body)

        if not result:
            return {
                "meetingTimeSuggestions": [],
                "emptySuggestionsReason": "No response from API",
            }

        # Convert to dict format
        return self._result_to_dict(result)

    def _build_attendees(self, attendees: List[Dict[str, Any]]) -> List[AttendeeBase]:
        """Convert attendee dicts to Kiota AttendeeBase objects."""
        return build_attendees(attendees, AttendeeBase)

    def _build_time_constraint(
        self, constraint: Dict[str, Any], default_timezone: str
    ) -> TimeConstraint:
        """Convert time constraint dict to Kiota TimeConstraint object."""
        time_constraint = TimeConstraint()

        # Activity domain
        activity_domain = constraint.get("activityDomain", "work").lower()
        domain_map = {
            "work": ActivityDomain.Work,
            "personal": ActivityDomain.Personal,
            "unrestricted": ActivityDomain.Unrestricted,
            "unknown": ActivityDomain.Unknown,
        }
        time_constraint.activity_domain = domain_map.get(
            activity_domain, ActivityDomain.Work
        )

        # Time slots
        time_slots = []
        for slot_data in constraint.get("timeSlots", []):
            time_slot = TimeSlot()

            # Start
            start_data = slot_data.get("start", {})
            start = DateTimeTimeZone()
            start.date_time = start_data.get("dateTime")
            start.time_zone = start_data.get("timeZone", default_timezone)
            time_slot.start = start

            # End
            end_data = slot_data.get("end", {})
            end = DateTimeTimeZone()
            end.date_time = end_data.get("dateTime")
            end.time_zone = end_data.get("timeZone", default_timezone)
            time_slot.end = end

            time_slots.append(time_slot)

        time_constraint.time_slots = time_slots
        return time_constraint

    def _build_location_constraint(
        self, constraint: Dict[str, Any]
    ) -> LocationConstraint:
        """Convert location constraint dict to Kiota LocationConstraint object."""
        location_constraint = LocationConstraint()
        location_constraint.is_required = constraint.get("isRequired", False)
        location_constraint.suggest_location = constraint.get("suggestLocation", False)

        # Locations
        locations = []
        for loc_data in constraint.get("locations", []):
            location = LocationConstraintItem()
            location.display_name = loc_data.get("displayName")
            location.resolve_availability = loc_data.get("resolveAvailability", False)
            locations.append(location)

        location_constraint.locations = locations
        return location_constraint

    def _parse_duration(self, duration_str: str) -> timedelta:
        """Parse ISO 8601 duration string to timedelta."""
        # Simple parser for common formats: PT1H, PT30M, PT1H30M
        duration_str = duration_str.upper()
        if not duration_str.startswith("PT"):
            # Default to 1 hour if invalid
            return timedelta(hours=1)

        duration_str = duration_str[2:]  # Remove "PT"
        hours = 0
        minutes = 0

        if "H" in duration_str:
            parts = duration_str.split("H")
            hours = int(parts[0]) if parts[0] else 0
            duration_str = parts[1] if len(parts) > 1 else ""

        if "M" in duration_str:
            parts = duration_str.split("M")
            minutes = int(parts[0]) if parts[0] else 0

        return timedelta(hours=hours, minutes=minutes)

    def _result_to_dict(self, result) -> Dict[str, Any]:
        """Convert Kiota MeetingTimeSuggestionsResult to dict."""
        suggestions = []

        if result.meeting_time_suggestions:
            for suggestion in result.meeting_time_suggestions:
                sugg_dict = {
                    "confidence": suggestion.confidence,
                    "order": suggestion.order,
                    "organizerAvailability": str(suggestion.organizer_availability)
                    if suggestion.organizer_availability
                    else None,
                }

                # Suggestion reason
                if suggestion.suggestion_reason:
                    sugg_dict["suggestionReason"] = suggestion.suggestion_reason

                # Meeting time slot
                if suggestion.meeting_time_slot:
                    sugg_dict["meetingTimeSlot"] = {
                        "start": {
                            "dateTime": self._format_graph_datetime(
                                suggestion.meeting_time_slot.start.date_time
                            )
                            if suggestion.meeting_time_slot.start
                            else None,
                            "timeZone": suggestion.meeting_time_slot.start.time_zone
                            if suggestion.meeting_time_slot.start
                            else None,
                        },
                        "end": {
                            "dateTime": self._format_graph_datetime(
                                suggestion.meeting_time_slot.end.date_time
                            )
                            if suggestion.meeting_time_slot.end
                            else None,
                            "timeZone": suggestion.meeting_time_slot.end.time_zone
                            if suggestion.meeting_time_slot.end
                            else None,
                        },
                    }

                # Attendee availability
                if suggestion.attendee_availability:
                    sugg_dict["attendeeAvailability"] = [
                        {
                            "availability": str(att.availability)
                            if att.availability
                            else None,
                            "attendee": {
                                "emailAddress": {
                                    "address": att.attendee.email_address.address
                                    if att.attendee and att.attendee.email_address
                                    else None,
                                    "name": att.attendee.email_address.name
                                    if att.attendee and att.attendee.email_address
                                    else None,
                                }
                            }
                            if att.attendee
                            else None,
                        }
                        for att in suggestion.attendee_availability
                    ]

                # Locations
                if suggestion.locations:
                    sugg_dict["locations"] = [
                        {"displayName": loc.display_name}
                        for loc in suggestion.locations
                    ]

                suggestions.append(sugg_dict)

        return {
            "meetingTimeSuggestions": suggestions,
            "emptySuggestionsReason": result.empty_suggestions_reason or "",
            "@odata.context": "$metadata#microsoft.graph.meetingTimeSuggestionsResult",
        }

    def _format_graph_datetime(self, datetime_str: str) -> Optional[str]:
        """Convert MS Graph datetime string to ISO format with timezone offset."""
        return format_graph_datetime(datetime_str)

    def format_as_tana(
        self,
        result: Dict[str, Any],
        subject: str = "Meeting",
        tag: str = "meeting-proposal",
    ) -> str:
        """
        Format meeting time suggestions as Tana Paste.

        Simple default format - for complex formatting, use POST with template.
        """
        suggestions = result.get("meetingTimeSuggestions", [])

        if not suggestions:
            reason = result.get("emptySuggestionsReason", "No available times found")
            return (
                f"%%tana%%\n- No meeting times available #{tag}\n  - Reason:: {reason}"
            )

        lines = ["%%tana%%", f"- {subject} #{tag}"]

        for sugg in suggestions:
            slot = sugg.get("meetingTimeSlot", {})
            start = slot.get("start", {})
            end = slot.get("end", {})
            confidence = sugg.get("confidence", 0)
            order = sugg.get("order", 0)

            start_dt = start.get("dateTime", "")
            end_dt = end.get("dateTime", "")

            lines.append(f"  - Option {order}:: [[date:{start_dt}/{end_dt}]]")
            lines.append(f"    - Confidence:: {confidence}%")

            # Organizer availability
            org_avail = sugg.get("organizerAvailability")
            if org_avail:
                lines.append(f"    - Organizer:: {org_avail}")

            # Suggestion reason
            reason = sugg.get("suggestionReason")
            if reason:
                lines.append(f"    - Reason:: {reason}")

        return "\n".join(lines)
