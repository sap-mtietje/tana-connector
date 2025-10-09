"""Integration tests for /events.tana endpoint"""

import pytest
from unittest.mock import patch


@pytest.mark.integration
class TestEventsEndpointTana:
    """Tests for /events.tana endpoint"""

    @patch("app.services.events_service.events_service.get_events")
    async def test_get_events_tana_basic(self, mock_get_events, client, sample_event):
        """Should return events in Tana Paste format"""
        mock_get_events.return_value = [sample_event]

        response = client.get("/events.tana")

        assert response.status_code == 200
        content = response.text

        # Check Tana format
        assert "- Team Meeting #[[meeting]]" in content
        assert "Location::" in content
        assert "Status::" in content

    @patch("app.services.events_service.events_service.get_events")
    async def test_get_events_tana_custom_tag(
        self, mock_get_events, client, sample_event
    ):
        """Should use custom tag"""
        mock_get_events.return_value = [sample_event]

        response = client.get("/events.tana?tag=work")

        assert response.status_code == 200
        content = response.text
        assert "#[[work]]" in content
        assert "#[[meeting]]" not in content

    @patch("app.services.events_service.events_service.get_events")
    async def test_get_events_tana_category_tags(
        self, mock_get_events, client, sample_event
    ):
        """Should use category tags when enabled"""
        mock_get_events.return_value = [sample_event]

        response = client.get("/events.tana?includeCategoryTags=true")

        assert response.status_code == 200
        content = response.text
        assert "#[[Work]]" in content
        assert "#[[Important]]" in content

    @patch("app.services.events_service.events_service.get_events")
    async def test_get_events_tana_field_tags(
        self, mock_get_events, client, sample_event
    ):
        """Should apply field tags"""
        mock_get_events.return_value = [sample_event]

        response = client.get(
            "/events.tana?fieldTags=attendees:co-worker,location:office"
        )

        assert response.status_code == 200
        content = response.text
        # Field tags should be applied to attendees
        assert "#co-worker" in content or "#office" in content

    @patch("app.services.events_service.events_service.get_events")
    async def test_get_events_tana_show_empty_false(
        self, mock_get_events, client, sample_event
    ):
        """Should hide empty fields when showEmpty is false"""
        sample_event["location"] = ""
        mock_get_events.return_value = [sample_event]

        response = client.get("/events.tana?showEmpty=false")

        assert response.status_code == 200
        content = response.text
        # Empty location should not appear when showEmpty is false
        assert "Location::" not in content

    @patch("app.services.events_service.events_service.get_events")
    async def test_get_events_tana_fields_filter(
        self, mock_get_events, client, sample_event
    ):
        """Should only show specified fields"""
        mock_get_events.return_value = [sample_event]

        response = client.get("/events.tana?fields=title,date,location")

        assert response.status_code == 200
        content = response.text

        # Should have these fields
        assert "Date::" in content
        assert "Location::" in content

        # Should NOT have these fields
        assert "Status::" not in content
        assert "Attendees::" not in content

    @patch("app.services.events_service.events_service.get_events")
    async def test_get_events_tana_multiple_events(
        self, mock_get_events, client, sample_event
    ):
        """Should format multiple events"""
        event2 = sample_event.copy()
        event2["title"] = "Another Meeting"
        mock_get_events.return_value = [sample_event, event2]

        response = client.get("/events.tana")

        assert response.status_code == 200
        content = response.text
        assert "- Team Meeting" in content
        assert "- Another Meeting" in content

    @patch("app.services.events_service.events_service.get_events")
    async def test_get_events_tana_empty_result(self, mock_get_events, client):
        """Should handle empty event list"""
        mock_get_events.return_value = []

        response = client.get("/events.tana")

        assert response.status_code == 200
        assert response.text == ""
