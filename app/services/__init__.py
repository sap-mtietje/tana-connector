"""Business logic services.

Service classes are available for import. Service instances are managed
via dependency injection in app.dependencies.
"""

from app.services.auth_service import AuthService
from app.services.availability_service import AvailabilityService
from app.services.calendar_service import CalendarService
from app.services.delta_cache_service import DeltaCacheService
from app.services.graph_service import GraphService
from app.services.mail_service import MailService
from app.services.template_service import TemplateService

__all__ = [
    "AuthService",
    "AvailabilityService",
    "CalendarService",
    "DeltaCacheService",
    "GraphService",
    "MailService",
    "TemplateService",
]
