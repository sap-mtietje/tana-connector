"""Graph API passthrough routers"""

from fastapi import APIRouter
from app.routers.graph import calendar

router = APIRouter(prefix="/me", tags=["Microsoft Graph"])
router.include_router(calendar.router)
