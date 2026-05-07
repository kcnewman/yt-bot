"""Clients for external APIs - initialization and management."""

from google import genai

from app.config import GCP_PROJECT_ID, GCP_REGION
from app.utils.logger import logger


def create_genai_client() -> genai.Client | None:
    """
    Create and initialize a Google GenAI client.

    Returns:
        Initialized GenAI client, or None if initialization fails.
    """
    if not GCP_PROJECT_ID or not GCP_REGION:
        logger.error("GCP_PROJECT_ID or GCP_REGION environment variables are missing.")
        return None

    try:
        client = genai.Client(
            vertexai=True,
            project=GCP_PROJECT_ID,
            location=GCP_REGION,
        )
        logger.info("Google GenAI Client initialized successfully.")
        return client
    except Exception as error:
        logger.error(f"Failed to initialize GenAI Client: {error}", exc_info=True)
        return None
