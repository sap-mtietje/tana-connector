"""Custom exceptions for tana-connector.

This module defines a hierarchy of exceptions for better error handling:

- TanaConnectorError: Base exception for all custom errors
  - GraphAPIError: Errors from Microsoft Graph API calls
  - AuthenticationError: Authentication/authorization failures
  - ValidationError: Input validation errors
  - TemplateError: Jinja2 template rendering errors
  - CacheError: Delta cache operation errors
"""

from typing import Any, Dict, Optional


class TanaConnectorError(Exception):
    """Base exception for tana-connector.

    All custom exceptions inherit from this class, allowing
    catch-all handling when needed.

    Attributes:
        message: Human-readable error description
        details: Optional dict with additional context
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class GraphAPIError(TanaConnectorError):
    """Error from Microsoft Graph API.

    Raised when Graph API calls fail, including network errors,
    permission issues, and invalid requests.

    Attributes:
        message: Error description
        status_code: HTTP status code from Graph API (if available)
        error_code: Graph API error code (e.g., 'ErrorAccessDenied')
        details: Additional error context
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(message, details)


class AuthenticationError(TanaConnectorError):
    """Authentication or authorization error.

    Raised when:
    - Initial authentication fails
    - Token refresh fails
    - Insufficient permissions for requested operation
    """

    pass


class ValidationError(TanaConnectorError):
    """Input validation error.

    Raised when request parameters fail validation:
    - Missing required parameters
    - Invalid date formats
    - Invalid filter expressions
    """

    pass


class TemplateError(TanaConnectorError):
    """Template rendering error.

    Raised when Jinja2 template processing fails:
    - Syntax errors in template
    - Undefined variables
    - Filter errors

    Attributes:
        message: Error description
        line_number: Line where error occurred (if available)
        details: Additional context
    """

    def __init__(
        self,
        message: str,
        line_number: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.line_number = line_number
        super().__init__(message, details)


class CacheError(TanaConnectorError):
    """Cache operation error.

    Raised when delta cache operations fail:
    - Failed to read cache file
    - Failed to write cache file
    - Cache corruption
    """

    pass


__all__ = [
    "TanaConnectorError",
    "GraphAPIError",
    "AuthenticationError",
    "ValidationError",
    "TemplateError",
    "CacheError",
]
