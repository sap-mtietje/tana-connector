"""FastAPI application entry point"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app import __version__
from app.config import validate_config
from app.routers import health, events
from app.routers.graph import router as graph_router

validate_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    print("🚀 Tana-Connector server starting...")
    print(f"📝 Version: {__version__}")

    yield

    # Shutdown
    print("👋 Tana-Connector server shutting down...")


app = FastAPI(
    title="Tana-Connector API",
    description="Microsoft Outlook calendar integration for Tana. Fetch events in JSON or Tana Paste format with filtering, category tagging, and smart description processing.",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(graph_router)  # New MS Graph style API
app.include_router(events.router)  # Legacy endpoints
