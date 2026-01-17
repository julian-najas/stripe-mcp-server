import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi_mcp import FastApiMCP

from app.api import health, tools_rest, payments
from app.api.webhooks import stripe as stripe_webhooks
from app.core.logging import logger
from app.core.settings import settings
from app.db.database import init_db


def validate_startup():
    """Validate configuration on startup."""
    print(f"[STARTUP] DEBUG={settings.DEBUG}, API_KEY={settings.API_KEY}, ENV={settings.ENVIRONMENT}")
    if not settings.DEBUG and not settings.API_KEY:
        raise ValueError(
            "Production mode (DEBUG=false) requires API_KEY environment variable to be set"
        )
    if not settings.DEBUG:
        logger.warning(f"Running in production mode (ENVIRONMENT={settings.ENVIRONMENT})")
    else:
        logger.info("Running in debug mode")


# Store request_id in context for logging
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager."""
    validate_startup()
    # Initialize database
    init_db()
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Database: {settings.DATABASE_URL}")
    yield
    logger.info("Shutting down application")


app = FastAPI(
    title=settings.APP_NAME, version=settings.APP_VERSION, debug=settings.DEBUG, lifespan=lifespan
)


@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    """Add request_id to all requests for tracking."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    logger.info(f"Request: {request.method} {request.url.path} - request_id: {request_id}")

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


# Include routers
app.include_router(health.router, prefix="")
app.include_router(tools_rest.router, prefix=settings.API_PREFIX)
app.include_router(payments.router, prefix=settings.API_PREFIX)
app.include_router(stripe_webhooks.router, prefix=settings.API_PREFIX)


# Register MCP server - converts selected FastAPI operations to MCP tools.
# We restrict tools to the "payments" tag and forward headers needed for auth/idempotency.
mcp = FastApiMCP(
    app,
    include_tags=["payments"],
    headers=["authorization", "x-api-key", "idempotency-key"],
)
# Prefer HTTP transport (recommended by fastapi-mcp). This avoids SSE-specific client requirements.
mcp.mount_http(mount_path="/mcp")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
