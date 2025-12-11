"""Business logic services."""

from app.services.auth_service import auth_service, AuthService
from app.services.availability_service import availability_service, AvailabilityService
from app.services.calendar_service import calendar_service, CalendarService
from app.services.delta_cache_service import delta_cache_service, DeltaCacheService
from app.services.graph_service import graph_service, GraphService
from app.services.mail_service import mail_service, MailService
from app.services.template_service import template_service, TemplateService

__all__ = [
    # Service instances
    "auth_service",
    "availability_service",
    "calendar_service",
    "delta_cache_service",
    "graph_service",
    "mail_service",
    "template_service",
    # Service classes
    "AuthService",
    "AvailabilityService",
    "CalendarService",
    "DeltaCacheService",
    "GraphService",
    "MailService",
    "TemplateService",
]
