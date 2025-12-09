"""Graph API passthrough routers"""

from fastapi import APIRouter
from app.routers.graph import calendar, mail, availability

router = APIRouter(prefix="/me")
router.include_router(calendar.router)
router.include_router(mail.router)
router.include_router(availability.router)
