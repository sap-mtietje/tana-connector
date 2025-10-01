"""Health check endpoints"""

from fastapi import APIRouter
from app import __version__

router = APIRouter()

@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Tana-Connector API",
        "version": __version__,
        "status": "running"
    }

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": __version__
    }


