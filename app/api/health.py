from fastapi import APIRouter, status

from app.core.settings import settings
from app.models.schemas import HealthResponse, ReadyResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check endpoint",
)
async def health_check():
    """
    Health check endpoint. No authentication required.
    Returns application status and version.
    """
    return HealthResponse(status="healthy", version=settings.APP_VERSION, debug=settings.DEBUG)


@router.get(
    "/ready",
    response_model=ReadyResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness check endpoint",
)
async def readiness_check():
    """
    Readiness check endpoint. No authentication required.
    Returns whether the application is ready to serve requests.
    """
    return ReadyResponse(ready=True)
