from fastapi import Header, HTTPException, status

from app.core.logging import logger
from app.core.settings import settings


async def verify_api_key(x_api_key: str | None = Header(None)) -> str:
    """Verify API key from header.

    - If DEBUG=true: allow without key (development mode)
    - If DEBUG=false and API_KEY is set: header must match
    - If API_KEY is None: no validation needed
    """
    # Debug mode: no validation
    if settings.DEBUG:
        logger.debug("Debug mode: skipping API key validation")
        return "debug-mode"

    # Production mode with API_KEY configured
    if settings.API_KEY:
        if not x_api_key:
            logger.warning("Missing API key header")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-API-Key header"
            )

        if x_api_key != settings.API_KEY:
            logger.warning(f"Invalid API key: {x_api_key[:10]}...")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key")

    return x_api_key or "authenticated"
