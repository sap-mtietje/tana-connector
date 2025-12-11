"""Unit tests for custom exceptions."""

import pytest

from app.exceptions import (
    AuthenticationError,
    CacheError,
    GraphAPIError,
    TanaConnectorError,
    TemplateError,
    ValidationError,
)


@pytest.mark.unit
class TestTanaConnectorError:
    """Tests for base TanaConnectorError exception."""

    def test_basic_instantiation(self):
        """Should create exception with message."""
        exc = TanaConnectorError("Test error")
        assert exc.message == "Test error"
        assert exc.details == {}
        assert str(exc) == "Test error"

    def test_with_details(self):
        """Should create exception with message and details."""
        exc = TanaConnectorError("Test error", details={"key": "value"})
        assert exc.message == "Test error"
        assert exc.details == {"key": "value"}

    def test_inheritance(self):
        """Should inherit from Exception."""
        exc = TanaConnectorError("Test")
        assert isinstance(exc, Exception)


@pytest.mark.unit
class TestGraphAPIError:
    """Tests for GraphAPIError exception."""

    def test_basic_instantiation(self):
        """Should create exception with message."""
        exc = GraphAPIError("API failed")
        assert exc.message == "API failed"
        assert exc.status_code is None
        assert exc.error_code is None
        assert exc.details == {}

    def test_with_status_code(self):
        """Should create exception with status code."""
        exc = GraphAPIError("API failed", status_code=401)
        assert exc.status_code == 401

    def test_with_error_code(self):
        """Should create exception with Graph API error code."""
        exc = GraphAPIError("Access denied", error_code="ErrorAccessDenied")
        assert exc.error_code == "ErrorAccessDenied"

    def test_full_instantiation(self):
        """Should create exception with all attributes."""
        exc = GraphAPIError(
            message="API failed",
            status_code=403,
            error_code="ErrorAccessDenied",
            details={"resource": "/me/calendar"},
        )
        assert exc.message == "API failed"
        assert exc.status_code == 403
        assert exc.error_code == "ErrorAccessDenied"
        assert exc.details == {"resource": "/me/calendar"}

    def test_inheritance(self):
        """Should inherit from TanaConnectorError."""
        exc = GraphAPIError("Test")
        assert isinstance(exc, TanaConnectorError)
        assert isinstance(exc, Exception)


@pytest.mark.unit
class TestAuthenticationError:
    """Tests for AuthenticationError exception."""

    def test_basic_instantiation(self):
        """Should create exception with message."""
        exc = AuthenticationError("Auth failed")
        assert exc.message == "Auth failed"
        assert exc.details == {}

    def test_with_details(self):
        """Should create exception with details."""
        exc = AuthenticationError("Token expired", details={"token_type": "access"})
        assert exc.details == {"token_type": "access"}

    def test_inheritance(self):
        """Should inherit from TanaConnectorError."""
        exc = AuthenticationError("Test")
        assert isinstance(exc, TanaConnectorError)


@pytest.mark.unit
class TestValidationError:
    """Tests for ValidationError exception."""

    def test_basic_instantiation(self):
        """Should create exception with message."""
        exc = ValidationError("Invalid input")
        assert exc.message == "Invalid input"

    def test_with_details(self):
        """Should create exception with field details."""
        exc = ValidationError(
            "Invalid date format",
            details={"field": "startDate", "expected": "ISO 8601"},
        )
        assert exc.details == {"field": "startDate", "expected": "ISO 8601"}

    def test_inheritance(self):
        """Should inherit from TanaConnectorError."""
        exc = ValidationError("Test")
        assert isinstance(exc, TanaConnectorError)


@pytest.mark.unit
class TestTemplateError:
    """Tests for TemplateError exception."""

    def test_basic_instantiation(self):
        """Should create exception with message."""
        exc = TemplateError("Template failed")
        assert exc.message == "Template failed"
        assert exc.line_number is None
        assert exc.details == {}

    def test_with_line_number(self):
        """Should create exception with line number."""
        exc = TemplateError("Syntax error", line_number=5)
        assert exc.line_number == 5

    def test_full_instantiation(self):
        """Should create exception with all attributes."""
        exc = TemplateError(
            message="Undefined variable",
            line_number=10,
            details={"variable": "event.title"},
        )
        assert exc.message == "Undefined variable"
        assert exc.line_number == 10
        assert exc.details == {"variable": "event.title"}

    def test_inheritance(self):
        """Should inherit from TanaConnectorError."""
        exc = TemplateError("Test")
        assert isinstance(exc, TanaConnectorError)


@pytest.mark.unit
class TestCacheError:
    """Tests for CacheError exception."""

    def test_basic_instantiation(self):
        """Should create exception with message."""
        exc = CacheError("Cache read failed")
        assert exc.message == "Cache read failed"

    def test_with_details(self):
        """Should create exception with details."""
        exc = CacheError(
            "Failed to write cache",
            details={"path": "/tmp/cache.json", "error": "Permission denied"},
        )
        assert exc.details["path"] == "/tmp/cache.json"

    def test_inheritance(self):
        """Should inherit from TanaConnectorError."""
        exc = CacheError("Test")
        assert isinstance(exc, TanaConnectorError)


@pytest.mark.unit
class TestExceptionHierarchy:
    """Tests for exception hierarchy and catch-all behavior."""

    def test_catch_all_with_base_exception(self):
        """Should be able to catch all custom exceptions with base class."""
        exceptions = [
            GraphAPIError("API error"),
            AuthenticationError("Auth error"),
            ValidationError("Validation error"),
            TemplateError("Template error"),
            CacheError("Cache error"),
        ]

        for exc in exceptions:
            try:
                raise exc
            except TanaConnectorError as caught:
                assert caught.message is not None

    def test_specific_catch_before_base(self):
        """Should catch specific exception before base class."""
        exc = GraphAPIError("API error", status_code=500)

        try:
            raise exc
        except GraphAPIError as caught:
            assert caught.status_code == 500
        except TanaConnectorError:
            pytest.fail("Should have caught GraphAPIError specifically")
