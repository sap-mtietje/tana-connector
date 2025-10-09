"""Shared query params and enums for events endpoints"""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel
from fastapi import Query

from app.constants import EVENTS_AVAILABLE_FIELDS, EVENTS_DATE_KEYWORDS


class DescriptionMode(str, Enum):
    full = "full"
    clean = "clean"
    none = "none"


class EventsQueryParams(BaseModel):
    date: Optional[str] = None
    offset: int = 1
    filterTitle: Optional[str] = None
    filterAttendee: Optional[str] = None
    filterStatus: Optional[str] = None
    filterAvailability: Optional[str] = None
    filterCategories: Optional[str] = None
    includeAllDay: Optional[bool] = None
    calendar: Optional[str] = None
    tag: str = "meeting"
    includeCategoryTags: bool = False
    fieldTags: Optional[str] = None
    fields: Optional[str] = None
    showEmpty: bool = True
    descriptionMode: DescriptionMode = DescriptionMode.full
    descriptionLength: Optional[int] = None

    @property
    def parsed_filter_title(self) -> Optional[List[str]]:
        return [self.filterTitle] if self.filterTitle else None

    @property
    def parsed_filter_attendee(self) -> Optional[List[str]]:
        return self._split_csv(self.filterAttendee)

    @property
    def parsed_filter_status(self) -> Optional[List[str]]:
        return self._split_csv(self.filterStatus)

    @property
    def parsed_filter_availability(self) -> Optional[List[str]]:
        return self._split_csv(self.filterAvailability)

    @property
    def parsed_filter_categories(self) -> Optional[List[str]]:
        return self._split_csv(self.filterCategories)

    @staticmethod
    def _split_csv(value: Optional[str]) -> Optional[List[str]]:
        return [v.strip() for v in value.split(",")] if value else None


def events_query_params(
    date: Optional[str] = Query(
        default=None,
        description=f"Start date. Keywords: {', '.join(EVENTS_DATE_KEYWORDS)} or YYYY-MM-DD format",
        examples=["today", "tomorrow", "next-week", "2025-10-15"],
    ),
    offset: int = Query(
        default=1,
        ge=1,
        le=365,
        description="Number of days to fetch",
        examples=[1, 7, 30],
    ),
    filterTitle: Optional[str] = Query(
        default=None,
        description="Filter by title (case-insensitive substring match)",
        examples=["standup", "review"],
    ),
    filterAttendee: Optional[str] = Query(
        default=None,
        description="Filter by attendee (comma-separated, case-insensitive)",
        examples=["john@company.com", "john,jane"],
    ),
    filterStatus: Optional[str] = Query(
        default=None,
        description=(
            "Filter by response status (comma-separated, case-sensitive). Values: "
            "Accepted, Declined, Tentative, No Response, None, Organizer"
        ),
        examples=["Accepted", "Organizer", "Accepted,No Response"],
    ),
    filterAvailability: Optional[str] = Query(
        default=None,
        description=(
            "Filter by availability (comma-separated, case-sensitive). Values: Free, Busy, "
            "Tentative, Out of Office, Working Elsewhere, Unknown."
        ),
        examples=["Busy", "Out of Office", "Busy,Tentative"],
    ),
    filterCategories: Optional[str] = Query(
        default=None,
        description="Filter by categories (comma-separated, case-insensitive)",
        examples=["Work", "Personal,Work"],
    ),
    includeAllDay: Optional[bool] = Query(
        default=None,
        description=(
            "Filter all-day events. true=only all-day, false=exclude all-day, null=include both"
        ),
        examples=[True, False, None],
    ),
    calendar: Optional[str] = Query(
        default=None,
        description="Filter by calendar name",
        examples=["Calendar", "Work Calendar"],
    ),
    tag: str = Query(
        default="meeting",
        description="Base Tana tag for all events",
        examples=["meeting", "work", "personal"],
    ),
    includeCategoryTags: bool = Query(
        default=False,
        description="Auto-convert categories to Tana tags instead of using base tag",
        examples=[True, False],
    ),
    fieldTags: Optional[str] = Query(
        default=None,
        description=(
            "Tag specific fields in Tana format (field:tag,field:tag). Supported: attendees, organizer, categories, location"
        ),
        examples=["attendees:co-worker,organizer:manager", "location:office"],
    ),
    fields: Optional[str] = Query(
        default=None,
        description=(
            f"Include only these fields (comma-separated). Available: {', '.join(sorted(EVENTS_AVAILABLE_FIELDS))}"
        ),
        examples=["date,location,attendees", "start,end,title,status"],
    ),
    showEmpty: bool = Query(
        default=True, description="Show fields even when empty", examples=[True, False]
    ),
    descriptionMode: DescriptionMode = Query(
        default=DescriptionMode.full,
        description="Description processing: full=complete, clean=remove meeting links/HTML, none=omit",
        examples=["full", "clean", "none"],
    ),
    descriptionLength: Optional[int] = Query(
        default=None,
        ge=1,
        le=5000,
        description="Max description length (1-5000 characters)",
        examples=[100, 500, 1000],
    ),
) -> EventsQueryParams:
    return EventsQueryParams(
        date=date,
        offset=offset,
        filterTitle=filterTitle,
        filterAttendee=filterAttendee,
        filterStatus=filterStatus,
        filterAvailability=filterAvailability,
        filterCategories=filterCategories,
        includeAllDay=includeAllDay,
        calendar=calendar,
        tag=tag,
        includeCategoryTags=includeCategoryTags,
        fieldTags=fieldTags,
        fields=fields,
        showEmpty=showEmpty,
        descriptionMode=descriptionMode,
        descriptionLength=descriptionLength,
    )
