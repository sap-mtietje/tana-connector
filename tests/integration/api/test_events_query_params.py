"""Integration tests for query parameter parsing and validation"""

import pytest
from unittest.mock import patch


@pytest.mark.integration
class TestEventsEndpointQueryParameters:
    """Tests for query parameter parsing and validation (parametrized)"""

    @pytest.mark.parametrize(
        "qs,arg_key,expected",
        [
            ("filterAttendee=john,jane", "filter_attendee", ["john", "jane"]),
            (
                "filterStatus=Accepted,Tentative",
                "filter_status",
                ["Accepted", "Tentative"],
            ),
            (
                "filterCategories=Work,Personal",
                "filter_categories",
                ["Work", "Personal"],
            ),
        ],
        ids=["attendees", "status", "categories"],
    )
    @patch("app.services.events_service.events_service.get_events")
    async def test_comma_separated_filters(
        self, mock_get_events, client, sample_event, qs, arg_key, expected
    ):
        mock_get_events.return_value = [sample_event]

        response = client.get(f"/events.json?{qs}")

        assert response.status_code == 200
        call_args = mock_get_events.call_args
        assert call_args[1][arg_key] == expected

    @pytest.mark.parametrize(
        "value",
        ["true", "false"],
        ids=["include-all-day-true", "include-all-day-false"],
    )
    @patch("app.services.events_service.events_service.get_events")
    async def test_include_all_day_boolean(
        self, mock_get_events, client, sample_event, value
    ):
        mock_get_events.return_value = [sample_event]
        response = client.get(f"/events.json?includeAllDay={value}")
        assert response.status_code == 200

    @patch("app.services.events_service.events_service.get_events")
    async def test_calendar_filter(self, mock_get_events, client, sample_event):
        mock_get_events.return_value = [sample_event]

        response = client.get("/events.json?calendar=Work%20Calendar")

        assert response.status_code == 200
        call_args = mock_get_events.call_args
        assert call_args[1]["filter_calendar"] == "Work Calendar"
