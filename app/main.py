"""FastAPI application entry point"""

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app import __version__
from app.config import validate_config
from app.routers import health, events

validate_config()

app = FastAPI(
    title="Tana-Connector API",
    description="Microsoft Outlook calendar integration for Tana. Fetch events in JSON or Tana Paste format with filtering, category tagging, and smart description processing.",
    version=__version__,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(events.router)

@app.on_event("startup")
async def startup_event():
    print("🚀 Tana-Connector server starting...")
    print(f"📝 Version: {__version__}")

@app.on_event("shutdown")
async def shutdown_event():
    print("👋 Tana-Connector server shutting down...")
