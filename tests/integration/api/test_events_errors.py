"""Integration tests for events endpoints error handling"""

import pytest
from unittest.mock import patch


@pytest.mark.integration
class TestEventsEndpointErrors:
    """Tests for error handling in events endpoints"""

    def test_invalid_format(self, client):
        """Should reject invalid format"""
        response = client.get("/events.xml")
        # FastAPI returns 422 for path parameter validation errors
        assert response.status_code == 422

    def test_invalid_date_keyword(self, client):
        """Should reject invalid date keyword for GET JSON"""
        response = client.get("/events.json?date=invalid-keyword")
        assert response.status_code == 400
        data = response.json()
        assert "Invalid date format" in data["detail"]

    @patch("app.services.events_service.events_service.get_events")
    async def test_service_exception(self, mock_get_events, client):
        """Should handle service exceptions gracefully"""
        mock_get_events.side_effect = Exception("Service error")

        response = client.get("/events.json")

        assert response.status_code == 500
        data = response.json()
        assert "Failed to fetch events" in data["detail"]

    def test_description_mode_invalid(self, client):
        """Should reject invalid description mode"""
        response = client.get("/events.json?descriptionMode=invalid")
        assert response.status_code == 422

    @pytest.mark.parametrize(
        "qs",
        [
            "offset=0",
            "offset=400",
            "descriptionLength=0",
            "descriptionLength=10000",
        ],
        ids=["offset-too-low", "offset-too-high", "desc-too-low", "desc-too-high"],
    )
    def test_invalid_query_values(self, client, qs):
        """Should return validation errors for invalid query values"""
        response = client.get(f"/events.json?{qs}")
        assert response.status_code == 422

    @patch("app.services.events_service.events_service.get_events")
    async def test_value_error_from_service(self, mock_get_events, client):
        """Should return 400 for ValueError from service"""
        mock_get_events.side_effect = ValueError("Invalid filter")

        response = client.get("/events.json")

        assert response.status_code == 400
        data = response.json()
        assert "Invalid filter" in data["detail"]
