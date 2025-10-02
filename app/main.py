"""FastAPI application entry point"""

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app import __version__
from app.config import validate_config
from app.routers import health, events

# Validate configuration on startup
validate_config()

# Initialize FastAPI app
app = FastAPI(
    title="Tana-Connector",
    description="Local FastAPI server for Tana and Microsoft Graph API integration",
    version=__version__,
)

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(events.router, tags=["Events"])

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("🚀 Tana-Connector server starting...")
    print(f"📝 Version: {__version__}")

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    print("👋 Tana-Connector server shutting down...")
