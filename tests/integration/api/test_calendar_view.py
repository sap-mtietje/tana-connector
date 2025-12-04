"""
Comprehensive tests for GET /me/CalendarView and POST /me/CalendarView endpoints.

Tests cover:
- Basic functionality (date params, date keywords)
- Friendly filter params (_importance, _showAs, _isAllDay, etc.)
- OData filter param
- Combined friendly + OData filters
- Response formats (JSON, Tana)
- Template rendering (POST)
- Error handling
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from tests.fixtures.factories import (
    make_ms_graph_event,
)


class TestCalendarViewGet:
    """Tests for GET /me/CalendarView endpoint"""

    # -------------------------------------------------------------------------
    # Basic Functionality
    # -------------------------------------------------------------------------

    def test_get_calendar_view_with_date_keyword(self, client, mock_calendar_service):
        """Test GET with _dateKeyword parameter"""
        mock_calendar_service.return_value = [make_ms_graph_event()]

        response = client.get("/me/CalendarView?_dateKeyword=today")

        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert "@odata.count" in data
        assert data["@odata.count"] == 1

    def test_get_calendar_view_with_explicit_dates(self, client, mock_calendar_service):
        """Test GET with explicit startDateTime and endDateTime"""
        mock_calendar_service.return_value = [make_ms_graph_event()]

        response = client.get(
            "/me/CalendarView"
            "?startDateTime=2025-10-05T00:00:00"
            "&endDateTime=2025-10-05T23:59:59"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["@odata.count"] == 1

    def test_get_calendar_view_missing_dates_returns_400(self, client):
        """Test that missing date params returns 400"""
        response = client.get("/me/CalendarView")

        assert response.status_code == 400
        assert "startDateTime/endDateTime or _dateKeyword" in response.json()["detail"]

    def test_get_calendar_view_invalid_date_keyword_returns_400(
        self, client, mock_calendar_service
    ):
        """Test that invalid _dateKeyword returns 400"""
        response = client.get("/me/CalendarView?_dateKeyword=invalid-keyword")

        assert response.status_code == 400

    def test_get_calendar_view_empty_results(self, client, mock_calendar_service):
        """Test GET returns empty list when no events"""
        mock_calendar_service.return_value = []

        response = client.get("/me/CalendarView?_dateKeyword=today")

        assert response.status_code == 200
        data = response.json()
        assert data["value"] == []
        assert data["@odata.count"] == 0

    # -------------------------------------------------------------------------
    # Tana Format
    # -------------------------------------------------------------------------

    def test_get_calendar_view_tana_format(self, client, mock_calendar_service):
        """Test GET with _format=tana returns Tana Paste"""
        mock_calendar_service.return_value = [
            make_ms_graph_event(subject="Test Meeting")
        ]

        response = client.get("/me/CalendarView?_dateKeyword=today&_format=tana")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        assert "%%tana%%" in response.text
        assert "Test Meeting" in response.text

    def test_get_calendar_view_tana_format_empty(self, client, mock_calendar_service):
        """Test Tana format with no events"""
        mock_calendar_service.return_value = []

        response = client.get("/me/CalendarView?_dateKeyword=today&_format=tana")

        assert response.status_code == 200
        assert "No events found" in response.text


class TestCalendarViewFilters:
    """Tests for friendly filter parameters"""

    # -------------------------------------------------------------------------
    # Single Filter Tests
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize(
        "filter_param,filter_value,expected_odata",
        [
            ("_importance", "high", "importance eq 'high'"),
            ("_importance", "normal", "importance eq 'normal'"),
            ("_importance", "low", "importance eq 'low'"),
            ("_sensitivity", "normal", "sensitivity eq 'normal'"),
            ("_sensitivity", "personal", "sensitivity eq 'personal'"),
            ("_sensitivity", "private", "sensitivity eq 'private'"),
            ("_sensitivity", "confidential", "sensitivity eq 'confidential'"),
            ("_showAs", "free", "showAs eq 'free'"),
            ("_showAs", "busy", "showAs eq 'busy'"),
            ("_showAs", "tentative", "showAs eq 'tentative'"),
            ("_showAs", "oof", "showAs eq 'oof'"),
            ("_showAs", "workingElsewhere", "showAs eq 'workingElsewhere'"),
            ("_responseStatus", "accepted", "responseStatus/response eq 'accepted'"),
            ("_responseStatus", "declined", "responseStatus/response eq 'declined'"),
            (
                "_responseStatus",
                "tentativelyAccepted",
                "responseStatus/response eq 'tentativelyAccepted'",
            ),
            ("_responseStatus", "organizer", "responseStatus/response eq 'organizer'"),
        ],
    )
    def test_enum_filter_generates_correct_odata(
        self, client, mock_calendar_service, filter_param, filter_value, expected_odata
    ):
        """Test that enum filter params generate correct OData filter strings"""
        mock_calendar_service.return_value = []

        response = client.get(
            f"/me/CalendarView?_dateKeyword=today&{filter_param}={filter_value}"
        )

        assert response.status_code == 200
        # Verify the filter was passed to the service
        call_kwargs = mock_calendar_service.call_args.kwargs
        assert expected_odata in call_kwargs.get("filter", "")

    @pytest.mark.parametrize(
        "filter_param,filter_value,expected_odata",
        [
            ("_isAllDay", "true", "isAllDay eq true"),
            ("_isAllDay", "false", "isAllDay eq false"),
            ("_isOnlineMeeting", "true", "isOnlineMeeting eq true"),
            ("_isOnlineMeeting", "false", "isOnlineMeeting eq false"),
            ("_isCancelled", "true", "isCancelled eq true"),
            ("_isCancelled", "false", "isCancelled eq false"),
            ("_hasAttachments", "true", "hasAttachments eq true"),
            ("_hasAttachments", "false", "hasAttachments eq false"),
        ],
    )
    def test_boolean_filter_generates_correct_odata(
        self, client, mock_calendar_service, filter_param, filter_value, expected_odata
    ):
        """Test that boolean filter params generate correct OData filter strings"""
        mock_calendar_service.return_value = []

        response = client.get(
            f"/me/CalendarView?_dateKeyword=today&{filter_param}={filter_value}"
        )

        assert response.status_code == 200
        call_kwargs = mock_calendar_service.call_args.kwargs
        assert expected_odata in call_kwargs.get("filter", "")

    def test_categories_filter_single(self, client, mock_calendar_service):
        """Test _categories filter with single category"""
        mock_calendar_service.return_value = []

        response = client.get("/me/CalendarView?_dateKeyword=today&_categories=Work")

        assert response.status_code == 200
        call_kwargs = mock_calendar_service.call_args.kwargs
        assert "categories/any(c:c eq 'Work')" in call_kwargs.get("filter", "")

    def test_categories_filter_multiple(self, client, mock_calendar_service):
        """Test _categories filter with multiple categories (comma-separated)"""
        mock_calendar_service.return_value = []

        response = client.get(
            "/me/CalendarView?_dateKeyword=today&_categories=Work,Personal"
        )

        assert response.status_code == 200
        call_kwargs = mock_calendar_service.call_args.kwargs
        filter_str = call_kwargs.get("filter", "")
        assert "categories/any(c:c eq 'Work')" in filter_str
        assert "categories/any(c:c eq 'Personal')" in filter_str
        assert " or " in filter_str  # Categories are OR'd together

    # -------------------------------------------------------------------------
    # Combined Filter Tests
    # -------------------------------------------------------------------------

    def test_multiple_friendly_filters_combined(self, client, mock_calendar_service):
        """Test multiple friendly filters are AND'd together"""
        mock_calendar_service.return_value = []

        response = client.get(
            "/me/CalendarView?_dateKeyword=today"
            "&_importance=high"
            "&_showAs=busy"
            "&_isOnlineMeeting=true"
        )

        assert response.status_code == 200
        call_kwargs = mock_calendar_service.call_args.kwargs
        filter_str = call_kwargs.get("filter", "")

        assert "importance eq 'high'" in filter_str
        assert "showAs eq 'busy'" in filter_str
        assert "isOnlineMeeting eq true" in filter_str
        assert filter_str.count(" and ") == 2  # 3 conditions = 2 ANDs

    def test_friendly_and_odata_filters_combined(self, client, mock_calendar_service):
        """Test friendly filters combined with raw OData filter"""
        mock_calendar_service.return_value = []

        response = client.get(
            "/me/CalendarView?_dateKeyword=today"
            "&_importance=high"
            "&$filter=contains(subject,'standup')"
        )

        assert response.status_code == 200
        call_kwargs = mock_calendar_service.call_args.kwargs
        filter_str = call_kwargs.get("filter", "")

        # OData filter should be wrapped in parentheses
        assert "(contains(subject,'standup'))" in filter_str
        assert "importance eq 'high'" in filter_str

    # -------------------------------------------------------------------------
    # Invalid Filter Values
    # -------------------------------------------------------------------------

    def test_invalid_importance_value_returns_422(self, client):
        """Test invalid _importance value returns 422"""
        response = client.get("/me/CalendarView?_dateKeyword=today&_importance=invalid")

        assert response.status_code == 422

    def test_invalid_showAs_value_returns_422(self, client):
        """Test invalid _showAs value returns 422"""
        response = client.get("/me/CalendarView?_dateKeyword=today&_showAs=invalid")

        assert response.status_code == 422


class TestCalendarViewPost:
    """Tests for POST /me/CalendarView endpoint (template rendering)"""

    def test_post_calendar_view_with_template(self, client, mock_calendar_service):
        """Test POST with Jinja2 template"""
        mock_calendar_service.return_value = [
            make_ms_graph_event(subject="Test Meeting")
        ]

        template = """{% for event in events %}
{{ event.subject }}
{% endfor %}"""

        response = client.post(
            "/me/CalendarView/render?_dateKeyword=today",
            content=template,
            headers={"Content-Type": "text/plain"},
        )

        assert response.status_code == 200
        assert "Test Meeting" in response.text

    def test_post_calendar_view_tana_template(self, client, mock_calendar_service):
        """Test POST with Tana Paste template"""
        mock_calendar_service.return_value = [
            make_ms_graph_event(subject="Strategy Meeting"),
            make_ms_graph_event(subject="Team Standup"),
        ]

        template = """%%tana%%
{% for event in events %}
- {{ event.subject }} #meeting
  - Start:: {{ event.start.dateTime }}
{% endfor %}"""

        response = client.post(
            "/me/CalendarView/render?_dateKeyword=today",
            content=template,
            headers={"Content-Type": "text/plain"},
        )

        assert response.status_code == 200
        assert "%%tana%%" in response.text
        assert "Strategy Meeting" in response.text
        assert "Team Standup" in response.text
        assert "#meeting" in response.text

    def test_post_calendar_view_with_filters(self, client, mock_calendar_service):
        """Test POST with friendly filter params"""
        mock_calendar_service.return_value = [make_ms_graph_event()]

        template = "{{ count }} events"

        response = client.post(
            "/me/CalendarView/render?_dateKeyword=today&_importance=high&_showAs=busy",
            content=template,
            headers={"Content-Type": "text/plain"},
        )

        assert response.status_code == 200
        # Verify filters were applied
        call_kwargs = mock_calendar_service.call_args.kwargs
        filter_str = call_kwargs.get("filter", "")
        assert "importance eq 'high'" in filter_str
        assert "showAs eq 'busy'" in filter_str

    def test_post_calendar_view_empty_template_returns_error(self, client):
        """Test POST with empty template returns 400 or 422"""
        response = client.post(
            "/me/CalendarView/render?_dateKeyword=today",
            content="",
            headers={"Content-Type": "text/plain"},
        )

        # FastAPI may return 422 (validation) or 400 (our check)
        assert response.status_code in (400, 422)

    def test_post_calendar_view_invalid_template_returns_400(
        self, client, mock_calendar_service
    ):
        """Test POST with invalid Jinja2 template returns 400"""
        mock_calendar_service.return_value = []

        template = "{% for event in events %}{{ event.subject"  # Missing closing

        response = client.post(
            "/me/CalendarView/render?_dateKeyword=today",
            content=template,
            headers={"Content-Type": "text/plain"},
        )

        assert response.status_code == 400

    def test_post_calendar_view_template_context(self, client, mock_calendar_service):
        """Test that template has access to all context variables"""
        mock_calendar_service.return_value = [make_ms_graph_event()]

        template = """Events: {{ count }}
Start: {{ start_date }}
End: {{ end_date }}"""

        response = client.post(
            "/me/CalendarView/render?_dateKeyword=today",
            content=template,
            headers={"Content-Type": "text/plain"},
        )

        assert response.status_code == 200
        assert "Events: 1" in response.text
        assert "Start:" in response.text
        assert "End:" in response.text


class TestCalendarViewODataParams:
    """Tests for OData query parameters (select, orderby, top, skip)"""

    def test_select_param(self, client, mock_calendar_service):
        """Test select parameter is passed to service"""
        mock_calendar_service.return_value = []

        response = client.get(
            "/me/CalendarView?_dateKeyword=today&select=subject,start,end"
        )

        assert response.status_code == 200
        call_kwargs = mock_calendar_service.call_args.kwargs
        assert call_kwargs["select"] == ["subject", "start", "end"]

    def test_orderby_param(self, client, mock_calendar_service):
        """Test orderby parameter is passed to service"""
        mock_calendar_service.return_value = []

        response = client.get(
            "/me/CalendarView?_dateKeyword=today&orderby=start/dateTime"
        )

        assert response.status_code == 200
        call_kwargs = mock_calendar_service.call_args.kwargs
        assert call_kwargs["orderby"] == ["start/dateTime"]

    def test_top_param(self, client, mock_calendar_service):
        """Test top parameter is passed to service"""
        mock_calendar_service.return_value = []

        response = client.get("/me/CalendarView?_dateKeyword=today&top=10")

        assert response.status_code == 200
        call_kwargs = mock_calendar_service.call_args.kwargs
        assert call_kwargs["top"] == 10

    def test_top_param_max_100(self, client):
        """Test top parameter max value is 100"""
        response = client.get("/me/CalendarView?_dateKeyword=today&top=101")

        assert response.status_code == 422

    def test_skip_param(self, client, mock_calendar_service):
        """Test skip parameter is passed to service"""
        mock_calendar_service.return_value = []

        response = client.get("/me/CalendarView?_dateKeyword=today&skip=20")

        assert response.status_code == 200
        call_kwargs = mock_calendar_service.call_args.kwargs
        assert call_kwargs["skip"] == 20


# -------------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------------


@pytest.fixture
def mock_calendar_service():
    """Mock the calendar_service.get_calendar_view method"""
    with patch(
        "app.routers.graph.calendar.calendar_service.get_calendar_view",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


@pytest.fixture
def client():
    """FastAPI test client"""
    import os

    os.environ["CLIENT_ID"] = "test-client-id"
    os.environ["TENANT_ID"] = "test-tenant-id"

    from app.main import app

    return TestClient(app)
