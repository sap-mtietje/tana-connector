"""Integration tests for POST /events endpoint with templates"""

import pytest
from unittest.mock import patch


@pytest.mark.integration
class TestEventsPostEndpoint:
    """Tests for POST /events with templates"""

    @patch("app.services.events_service.events_service.get_events")
    async def test_post_simple_template(self, mock_get_events, client, sample_event):
        """Should render simple template with events"""
        mock_get_events.return_value = [sample_event]
        template = "{{events[0].title}} at {{events[0].location}}"

        response = client.post(
            "/events", content=template, headers={"Content-Type": "text/plain"}
        )

        assert response.status_code == 200
        assert "Team Meeting at Conference Room A" in response.text

    @patch("app.services.events_service.events_service.get_events")
    async def test_post_template_with_loop(self, mock_get_events, client, sample_event):
        """Should render template with loops"""
        event2 = sample_event.copy()
        event2["title"] = "Code Review"
        event2["location"] = "Room B"
        mock_get_events.return_value = [sample_event, event2]

        template = """{% for event in events %}{{event.title}} - {{event.location}}
{% endfor %}"""

        response = client.post(
            "/events", content=template, headers={"Content-Type": "text/plain"}
        )

        assert response.status_code == 200
        assert "Team Meeting - Conference Room A" in response.text
        assert "Code Review - Room B" in response.text

    @patch("app.services.events_service.events_service.get_events")
    async def test_post_tana_template(self, mock_get_events, client, sample_event):
        """Should render Tana format template"""
        mock_get_events.return_value = [sample_event]
        template = """%%tana%%
{% for event in events %}- {{event.title}} #meeting
  - Date:: [[date:{{event.start}}/{{event.end}}]]
  - Location:: [[{{event.location}} #location]]
{% endfor %}"""

        response = client.post(
            "/events", content=template, headers={"Content-Type": "text/plain"}
        )

        assert response.status_code == 200
        assert "%%tana%%" in response.text
        assert "- Team Meeting #meeting" in response.text
        assert "Date::" in response.text
        assert "Location:: [[Conference Room A #location]]" in response.text

    @patch("app.services.events_service.events_service.get_events")
    async def test_post_template_with_attendees_loop(
        self, mock_get_events, client, sample_event
    ):
        """Should render nested loops (attendees)"""
        mock_get_events.return_value = [sample_event]
        template = """{% for event in events %}{{event.title}}:
{% for attendee in event.attendees %}  - {{attendee}}
{% endfor %}{% endfor %}"""

        response = client.post(
            "/events", content=template, headers={"Content-Type": "text/plain"}
        )

        assert response.status_code == 200
        assert "Team Meeting:" in response.text
        assert "- John Doe" in response.text
        assert "- jane@example.com" in response.text

    @patch("app.services.events_service.events_service.get_events")
    async def test_post_template_with_conditionals(
        self, mock_get_events, client, sample_event
    ):
        """Should handle conditional statements"""
        event_no_location = sample_event.copy()
        event_no_location["location"] = ""
        event_no_location["title"] = "Phone Call"
        mock_get_events.return_value = [sample_event, event_no_location]

        template = """{% for event in events %}{{event.title}}{% if event.location %} at {{event.location}}{% endif %}
{% endfor %}"""

        response = client.post(
            "/events", content=template, headers={"Content-Type": "text/plain"}
        )

        assert response.status_code == 200
        assert "Team Meeting at Conference Room A" in response.text
        assert "Phone Call" in response.text
        # Phone Call should not have " at " appended
        assert "Phone Call at" not in response.text

    @patch("app.services.events_service.events_service.get_events")
    async def test_post_template_with_context_variables(
        self, mock_get_events, client, sample_event
    ):
        """Should provide count, start_date, end_date in context"""
        mock_get_events.return_value = [sample_event, sample_event.copy()]
        template = "Found {{count}} events from {{start_date}} to {{end_date}}"

        response = client.post(
            "/events?date=tomorrow&offset=7",
            content=template,
            headers={"Content-Type": "text/plain"},
        )

        assert response.status_code == 200
        assert "Found 2 events from" in response.text

    @patch("app.services.events_service.events_service.get_events")
    async def test_post_template_with_query_parameters(
        self, mock_get_events, client, sample_event
    ):
        """Should apply query parameter filters"""
        mock_get_events.return_value = [sample_event]
        template = "{{events[0].title}}"

        response = client.post(
            "/events?date=tomorrow&offset=3&filterTitle=Meeting&includeAllDay=false",
            content=template,
            headers={"Content-Type": "text/plain"},
        )

        assert response.status_code == 200
        # Verify the service was called with correct filters
        call_args = mock_get_events.call_args
        assert call_args[1]["filter_title"] == ["Meeting"]
        assert call_args[1]["filter_all_day"] is False

    @patch("app.services.events_service.events_service.get_events")
    async def test_post_template_with_description_mode(
        self, mock_get_events, client, sample_event
    ):
        """Should process description according to descriptionMode"""
        sample_event["description"] = "<p>Meeting notes</p>"
        mock_get_events.return_value = [sample_event]
        template = "{{events[0].description}}"

        response = client.post(
            "/events?descriptionMode=clean",
            content=template,
            headers={"Content-Type": "text/plain"},
        )

        assert response.status_code == 200
        # HTML should be cleaned
        assert "<p>" not in response.text
        assert "Meeting notes" in response.text

    @patch("app.services.events_service.events_service.get_events")
    async def test_post_template_with_custom_filter_clean(
        self, mock_get_events, client, sample_event
    ):
        """Should use custom clean filter"""
        sample_event["description"] = (
            "<p>Test</p> https://teams.microsoft.com/meeting/123"
        )
        mock_get_events.return_value = [sample_event]
        template = "{{events[0].description | clean}}"

        response = client.post(
            "/events", content=template, headers={"Content-Type": "text/plain"}
        )

        assert response.status_code == 200
        assert "<p>" not in response.text
        assert "https://teams.microsoft.com" not in response.text
        assert "Test" in response.text

    @patch("app.services.events_service.events_service.get_events")
    async def test_post_template_with_custom_filter_truncate(
        self, mock_get_events, client, sample_event
    ):
        """Should use custom truncate filter"""
        sample_event["description"] = "A" * 200
        mock_get_events.return_value = [sample_event]
        template = "{{events[0].description | truncate(50)}}"

        response = client.post(
            "/events", content=template, headers={"Content-Type": "text/plain"}
        )

        assert response.status_code == 200
        assert len(response.text) <= 53  # 50 + "..."
        assert response.text.endswith("...")

    @patch("app.services.events_service.events_service.get_events")
    async def test_post_template_with_custom_filter_date_format(
        self, mock_get_events, client, sample_event
    ):
        """Should use custom date_format filter"""
        mock_get_events.return_value = [sample_event]
        template = "{{events[0].start | date_format('%Y-%m-%d')}}"

        response = client.post(
            "/events", content=template, headers={"Content-Type": "text/plain"}
        )

        assert response.status_code == 200
        assert "2025-10-05" in response.text

    @patch("app.services.events_service.events_service.get_events")
    async def test_post_template_with_empty_events(self, mock_get_events, client):
        """Should handle empty events list"""
        mock_get_events.return_value = []
        template = (
            "{% for event in events %}{{event.title}}{% endfor %}Count: {{count}}"
        )

        response = client.post(
            "/events", content=template, headers={"Content-Type": "text/plain"}
        )

        assert response.status_code == 200
        assert "Count: 0" in response.text

    @patch("app.services.events_service.events_service.get_events")
    async def test_post_undefined_variable_error(
        self, mock_get_events, client, sample_event
    ):
        """Should return 400 for undefined template variables"""
        mock_get_events.return_value = [sample_event]
        template = "{{events[0].nonexistent_field}}"

        response = client.post(
            "/events", content=template, headers={"Content-Type": "text/plain"}
        )

        assert response.status_code == 400
        data = response.json()
        assert "Undefined variable" in data["detail"]

    @patch("app.services.events_service.events_service.get_events")
    async def test_post_template_syntax_error(self, mock_get_events, client):
        """Should return 400 for invalid template syntax"""
        mock_get_events.return_value = []
        template = "{% for event in events %}{{event.title}}"  # Missing endfor

        response = client.post(
            "/events", content=template, headers={"Content-Type": "text/plain"}
        )

        assert response.status_code == 400
        data = response.json()
        assert "Template syntax error" in data["detail"]

    def test_post_empty_template_body(self, client):
        """Should return 422 for empty template body (validation error)"""
        response = client.post(
            "/events", content="", headers={"Content-Type": "text/plain"}
        )

        # FastAPI returns 422 for required field validation
        assert response.status_code == 422

    def test_post_whitespace_only_template(self, client):
        """Should return 400 for whitespace-only template"""
        response = client.post(
            "/events", content="   \n  \n  ", headers={"Content-Type": "text/plain"}
        )

        assert response.status_code == 400
        data = response.json()
        assert "Template body is required" in data["detail"]

    def test_post_invalid_date_keyword(self, client):
        """Should return 400 for invalid date keyword"""
        template = "{{count}} events"
        response = client.post(
            "/events?date=invalid-keyword",
            content=template,
            headers={"Content-Type": "text/plain"},
        )

        assert response.status_code == 400
        data = response.json()
        assert "Invalid date format" in data["detail"]

    @patch("app.services.events_service.events_service.get_events")
    async def test_post_service_exception(self, mock_get_events, client):
        """Should handle service exceptions gracefully"""
        mock_get_events.side_effect = Exception("Service error")
        template = "{{count}} events"

        response = client.post(
            "/events", content=template, headers={"Content-Type": "text/plain"}
        )

        assert response.status_code == 500
        data = response.json()
        assert "Failed to render template" in data["detail"]
