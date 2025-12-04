"""Unit tests for OData filter building logic"""

from app.models.filters import (
    build_odata_filter,
    Importance,
    Sensitivity,
    ShowAs,
    ResponseStatus,
)


class TestBuildOdataFilter:
    """Tests for build_odata_filter function"""

    def test_returns_none_when_no_filters(self):
        """Test returns None when no filters provided"""
        result = build_odata_filter()
        assert result is None

    def test_importance_filter(self):
        """Test importance filter generates correct OData"""
        result = build_odata_filter(importance=Importance.high)
        assert result == "importance eq 'high'"

    def test_sensitivity_filter(self):
        """Test sensitivity filter generates correct OData"""
        result = build_odata_filter(sensitivity=Sensitivity.private)
        assert result == "sensitivity eq 'private'"

    def test_show_as_filter(self):
        """Test showAs filter generates correct OData"""
        result = build_odata_filter(show_as=ShowAs.busy)
        assert result == "showAs eq 'busy'"

    def test_response_status_filter(self):
        """Test responseStatus filter generates correct OData"""
        result = build_odata_filter(response_status=ResponseStatus.accepted)
        assert result == "responseStatus/response eq 'accepted'"

    def test_is_all_day_true(self):
        """Test isAllDay=true filter"""
        result = build_odata_filter(is_all_day=True)
        assert result == "isAllDay eq true"

    def test_is_all_day_false(self):
        """Test isAllDay=false filter"""
        result = build_odata_filter(is_all_day=False)
        assert result == "isAllDay eq false"

    def test_is_online_meeting_filter(self):
        """Test isOnlineMeeting filter"""
        result = build_odata_filter(is_online_meeting=True)
        assert result == "isOnlineMeeting eq true"

    def test_is_cancelled_filter(self):
        """Test isCancelled filter"""
        result = build_odata_filter(is_cancelled=True)
        assert result == "isCancelled eq true"

    def test_has_attachments_filter(self):
        """Test hasAttachments filter"""
        result = build_odata_filter(has_attachments=True)
        assert result == "hasAttachments eq true"

    def test_single_category_filter(self):
        """Test single category generates correct OData"""
        result = build_odata_filter(categories=["Work"])
        assert result == "(categories/any(c:c eq 'Work'))"

    def test_multiple_categories_filter(self):
        """Test multiple categories are OR'd together"""
        result = build_odata_filter(categories=["Work", "Personal"])
        assert (
            "(categories/any(c:c eq 'Work') or categories/any(c:c eq 'Personal'))"
            in result
        )

    def test_base_filter_wrapped_in_parentheses(self):
        """Test base OData filter is wrapped in parentheses"""
        result = build_odata_filter(base_filter="contains(subject,'meeting')")
        assert result == "(contains(subject,'meeting'))"

    def test_multiple_filters_combined_with_and(self):
        """Test multiple filters are AND'd together"""
        result = build_odata_filter(
            importance=Importance.high,
            show_as=ShowAs.busy,
            is_online_meeting=True,
        )

        assert "importance eq 'high'" in result
        assert "showAs eq 'busy'" in result
        assert "isOnlineMeeting eq true" in result
        assert result.count(" and ") == 2

    def test_base_filter_combined_with_friendly_filters(self):
        """Test base OData filter combined with friendly filters"""
        result = build_odata_filter(
            base_filter="contains(subject,'standup')",
            importance=Importance.high,
        )

        assert "(contains(subject,'standup'))" in result
        assert "importance eq 'high'" in result
        assert " and " in result

    def test_all_filters_combined(self):
        """Test all filter types combined"""
        result = build_odata_filter(
            base_filter="contains(subject,'test')",
            importance=Importance.high,
            sensitivity=Sensitivity.normal,
            show_as=ShowAs.busy,
            is_all_day=False,
            is_cancelled=False,
            is_online_meeting=True,
            has_attachments=False,
            response_status=ResponseStatus.accepted,
            categories=["Work"],
        )

        # All conditions should be present
        assert "(contains(subject,'test'))" in result
        assert "importance eq 'high'" in result
        assert "sensitivity eq 'normal'" in result
        assert "showAs eq 'busy'" in result
        assert "isAllDay eq false" in result
        assert "isCancelled eq false" in result
        assert "isOnlineMeeting eq true" in result
        assert "hasAttachments eq false" in result
        assert "responseStatus/response eq 'accepted'" in result
        assert "categories/any(c:c eq 'Work')" in result

        # Should have 9 " and " connectors (10 conditions)
        assert result.count(" and ") == 9


class TestFilterEnums:
    """Tests for filter enum values"""

    def test_importance_enum_values(self):
        """Test Importance enum has correct values"""
        assert Importance.low.value == "low"
        assert Importance.normal.value == "normal"
        assert Importance.high.value == "high"

    def test_sensitivity_enum_values(self):
        """Test Sensitivity enum has correct values"""
        assert Sensitivity.normal.value == "normal"
        assert Sensitivity.personal.value == "personal"
        assert Sensitivity.private.value == "private"
        assert Sensitivity.confidential.value == "confidential"

    def test_show_as_enum_values(self):
        """Test ShowAs enum has correct values"""
        assert ShowAs.free.value == "free"
        assert ShowAs.tentative.value == "tentative"
        assert ShowAs.busy.value == "busy"
        assert ShowAs.oof.value == "oof"
        assert ShowAs.workingElsewhere.value == "workingElsewhere"
        assert ShowAs.unknown.value == "unknown"

    def test_response_status_enum_values(self):
        """Test ResponseStatus enum has correct values"""
        assert ResponseStatus.none.value == "none"
        assert ResponseStatus.organizer.value == "organizer"
        assert ResponseStatus.tentativelyAccepted.value == "tentativelyAccepted"
        assert ResponseStatus.accepted.value == "accepted"
        assert ResponseStatus.declined.value == "declined"
        assert ResponseStatus.notResponded.value == "notResponded"
