"""Integration tests for /events.json endpoint"""

import pytest
from unittest.mock import patch


@pytest.mark.integration
class TestEventsEndpointJSON:
    """Tests for /events.json endpoint (JSON format)"""

    @patch("app.services.events_service.events_service.get_events")
    async def test_get_events_json_basic(self, mock_get_events, client, sample_event):
        """Should return events in JSON format"""
        mock_get_events.return_value = [sample_event]

        response = client.get("/events.json")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 1
        assert len(data["events"]) == 1
        assert data["events"][0]["title"] == "Team Meeting"

    @patch("app.services.events_service.events_service.get_events")
    async def test_get_events_json_with_date_keyword(
        self, mock_get_events, client, sample_event
    ):
        """Should handle date keywords"""
        mock_get_events.return_value = [sample_event]

        response = client.get("/events.json?date=tomorrow")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @patch("app.services.events_service.events_service.get_events")
    async def test_get_events_json_with_offset(
        self, mock_get_events, client, sample_event
    ):
        """Should handle offset parameter"""
        mock_get_events.return_value = [sample_event]

        response = client.get("/events.json?offset=7")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["metadata"]["startDate"]
        assert data["metadata"]["endDate"]

    @patch("app.services.events_service.events_service.get_events")
    async def test_get_events_json_with_fields_filter(
        self, mock_get_events, client, sample_event
    ):
        """Should filter fields when specified"""
        mock_get_events.return_value = [sample_event]

        response = client.get("/events.json?fields=title,location,date")

        assert response.status_code == 200
        data = response.json()
        event = data["events"][0]

        # Should only have specified fields
        assert "title" in event
        assert "location" in event
        assert "date" in event

        # Should NOT have other fields
        assert "attendees" not in event
        assert "description" not in event

    @patch("app.services.events_service.events_service.get_events")
    async def test_get_events_json_with_title_filter(
        self, mock_get_events, client, sample_event
    ):
        """Should apply title filter"""
        mock_get_events.return_value = [sample_event]

        response = client.get("/events.json?filterTitle=Team")

        assert response.status_code == 200
        # The filtering happens in the service, so we just verify it's called
        mock_get_events.assert_called_once()

    @patch("app.services.events_service.events_service.get_events")
    async def test_get_events_json_with_multiple_filters(
        self, mock_get_events, client, sample_event
    ):
        """Should handle multiple filters"""
        mock_get_events.return_value = [sample_event]

        response = client.get(
            "/events.json?filterTitle=Meeting&filterStatus=Accepted&includeAllDay=false"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["filters"]["title"] == "Meeting"
        assert data["metadata"]["filters"]["status"] == "Accepted"
        assert data["metadata"]["filters"]["allDay"] is False

    @patch("app.services.events_service.events_service.get_events")
    async def test_get_events_json_empty_result(self, mock_get_events, client):
        """Should handle empty event list"""
        mock_get_events.return_value = []

        response = client.get("/events.json")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 0
        assert data["events"] == []

    @pytest.mark.parametrize(
        "mode,expected_empty",
        [("clean", False), ("none", True)],
        ids=["clean", "none"],
    )
    @patch("app.services.events_service.events_service.get_events")
    async def test_get_events_json_description_modes(
        self, mock_get_events, client, sample_event, mode, expected_empty
    ):
        """Should handle different description modes (parametrized)"""
        mock_get_events.return_value = [sample_event]

        response = client.get(f"/events.json?descriptionMode={mode}")
        assert response.status_code == 200
        data = response.json()
        desc = data["events"][0]["description"]
        assert (desc == "") is expected_empty

    @patch("app.services.events_service.events_service.get_events")
    async def test_get_events_json_description_length(
        self, mock_get_events, client, sample_event
    ):
        """Should truncate description to max length"""
        sample_event["description"] = "A" * 1000
        mock_get_events.return_value = [sample_event]

        response = client.get("/events.json?descriptionLength=50")

        assert response.status_code == 200
        data = response.json()
        assert len(data["events"][0]["description"]) <= 53  # 50 + "..."
