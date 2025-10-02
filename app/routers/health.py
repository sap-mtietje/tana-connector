"""Health check endpoints"""

from fastapi import APIRouter
from app import __version__

router = APIRouter(tags=["Health"])

@router.get("/", summary="API Root", description="Get API information and status")
async def root():
    return {
        "message": "Tana-Connector API",
        "version": __version__,
        "status": "running"
    }

@router.get("/health", summary="Health Check", description="Check if API is healthy")
async def health_check():
    return {
        "status": "healthy",
        "version": __version__
    }


