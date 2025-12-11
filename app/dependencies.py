"""FastAPI dependency injection providers.

This module provides dependency injection for all services, enabling:
- Better testability through mock injection
- Cleaner separation of concerns
- Explicit dependency graphs

Usage in routers:
    from app.dependencies import CalendarServiceDep

    @router.get("/CalendarView")
    async def get_calendar_view(service: CalendarServiceDep):
        events = await service.get_calendar_view(...)

Usage in tests:
    from app.dependencies import get_calendar_service

    def test_something():
        app.dependency_overrides[get_calendar_service] = lambda: mock_service
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.services.auth_service import AuthService
from app.services.availability_service import AvailabilityService
from app.services.calendar_service import CalendarService
from app.services.delta_cache_service import DeltaCacheService
from app.services.graph_service import GraphService
from app.services.mail_service import MailService
from app.services.template_service import TemplateService


# =============================================================================
# Singleton instances (module-level, created once on import)
# =============================================================================

_auth_service: AuthService | None = None
_graph_service: GraphService | None = None
_delta_cache_service: DeltaCacheService | None = None
_template_service: TemplateService | None = None


# =============================================================================
# Core Services (Singletons)
# =============================================================================


def get_auth_service() -> AuthService:
    """Get singleton AuthService instance."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service


def get_graph_service(
    auth_service: AuthService = Depends(get_auth_service),
) -> GraphService:
    """Get singleton GraphService instance with injected auth service."""
    global _graph_service
    if _graph_service is None:
        _graph_service = GraphService(auth_service=auth_service)
    return _graph_service


def get_delta_cache_service() -> DeltaCacheService:
    """Get singleton DeltaCacheService instance."""
    global _delta_cache_service
    if _delta_cache_service is None:
        _delta_cache_service = DeltaCacheService()
    return _delta_cache_service


def get_template_service() -> TemplateService:
    """Get singleton TemplateService instance."""
    global _template_service
    if _template_service is None:
        _template_service = TemplateService()
    return _template_service


# =============================================================================
# Domain Services (created per-request, with singleton dependencies)
# =============================================================================


def get_calendar_service(
    graph_service: GraphService = Depends(get_graph_service),
) -> CalendarService:
    """Get CalendarService with injected dependencies."""
    return CalendarService(graph_service=graph_service)


def get_mail_service(
    graph_service: GraphService = Depends(get_graph_service),
    delta_cache_service: DeltaCacheService = Depends(get_delta_cache_service),
) -> MailService:
    """Get MailService with injected dependencies."""
    return MailService(
        graph_service=graph_service,
        delta_cache_service=delta_cache_service,
    )


def get_availability_service(
    graph_service: GraphService = Depends(get_graph_service),
) -> AvailabilityService:
    """Get AvailabilityService with injected dependencies."""
    return AvailabilityService(graph_service=graph_service)


# =============================================================================
# Type Aliases for cleaner endpoint signatures
# =============================================================================

AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
GraphServiceDep = Annotated[GraphService, Depends(get_graph_service)]
DeltaCacheServiceDep = Annotated[DeltaCacheService, Depends(get_delta_cache_service)]
TemplateServiceDep = Annotated[TemplateService, Depends(get_template_service)]
CalendarServiceDep = Annotated[CalendarService, Depends(get_calendar_service)]
MailServiceDep = Annotated[MailService, Depends(get_mail_service)]
AvailabilityServiceDep = Annotated[
    AvailabilityService, Depends(get_availability_service)
]


# =============================================================================
# Testing utilities
# =============================================================================


def reset_singletons() -> None:
    """Reset all singleton instances. Use only in tests."""
    global _auth_service, _graph_service, _delta_cache_service, _template_service
    _auth_service = None
    _graph_service = None
    _delta_cache_service = None
    _template_service = None
