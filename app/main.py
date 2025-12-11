"""FastAPI application entry point"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from app import __version__
from app.config import DEBUG, validate_config
from app.logging import get_logger, setup_logging
from app.exceptions import (
    AuthenticationError,
    CacheError,
    GraphAPIError,
    TanaConnectorError,
    TemplateError,
    ValidationError,
)
from app.routers import health
from app.routers.graph import router as graph_router

validate_config()

# Initialize logging
setup_logging(debug=DEBUG)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info("Server starting", version=__version__)

    yield

    # Shutdown
    logger.info("Server shutting down")


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
app.include_router(graph_router)


# Exception handlers
@app.exception_handler(GraphAPIError)
async def graph_api_exception_handler(
    request: Request, exc: GraphAPIError
) -> JSONResponse:
    """Handle Microsoft Graph API errors."""
    return JSONResponse(
        status_code=exc.status_code or 502,
        content={
            "error": "graph_api_error",
            "message": exc.message,
            "error_code": exc.error_code,
            "details": exc.details,
        },
    )


@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(
    request: Request, exc: AuthenticationError
) -> JSONResponse:
    """Handle authentication errors."""
    return JSONResponse(
        status_code=401,
        content={
            "error": "authentication_error",
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Handle input validation errors."""
    return JSONResponse(
        status_code=400,
        content={
            "error": "validation_error",
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(TemplateError)
async def template_exception_handler(
    request: Request, exc: TemplateError
) -> JSONResponse:
    """Handle template rendering errors."""
    content: dict = {
        "error": "template_error",
        "message": exc.message,
        "details": exc.details,
    }
    if exc.line_number is not None:
        content["line_number"] = exc.line_number
    return JSONResponse(status_code=400, content=content)


@app.exception_handler(CacheError)
async def cache_exception_handler(request: Request, exc: CacheError) -> JSONResponse:
    """Handle cache operation errors."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "cache_error",
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(TanaConnectorError)
async def tana_connector_exception_handler(
    request: Request, exc: TanaConnectorError
) -> JSONResponse:
    """Handle any other TanaConnectorError (catch-all for custom exceptions)."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": exc.message,
            "details": exc.details,
        },
    )
