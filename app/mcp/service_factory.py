"""Service factory for MCP server - creates services without FastAPI Depends."""

from __future__ import annotations

from typing import Optional

from app.services.auth_service import AuthService
from app.services.availability_service import AvailabilityService
from app.services.calendar_service import CalendarService
from app.services.delta_cache_service import DeltaCacheService
from app.services.graph_service import GraphService
from app.services.mail_service import MailService


class ServiceFactory:
    """Factory for creating and caching service instances.

    This factory creates singleton instances of services for use in the MCP server.
    It reuses the existing authentication and Graph client across all services.
    """

    def __init__(self) -> None:
        self._auth_service: Optional[AuthService] = None
        self._graph_service: Optional[GraphService] = None
        self._delta_cache_service: Optional[DeltaCacheService] = None
        self._calendar_service: Optional[CalendarService] = None
        self._mail_service: Optional[MailService] = None
        self._availability_service: Optional[AvailabilityService] = None

    def get_auth_service(self) -> AuthService:
        """Get or create AuthService singleton."""
        if self._auth_service is None:
            self._auth_service = AuthService()
        return self._auth_service

    def get_graph_service(self) -> GraphService:
        """Get or create GraphService singleton."""
        if self._graph_service is None:
            self._graph_service = GraphService(self.get_auth_service())
        return self._graph_service

    def get_delta_cache_service(self) -> DeltaCacheService:
        """Get or create DeltaCacheService singleton."""
        if self._delta_cache_service is None:
            self._delta_cache_service = DeltaCacheService()
        return self._delta_cache_service

    def get_calendar_service(self) -> CalendarService:
        """Get or create CalendarService singleton."""
        if self._calendar_service is None:
            self._calendar_service = CalendarService(self.get_graph_service())
        return self._calendar_service

    def get_mail_service(self) -> MailService:
        """Get or create MailService singleton."""
        if self._mail_service is None:
            self._mail_service = MailService(
                self.get_graph_service(),
                self.get_delta_cache_service(),
            )
        return self._mail_service

    def get_availability_service(self) -> AvailabilityService:
        """Get or create AvailabilityService singleton."""
        if self._availability_service is None:
            self._availability_service = AvailabilityService(self.get_graph_service())
        return self._availability_service


# Global service factory instance
_factory: Optional[ServiceFactory] = None


def get_factory() -> ServiceFactory:
    """Get or create the global service factory."""
    global _factory
    if _factory is None:
        _factory = ServiceFactory()
    return _factory
