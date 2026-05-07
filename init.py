"""
Initialize required directories for the YouTube Telegram Bot.
This script ensures all necessary directories exist before the application runs.
"""

import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Define required directories
REQUIRED_DIRECTORIES = [
    "logs",
    "prompts",
    "temp",
    "app",
    "app/services",
    "app/utils",
]


def create_directories():
    """Create all required directories if they don't exist."""
    for directory in REQUIRED_DIRECTORIES:
        path = Path(directory)
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {directory}")
            except Exception as e:
                logger.error(f"Failed to create directory {directory}: {e}")
                raise
        else:
            logger.debug(f"Directory already exists: {directory}")


if __name__ == "__main__":
    logger.info("Initializing required directories...")
    create_directories()
    logger.info("Initialization complete")
