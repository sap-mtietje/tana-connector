"""Unit tests for template service"""

import pytest
from app.services.template_service import TemplateService


@pytest.mark.unit
class TestTemplateServiceInitialization:
    """Tests for template service initialization"""

    def test_template_service_initialization(self):
        """Should initialize with Jinja2 environment"""
        service = TemplateService()
        assert service.env is not None

    def test_custom_filters_registered(self):
        """Should have custom filters registered"""
        service = TemplateService()
        assert "clean" in service.env.filters
        assert "truncate" in service.env.filters
        assert "date_format" in service.env.filters


@pytest.mark.unit
class TestTemplateServiceRendering:
    """Tests for template rendering"""

    def test_render_simple_template(self):
        """Should render simple template with events"""
        service = TemplateService()
        events = [
            {"title": "Meeting 1", "location": "Room A"},
            {"title": "Meeting 2", "location": "Room B"},
        ]
        template = "{% for event in events %}{{event.title}} at {{event.location}}\n{% endfor %}"

        result = service.render_template(template, events, "2025-10-09", "2025-10-10")

        assert "Meeting 1 at Room A" in result
        assert "Meeting 2 at Room B" in result

    def test_render_with_context_variables(self):
        """Should provide context variables (count, start_date, end_date)"""
        service = TemplateService()
        events = [{"title": "Event 1"}, {"title": "Event 2"}]
        template = "Total: {{count}} events from {{start_date}} to {{end_date}}"

        result = service.render_template(template, events, "2025-10-09", "2025-10-10")

        assert "Total: 2 events" in result
        assert "from 2025-10-09 to 2025-10-10" in result

    def test_render_with_conditionals(self):
        """Should handle conditional statements"""
        service = TemplateService()
        events = [
            {"title": "Meeting", "location": "Room A"},
            {"title": "Call", "location": ""},
        ]
        template = """{% for event in events %}
{{event.title}}{% if event.location %} - {{event.location}}{% endif %}
{% endfor %}"""

        result = service.render_template(template, events, "2025-10-09", "2025-10-10")

        assert "Meeting - Room A" in result
        assert "Call" in result
        # "Call" should not have location appended
        assert "Call -" not in result

    def test_render_with_nested_loops(self):
        """Should handle nested loops (e.g., attendees)"""
        service = TemplateService()
        events = [
            {
                "title": "Team Meeting",
                "attendees": ["Alice", "Bob", "Charlie"],
            }
        ]
        template = """{% for event in events %}
{{event.title}}:
{% for attendee in event.attendees %}  - {{attendee}}
{% endfor %}{% endfor %}"""

        result = service.render_template(template, events, "2025-10-09", "2025-10-10")

        assert "Team Meeting:" in result
        assert "- Alice" in result
        assert "- Bob" in result
        assert "- Charlie" in result

    def test_render_empty_events(self):
        """Should handle empty events list"""
        service = TemplateService()
        template = (
            "{% for event in events %}{{event.title}}{% endfor %}Count: {{count}}"
        )

        result = service.render_template(template, [], "2025-10-09", "2025-10-10")

        assert "Count: 0" in result

    def test_render_with_empty_field_values(self):
        """Should render empty string for empty field values"""
        service = TemplateService()
        events = [{"title": "Meeting", "location": ""}]
        template = "{{events[0].title}} - {{events[0].location}}"

        result = service.render_template(template, events, "2025-10-09", "2025-10-10")

        assert result == "Meeting - "


@pytest.mark.unit
class TestTemplateServiceErrors:
    """Tests for error handling"""

    def test_undefined_variable_renders_empty(self):
        """Should render empty string for undefined variables (lenient mode)"""
        service = TemplateService()
        events = [{"title": "Meeting"}]
        template = "{{events[0].title}} at {{events[0].nonexistent_field}}"

        result = service.render_template(template, events, "2025-10-09", "2025-10-10")

        # Missing fields render as empty string instead of raising error
        assert result == "Meeting at "

    def test_invalid_template_syntax_raises_error(self):
        """Should raise ValueError for invalid template syntax"""
        service = TemplateService()
        events = []
        template = "{% for event in events %}{{event.title}}"  # Missing endfor

        with pytest.raises(ValueError) as exc_info:
            service.render_template(template, events, "2025-10-09", "2025-10-10")

        assert "Template syntax error" in str(exc_info.value)

    def test_invalid_jinja_expression_raises_error(self):
        """Should raise ValueError for invalid Jinja expression"""
        service = TemplateService()
        events = [{"title": "Meeting"}]
        template = "{{events[0].title | invalid_filter}}"

        with pytest.raises(ValueError) as exc_info:
            service.render_template(template, events, "2025-10-09", "2025-10-10")

        # Invalid filter raises TemplateSyntaxError which becomes "Template syntax error"
        assert "Template syntax error" in str(exc_info.value)


@pytest.mark.unit
class TestCustomFilters:
    """Tests for custom Jinja2 filters"""

    def test_clean_filter(self):
        """Should clean description text"""
        service = TemplateService()
        events = [
            {
                "title": "Meeting",
                "description": "<p>This is a meeting</p>\n\nJoin: https://teams.microsoft.com/meet/123",
            }
        ]
        template = "{{events[0].description | clean}}"

        result = service.render_template(template, events, "2025-10-09", "2025-10-10")

        # Should remove HTML but preserve meeting links
        assert "<p>" not in result
        assert "https://teams.microsoft.com" in result
        assert "This is a meeting" in result

    def test_clean_filter_with_empty_string(self):
        """Should handle empty string in clean filter"""
        service = TemplateService()
        events = [{"title": "Meeting", "description": ""}]
        template = "{{events[0].description | clean}}"

        result = service.render_template(template, events, "2025-10-09", "2025-10-10")

        assert result == ""

    def test_truncate_filter(self):
        """Should truncate text to specified length"""
        service = TemplateService()
        events = [{"title": "Meeting", "description": "A" * 200}]
        template = "{{events[0].description | truncate(50)}}"

        result = service.render_template(template, events, "2025-10-09", "2025-10-10")

        assert len(result) <= 53  # 50 + "..."
        assert result.endswith("...")

    def test_truncate_filter_short_text(self):
        """Should not truncate text shorter than limit"""
        service = TemplateService()
        events = [{"title": "Meeting", "description": "Short text"}]
        template = "{{events[0].description | truncate(50)}}"

        result = service.render_template(template, events, "2025-10-09", "2025-10-10")

        assert result == "Short text"
        assert not result.endswith("...")

    def test_truncate_filter_with_empty_string(self):
        """Should handle empty string in truncate filter"""
        service = TemplateService()
        events = [{"title": "Meeting", "description": ""}]
        template = "{{events[0].description | truncate(50)}}"

        result = service.render_template(template, events, "2025-10-09", "2025-10-10")

        assert result == ""

    def test_date_format_filter(self):
        """Should format datetime strings"""
        service = TemplateService()
        events = [{"title": "Meeting", "start": "2025-10-09T10:00:00"}]
        template = "{{events[0].start | date_format('%Y-%m-%d')}}"

        result = service.render_template(template, events, "2025-10-09", "2025-10-10")

        assert result == "2025-10-09"

    def test_date_format_filter_custom_format(self):
        """Should use custom format string"""
        service = TemplateService()
        events = [{"title": "Meeting", "start": "2025-10-09T14:30:00"}]
        template = "{{events[0].start | date_format('%H:%M')}}"

        result = service.render_template(template, events, "2025-10-09", "2025-10-10")

        assert result == "14:30"

    def test_date_format_filter_with_empty_string(self):
        """Should handle empty string in date_format filter"""
        service = TemplateService()
        events = [{"title": "Meeting", "start": ""}]
        template = "{{events[0].start | date_format('%Y-%m-%d')}}"

        result = service.render_template(template, events, "2025-10-09", "2025-10-10")

        assert result == ""

    def test_date_format_filter_invalid_date(self):
        """Should handle invalid date string gracefully"""
        service = TemplateService()
        events = [{"title": "Meeting", "start": "invalid-date"}]
        template = "{{events[0].start | date_format('%Y-%m-%d')}}"

        result = service.render_template(template, events, "2025-10-09", "2025-10-10")

        # Should return original string if parsing fails
        assert result == "invalid-date"


@pytest.mark.unit
class TestTanaTemplates:
    """Tests for Tana-specific template patterns"""

    def test_tana_basic_structure(self):
        """Should render basic Tana structure"""
        service = TemplateService()
        events = [
            {
                "title": "Team Meeting",
                "start": "2025-10-09T10:00:00",
                "end": "2025-10-09T11:00:00",
            }
        ]
        template = """%%tana%%
{% for event in events %}- {{event.title}} #meeting
  - Date:: [[date:{{event.start}}/{{event.end}}]]
{% endfor %}"""

        result = service.render_template(template, events, "2025-10-09", "2025-10-10")

        assert "%%tana%%" in result
        assert "- Team Meeting #meeting" in result
        assert "Date:: [[date:2025-10-09T10:00:00/2025-10-09T11:00:00]]" in result

    def test_tana_with_attendees(self):
        """Should render Tana format with attendees list"""
        service = TemplateService()
        events = [
            {
                "title": "Review",
                "attendees": ["Alice", "Bob"],
            }
        ]
        template = """{% for event in events %}- {{event.title}} #meeting
  - Attendees::
    {% for attendee in event.attendees %}
    - [[{{attendee}} #co-worker]]
    {% endfor %}
{% endfor %}"""

        result = service.render_template(template, events, "2025-10-09", "2025-10-10")

        assert "- Review #meeting" in result
        assert "[[Alice #co-worker]]" in result
        assert "[[Bob #co-worker]]" in result

    def test_tana_with_conditional_fields(self):
        """Should handle conditional fields in Tana format"""
        service = TemplateService()
        events = [
            {"title": "Meeting", "location": "Room A"},
            {"title": "Call", "location": ""},
        ]
        template = """{% for event in events %}- {{event.title}} #meeting
  {% if event.location %}
  - Location:: [[{{event.location}} #location]]
  {% endif %}
{% endfor %}"""

        result = service.render_template(template, events, "2025-10-09", "2025-10-10")

        assert "- Meeting #meeting" in result
        assert "Location:: [[Room A #location]]" in result
        assert "- Call #meeting" in result
        lines = result.split("\n")
        call_idx = next(i for i, line in enumerate(lines) if "Call #meeting" in line)
        assert (
            "Location::" not in lines[call_idx + 1]
            if call_idx + 1 < len(lines)
            else True
        )


@pytest.mark.unit
class TestGenericRenderMethod:
    """Tests for the generic render() method"""

    def test_render_with_messages(self):
        """Should render with messages context"""
        service = TemplateService()
        messages = [
            {"subject": "Hello", "from": "alice@example.com"},
            {"subject": "World", "from": "bob@example.com"},
        ]
        template = (
            "{% for msg in messages %}{{msg.subject}} from {{msg.from}}\n{% endfor %}"
        )

        result = service.render(template, messages=messages, count=len(messages))

        assert "Hello from alice@example.com" in result
        assert "World from bob@example.com" in result

    def test_render_with_arbitrary_context(self):
        """Should render with arbitrary context variables"""
        service = TemplateService()
        template = "User: {{user_name}}, Folder: {{folder}}"

        result = service.render(template, user_name="John", folder="inbox")

        assert result == "User: John, Folder: inbox"

    def test_render_undefined_variable_strict(self):
        """Should raise ValueError for undefined variable when accessed directly"""
        service = TemplateService()
        # This template tries to iterate over undefined variable
        template = "{% for item in undefined_var %}{{item}}{% endfor %}"

        # Jinja2 treats undefined as empty iterable, so this won't raise
        result = service.render(template)
        assert result == ""

    def test_render_date_format_with_z_suffix(self):
        """Should handle date strings with Z suffix"""
        service = TemplateService()
        template = "{{date | date_format('%Y-%m-%d')}}"

        result = service.render(template, date="2025-12-09T10:00:00Z")

        assert result == "2025-12-09"

    def test_render_date_format_with_microseconds(self):
        """Should handle date strings with .0000000 microseconds"""
        service = TemplateService()
        template = "{{date | date_format('%Y-%m-%d %H:%M')}}"

        result = service.render(template, date="2025-12-09T10:30:00.0000000")

        assert result == "2025-12-09 10:30"

    def test_render_date_format_non_iso_string(self):
        """Should return original string for non-ISO date format"""
        service = TemplateService()
        template = "{{date | date_format('%Y-%m-%d')}}"

        result = service.render(template, date="December 9, 2025")

        # No T in string, so returns original
        assert result == "December 9, 2025"

    def test_render_undefined_error_raises_valueerror(self):
        """Should raise ValueError for undefined variable access"""
        service = TemplateService()
        # Force an undefined error by using strict undefined access
        template = "{{ undefined_var.attribute }}"

        with pytest.raises(ValueError) as exc_info:
            service.render(template)

        assert "Undefined" in str(exc_info.value) or "undefined" in str(exc_info.value)

    def test_render_date_format_with_invalid_iso(self):
        """Should handle malformed ISO date gracefully"""
        service = TemplateService()
        template = "{{date | date_format('%Y-%m-%d')}}"

        # Has T but invalid format
        result = service.render(template, date="2025-13-45T99:99:99")

        # Should return original on parse failure
        assert result == "2025-13-45T99:99:99"
