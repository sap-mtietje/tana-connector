"""Integration tests for API endpoints"""

import pytest
from unittest.mock import patch


@pytest.mark.integration
class TestHealthEndpoints:
    """Tests for health check endpoints"""
    
    def test_root_endpoint(self, client):
        """Should return API information"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Tana-Connector API"
        assert data["version"] == "0.1.0"
        assert data["status"] == "running"
    
    def test_health_check_endpoint(self, client):
        """Should return health status"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"


@pytest.mark.integration
class TestEventsEndpointJSON:
    """Tests for /events.json endpoint"""
    
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
    async def test_get_events_json_with_date_keyword(self, mock_get_events, client, sample_event):
        """Should handle date keywords"""
        mock_get_events.return_value = [sample_event]
        
        response = client.get("/events.json?date=tomorrow")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @patch("app.services.events_service.events_service.get_events")
    async def test_get_events_json_with_offset(self, mock_get_events, client, sample_event):
        """Should handle offset parameter"""
        mock_get_events.return_value = [sample_event]
        
        response = client.get("/events.json?offset=7")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["metadata"]["startDate"]
        assert data["metadata"]["endDate"]
    
    @patch("app.services.events_service.events_service.get_events")
    async def test_get_events_json_with_fields_filter(self, mock_get_events, client, sample_event):
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
    async def test_get_events_json_with_title_filter(self, mock_get_events, client, sample_event):
        """Should apply title filter"""
        mock_get_events.return_value = [sample_event]
        
        response = client.get("/events.json?filterTitle=Team")
        
        assert response.status_code == 200
        # The filtering happens in the service, so we just verify it's called
        mock_get_events.assert_called_once()
    
    @patch("app.services.events_service.events_service.get_events")
    async def test_get_events_json_with_multiple_filters(self, mock_get_events, client, sample_event):
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
    
    @patch("app.services.events_service.events_service.get_events")
    async def test_get_events_json_description_modes(self, mock_get_events, client, sample_event):
        """Should handle different description modes"""
        mock_get_events.return_value = [sample_event]
        
        # Test clean mode
        response = client.get("/events.json?descriptionMode=clean")
        assert response.status_code == 200
        
        # Test none mode
        response = client.get("/events.json?descriptionMode=none")
        assert response.status_code == 200
        data = response.json()
        assert data["events"][0]["description"] == ""
    
    @patch("app.services.events_service.events_service.get_events")
    async def test_get_events_json_description_length(self, mock_get_events, client, sample_event):
        """Should truncate description to max length"""
        sample_event["description"] = "A" * 1000
        mock_get_events.return_value = [sample_event]
        
        response = client.get("/events.json?descriptionLength=50")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["events"][0]["description"]) <= 53  # 50 + "..."
    
    def test_get_events_json_invalid_offset(self, client):
        """Should reject invalid offset values"""
        response = client.get("/events.json?offset=0")
        assert response.status_code == 422  # Validation error
        
        response = client.get("/events.json?offset=400")
        assert response.status_code == 422  # Exceeds max


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
    async def test_get_events_tana_custom_tag(self, mock_get_events, client, sample_event):
        """Should use custom tag"""
        mock_get_events.return_value = [sample_event]
        
        response = client.get("/events.tana?tag=work")
        
        assert response.status_code == 200
        content = response.text
        assert "#[[work]]" in content
        assert "#[[meeting]]" not in content
    
    @patch("app.services.events_service.events_service.get_events")
    async def test_get_events_tana_category_tags(self, mock_get_events, client, sample_event):
        """Should use category tags when enabled"""
        mock_get_events.return_value = [sample_event]
        
        response = client.get("/events.tana?includeCategoryTags=true")
        
        assert response.status_code == 200
        content = response.text
        assert "#[[Work]]" in content
        assert "#[[Important]]" in content
    
    @patch("app.services.events_service.events_service.get_events")
    async def test_get_events_tana_field_tags(self, mock_get_events, client, sample_event):
        """Should apply field tags"""
        mock_get_events.return_value = [sample_event]
        
        response = client.get("/events.tana?fieldTags=attendees:co-worker,location:office")
        
        assert response.status_code == 200
        content = response.text
        # Field tags should be applied to attendees
        assert "#co-worker" in content or "#office" in content
    
    @patch("app.services.events_service.events_service.get_events")
    async def test_get_events_tana_show_empty_false(self, mock_get_events, client, sample_event):
        """Should hide empty fields when showEmpty is false"""
        sample_event["location"] = ""
        mock_get_events.return_value = [sample_event]
        
        response = client.get("/events.tana?showEmpty=false")
        
        assert response.status_code == 200
        content = response.text
        # Empty location should not appear when showEmpty is false
        assert "Location::" not in content
    
    @patch("app.services.events_service.events_service.get_events")
    async def test_get_events_tana_fields_filter(self, mock_get_events, client, sample_event):
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
    async def test_get_events_tana_multiple_events(self, mock_get_events, client, sample_event):
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


@pytest.mark.integration
class TestEventsEndpointErrors:
    """Tests for error handling in events endpoint"""
    
    def test_invalid_format(self, client):
        """Should reject invalid format"""
        response = client.get("/events.xml")
        # FastAPI returns 422 for path parameter validation errors
        assert response.status_code == 422
    
    def test_invalid_date_keyword(self, client):
        """Should reject invalid date keyword"""
        # The parse_relative_date ValueError is now caught in the try block
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
    
    def test_description_length_out_of_range(self, client):
        """Should reject description length out of valid range"""
        response = client.get("/events.json?descriptionLength=0")
        assert response.status_code == 422
        
        response = client.get("/events.json?descriptionLength=10000")
        assert response.status_code == 422
    
    @patch("app.services.events_service.events_service.get_events")
    async def test_value_error_from_service(self, mock_get_events, client):
        """Should return 400 for ValueError from service"""
        mock_get_events.side_effect = ValueError("Invalid filter")
        
        response = client.get("/events.json")
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid filter" in data["detail"]


@pytest.mark.integration
class TestEventsEndpointQueryParameters:
    """Tests for query parameter parsing and validation"""
    
    @patch("app.services.events_service.events_service.get_events")
    async def test_filter_attendee_comma_separated(self, mock_get_events, client, sample_event):
        """Should parse comma-separated attendee filter"""
        mock_get_events.return_value = [sample_event]
        
        response = client.get("/events.json?filterAttendee=john,jane")
        
        assert response.status_code == 200
        # Verify the service was called with split attendees
        call_args = mock_get_events.call_args
        assert call_args[1]["filter_attendee"] == ["john", "jane"]
    
    @patch("app.services.events_service.events_service.get_events")
    async def test_filter_status_comma_separated(self, mock_get_events, client, sample_event):
        """Should parse comma-separated status filter"""
        mock_get_events.return_value = [sample_event]
        
        response = client.get("/events.json?filterStatus=Accepted,Tentative")
        
        assert response.status_code == 200
        call_args = mock_get_events.call_args
        assert call_args[1]["filter_status"] == ["Accepted", "Tentative"]
    
    @patch("app.services.events_service.events_service.get_events")
    async def test_filter_categories_comma_separated(self, mock_get_events, client, sample_event):
        """Should parse comma-separated categories filter"""
        mock_get_events.return_value = [sample_event]
        
        response = client.get("/events.json?filterCategories=Work,Personal")
        
        assert response.status_code == 200
        call_args = mock_get_events.call_args
        assert call_args[1]["filter_categories"] == ["Work", "Personal"]
    
    @patch("app.services.events_service.events_service.get_events")
    async def test_include_all_day_boolean(self, mock_get_events, client, sample_event):
        """Should parse boolean includeAllDay parameter"""
        mock_get_events.return_value = [sample_event]
        
        response = client.get("/events.json?includeAllDay=true")
        assert response.status_code == 200
        
        response = client.get("/events.json?includeAllDay=false")
        assert response.status_code == 200
    
    @patch("app.services.events_service.events_service.get_events")
    async def test_calendar_filter(self, mock_get_events, client, sample_event):
        """Should pass calendar filter to service"""
        mock_get_events.return_value = [sample_event]
        
        response = client.get("/events.json?calendar=Work%20Calendar")
        
        assert response.status_code == 200
        call_args = mock_get_events.call_args
        assert call_args[1]["filter_calendar"] == "Work Calendar"

