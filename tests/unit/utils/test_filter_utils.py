"""Unit tests for filter_utils module"""

import pytest
from app.utils.filter_utils import (
    get_nested_value,
    matches_filter,
    parse_filter_expression,
    apply_filter,
)


@pytest.mark.unit
class TestGetNestedValue:
    """Tests for get_nested_value function"""

    def test_simple_key(self):
        """Should get top-level key"""
        obj = {"subject": "Test"}
        assert get_nested_value(obj, "subject") == "Test"

    def test_nested_key(self):
        """Should get nested key with dot notation"""
        obj = {"from": {"emailAddress": {"name": "John"}}}
        assert get_nested_value(obj, "from.emailAddress.name") == "John"

    def test_missing_key_returns_none(self):
        """Should return None for missing key"""
        obj = {"subject": "Test"}
        assert get_nested_value(obj, "missing") is None

    def test_missing_nested_key_returns_none(self):
        """Should return None for missing nested key"""
        obj = {"from": {"emailAddress": {}}}
        assert get_nested_value(obj, "from.emailAddress.name") is None

    def test_non_dict_intermediate_returns_none(self):
        """Should return None when intermediate value is not a dict"""
        obj = {"from": "not-a-dict"}
        assert get_nested_value(obj, "from.emailAddress.name") is None

    def test_deeply_nested(self):
        """Should handle deeply nested paths"""
        obj = {"a": {"b": {"c": {"d": "value"}}}}
        assert get_nested_value(obj, "a.b.c.d") == "value"


@pytest.mark.unit
class TestMatchesFilter:
    """Tests for matches_filter function"""

    # Equality operator tests
    def test_eq_string_match(self):
        """Should match equal strings (case-insensitive)"""
        item = {"importance": "high"}
        assert matches_filter(item, "importance", "eq", "high") is True
        assert matches_filter(item, "importance", "eq", "HIGH") is True

    def test_eq_string_no_match(self):
        """Should not match different strings"""
        item = {"importance": "high"}
        assert matches_filter(item, "importance", "eq", "low") is False

    def test_eq_list_contains(self):
        """Should match if value is in list"""
        item = {"categories": ["Work", "Important"]}
        assert matches_filter(item, "categories", "eq", "Work") is True
        assert matches_filter(item, "categories", "eq", "Personal") is False

    # Not equals operator tests
    def test_ne_string_match(self):
        """Should match when strings are different"""
        item = {"importance": "high"}
        assert matches_filter(item, "importance", "ne", "low") is True
        assert matches_filter(item, "importance", "ne", "high") is False

    def test_ne_list_not_contains(self):
        """Should match if value is not in list"""
        item = {"categories": ["Work"]}
        assert matches_filter(item, "categories", "ne", "Personal") is True
        assert matches_filter(item, "categories", "ne", "Work") is False

    def test_ne_none_value(self):
        """Should return True for ne when field is None"""
        item = {"subject": "Test"}
        assert matches_filter(item, "missing", "ne", "anything") is True

    # Contains operator tests
    def test_contains_string(self):
        """Should match substring (case-insensitive)"""
        item = {"subject": "Important Meeting"}
        assert matches_filter(item, "subject", "contains", "meeting") is True
        assert matches_filter(item, "subject", "contains", "lunch") is False

    def test_contains_list(self):
        """Should match if any list item contains value"""
        item = {"categories": ["Work-Related", "Important"]}
        assert matches_filter(item, "categories", "contains", "work") is True
        assert matches_filter(item, "categories", "contains", "personal") is False

    # Startswith operator tests
    def test_startswith(self):
        """Should match string prefix (case-insensitive)"""
        item = {"subject": "RE: Meeting"}
        assert matches_filter(item, "subject", "startswith", "re:") is True
        assert matches_filter(item, "subject", "startswith", "fw:") is False

    # Endswith operator tests
    def test_endswith(self):
        """Should match string suffix (case-insensitive)"""
        item = {"from": {"emailAddress": {"address": "john@example.com"}}}
        assert (
            matches_filter(
                item, "from.emailAddress.address", "endswith", "@example.com"
            )
            is True
        )
        assert (
            matches_filter(item, "from.emailAddress.address", "endswith", "@other.com")
            is False
        )

    # Greater than / less than tests
    def test_gt_numeric(self):
        """Should compare numeric values"""
        item = {"size": 100}
        assert matches_filter(item, "size", "gt", "50") is True
        assert matches_filter(item, "size", "gt", "150") is False

    def test_lt_numeric(self):
        """Should compare numeric values"""
        item = {"size": 100}
        assert matches_filter(item, "size", "lt", "150") is True
        assert matches_filter(item, "size", "lt", "50") is False

    def test_gt_string_fallback(self):
        """Should fall back to string comparison for non-numeric values"""
        item = {"receivedDateTime": "2025-10-05T10:00:00"}
        assert matches_filter(item, "receivedDateTime", "gt", "2025-10-01") is True
        assert matches_filter(item, "receivedDateTime", "lt", "2025-10-10") is True

    # Exists operator tests
    def test_exists_true(self):
        """Should match when field exists and has value"""
        item = {"subject": "Test", "categories": ["Work"]}
        assert matches_filter(item, "subject", "exists", "true") is True
        assert matches_filter(item, "categories", "exists", "true") is True

    def test_exists_false_for_missing(self):
        """Should not match exists=true when field is missing"""
        item = {"subject": "Test"}
        assert matches_filter(item, "missing", "exists", "true") is False

    def test_exists_false_for_empty(self):
        """Should not match exists=true when field is empty"""
        item = {"subject": "", "categories": []}
        assert matches_filter(item, "subject", "exists", "true") is False
        assert matches_filter(item, "categories", "exists", "true") is False

    def test_exists_negated(self):
        """Should match exists=false when field is missing or empty"""
        item = {"subject": "Test"}
        assert matches_filter(item, "missing", "exists", "false") is True
        assert matches_filter(item, "subject", "exists", "false") is False

    # None value handling
    def test_none_value_with_eq(self):
        """Should not match eq when field is None"""
        item = {"subject": None}
        assert matches_filter(item, "subject", "eq", "test") is False

    # Unknown operator
    def test_unknown_operator_returns_false(self):
        """Should return False for unknown operators"""
        item = {"subject": "Test"}
        assert matches_filter(item, "subject", "unknown", "test") is False

    # List with unknown operator
    def test_list_unknown_operator_returns_false(self):
        """Should return False for unknown operators on lists"""
        item = {"categories": ["Work"]}
        assert matches_filter(item, "categories", "startswith", "W") is False


@pytest.mark.unit
class TestParseFilterExpression:
    """Tests for parse_filter_expression function"""

    def test_simple_field_value(self):
        """Should parse field:value as eq operator"""
        result = parse_filter_expression("categories:tana")
        assert result == [("categories", "eq", "tana")]

    def test_explicit_operator(self):
        """Should parse field:operator:value"""
        result = parse_filter_expression("isRead:eq:false")
        assert result == [("isRead", "eq", "false")]

    def test_nested_field(self):
        """Should handle nested field paths"""
        result = parse_filter_expression("from.emailAddress.address:contains:@sap.com")
        assert result == [("from.emailAddress.address", "contains", "@sap.com")]

    def test_multiple_conditions(self):
        """Should parse comma-separated conditions"""
        result = parse_filter_expression("categories:tana,isRead:eq:false")
        assert result == [
            ("categories", "eq", "tana"),
            ("isRead", "eq", "false"),
        ]

    def test_value_with_colons(self):
        """Should handle values containing colons"""
        result = parse_filter_expression("webLink:contains:https://example.com")
        assert result == [("webLink", "contains", "https://example.com")]

    def test_empty_expression(self):
        """Should return empty list for empty expression"""
        result = parse_filter_expression("")
        assert result == []

    def test_whitespace_handling(self):
        """Should strip whitespace from parts"""
        result = parse_filter_expression(" categories : eq : tana ")
        assert result == [("categories", "eq", "tana")]

    def test_empty_parts_ignored(self):
        """Should ignore empty parts"""
        result = parse_filter_expression("categories:tana,,isRead:false")
        assert result == [
            ("categories", "eq", "tana"),
            ("isRead", "eq", "false"),
        ]


@pytest.mark.unit
class TestApplyFilter:
    """Tests for apply_filter function"""

    def test_filter_by_category(self):
        """Should filter items by category"""
        items = [
            {"id": "1", "categories": ["Work"]},
            {"id": "2", "categories": ["Personal"]},
            {"id": "3", "categories": ["Work", "Important"]},
        ]
        result = apply_filter(items, "categories:Work")
        assert len(result) == 2
        assert result[0]["id"] == "1"
        assert result[1]["id"] == "3"

    def test_filter_by_nested_field(self):
        """Should filter by nested field"""
        items = [
            {"id": "1", "from": {"emailAddress": {"address": "john@sap.com"}}},
            {"id": "2", "from": {"emailAddress": {"address": "jane@example.com"}}},
        ]
        result = apply_filter(items, "from.emailAddress.address:contains:@sap.com")
        assert len(result) == 1
        assert result[0]["id"] == "1"

    def test_multiple_conditions_and(self):
        """Should apply AND logic for multiple conditions by default"""
        items = [
            {"id": "1", "isRead": "true", "importance": "high"},
            {"id": "2", "isRead": "false", "importance": "high"},
            {"id": "3", "isRead": "true", "importance": "low"},
        ]
        result = apply_filter(items, "isRead:true,importance:high")
        assert len(result) == 1
        assert result[0]["id"] == "1"

    def test_multiple_conditions_or(self):
        """Should apply OR logic when match_all=False"""
        items = [
            {"id": "1", "isRead": "true", "importance": "high"},
            {"id": "2", "isRead": "false", "importance": "high"},
            {"id": "3", "isRead": "true", "importance": "low"},
            {"id": "4", "isRead": "false", "importance": "low"},
        ]
        result = apply_filter(items, "isRead:true,importance:high", match_all=False)
        assert len(result) == 3
        assert all(item["id"] != "4" for item in result)

    def test_empty_filter_returns_all(self):
        """Should return all items when filter is empty"""
        items = [{"id": "1"}, {"id": "2"}]
        result = apply_filter(items, "")
        assert result == items

    def test_none_filter_returns_all(self):
        """Should return all items when filter is None"""
        items = [{"id": "1"}, {"id": "2"}]
        result = apply_filter(items, None)
        assert result == items

    def test_empty_items_returns_empty(self):
        """Should return empty list when items is empty"""
        result = apply_filter([], "categories:Work")
        assert result == []

    def test_no_matching_items(self):
        """Should return empty list when no items match"""
        items = [
            {"id": "1", "categories": ["Personal"]},
            {"id": "2", "categories": ["Home"]},
        ]
        result = apply_filter(items, "categories:Work")
        assert result == []
