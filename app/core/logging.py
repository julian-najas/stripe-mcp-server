import logging

from app.core.settings import settings

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)
