"""Shared query parameter models for MS Graph-style endpoints"""

from dataclasses import dataclass
from typing import Optional, List
from fastapi import HTTPException

from app.models.filters import (
    Importance,
    Sensitivity,
    ShowAs,
    ResponseStatus,
    build_odata_filter,
)
from app.utils.date_utils import parse_date_keyword_to_range


@dataclass
class CalendarViewParams:
    """Resolved parameters for CalendarView requests"""

    start_date_time: str
    end_date_time: str
    select: Optional[List[str]]
    filter: Optional[str]
    orderby: Optional[List[str]]
    top: Optional[int]
    skip: Optional[int]


def resolve_calendar_view_params(
    # MS Graph standard params
    startDateTime: Optional[str],
    endDateTime: Optional[str],
    select: Optional[str],
    filter: Optional[str],
    orderby: Optional[str],
    top: Optional[int],
    skip: Optional[int],
    # Extension params
    _dateKeyword: Optional[str],
    # Friendly filter params
    _importance: Optional[Importance],
    _sensitivity: Optional[Sensitivity],
    _showAs: Optional[ShowAs],
    _responseStatus: Optional[ResponseStatus],
    _isAllDay: Optional[bool],
    _isOnlineMeeting: Optional[bool],
    _isCancelled: Optional[bool],
    _hasAttachments: Optional[bool],
    _categories: Optional[str],
) -> CalendarViewParams:
    """
    Resolve and validate CalendarView parameters.

    Handles:
    - Date keyword resolution to start/end datetime
    - Comma-separated string parsing to lists
    - Friendly filter params to OData filter string

    Raises:
        HTTPException: If required params are missing or invalid

    Returns:
        CalendarViewParams with resolved values
    """
    # Resolve date range from keyword
    if _dateKeyword:
        try:
            start_dt, end_dt = parse_date_keyword_to_range(_dateKeyword)
            startDateTime = start_dt.isoformat()
            endDateTime = end_dt.isoformat()
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # Validate required params
    if not startDateTime or not endDateTime:
        raise HTTPException(
            status_code=400,
            detail="Either startDateTime/endDateTime or _dateKeyword is required",
        )

    # Parse comma-separated strings to lists
    select_list = [s.strip() for s in select.split(",")] if select else None
    orderby_list = [o.strip() for o in orderby.split(",")] if orderby else None
    categories_list = (
        [c.strip() for c in _categories.split(",")] if _categories else None
    )

    # Build combined OData filter
    combined_filter = build_odata_filter(
        base_filter=filter,
        importance=_importance,
        sensitivity=_sensitivity,
        show_as=_showAs,
        is_all_day=_isAllDay,
        is_cancelled=_isCancelled,
        is_online_meeting=_isOnlineMeeting,
        has_attachments=_hasAttachments,
        response_status=_responseStatus,
        categories=categories_list,
    )

    return CalendarViewParams(
        start_date_time=startDateTime,
        end_date_time=endDateTime,
        select=select_list,
        filter=combined_filter,
        orderby=orderby_list,
        top=top,
        skip=skip,
    )
