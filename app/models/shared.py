"""Shared Pydantic models for MS Graph API requests/responses."""

from typing import Optional, List

from pydantic import BaseModel, Field


class EmailAddressModel(BaseModel):
    """Email address with optional display name."""

    address: str = Field(
        ...,
        description="Email address",
        examples=["user@example.com"],
    )
    name: Optional[str] = Field(
        default=None,
        description="Display name",
        examples=["John Doe"],
    )


class DateTimeTimeZoneModel(BaseModel):
    """DateTime with timezone for MS Graph API."""

    dateTime: str = Field(
        ...,
        description="ISO 8601 datetime",
        examples=["2024-12-10T09:00:00"],
    )
    timeZone: Optional[str] = Field(
        default=None,
        description="Timezone name (defaults to system timezone)",
        examples=["Europe/Berlin", "Pacific Standard Time"],
    )


class AttendeeModel(BaseModel):
    """Attendee for calendar events and meeting requests."""

    emailAddress: EmailAddressModel
    type: Optional[str] = Field(
        default="required",
        description="Attendee type: required, optional, resource",
        examples=["required", "optional"],
    )


class LocationModel(BaseModel):
    """Location for calendar events."""

    displayName: str = Field(
        ...,
        description="Location name",
        examples=["Conference Room A", "Teams Meeting"],
    )
    resolveAvailability: Optional[bool] = Field(
        default=False,
        description="Check room availability (for meeting rooms)",
    )


class ItemBodyModel(BaseModel):
    """Body content for events and messages."""

    contentType: Optional[str] = Field(
        default="HTML",
        description="Content type: HTML or Text",
        examples=["HTML", "Text"],
    )
    content: str = Field(
        ...,
        description="Body content",
    )


class TimeSlotModel(BaseModel):
    """Time slot for availability search."""

    start: DateTimeTimeZoneModel
    end: DateTimeTimeZoneModel


class TimeConstraintModel(BaseModel):
    """Time constraint for meeting search."""

    activityDomain: Optional[str] = Field(
        default="work",
        description="Activity domain: work, personal, unrestricted",
        examples=["work"],
    )
    timeSlots: List[TimeSlotModel] = Field(
        ...,
        description="List of time slots to search within",
    )


class LocationConstraintModel(BaseModel):
    """Location constraint for meeting search."""

    isRequired: Optional[bool] = Field(
        default=False,
        description="Whether location is required",
    )
    suggestLocation: Optional[bool] = Field(
        default=False,
        description="Whether to suggest locations",
    )
    locations: Optional[List[LocationModel]] = Field(
        default=None,
        description="Preferred locations",
    )
