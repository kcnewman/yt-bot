"""Clients for external APIs - initialization and management."""

from google import genai

from app.config import GCP_PROJECT_ID, GCP_REGION
from app.utils.logger import logger

_genai_client: genai.Client | None = None


def create_genai_client() -> genai.Client | None:
    global _genai_client
    if _genai_client is not None:
        return _genai_client

    if not GCP_PROJECT_ID or not GCP_REGION:
        logger.error("GCP_PROJECT_ID or GCP_REGION environment variables are missing.")
        return None

    try:
        _genai_client = genai.Client(
            vertexai=True,
            project=GCP_PROJECT_ID,
            location=GCP_REGION,
        )
        logger.info("Google GenAI client initialized.")
        return _genai_client
    except Exception as error:
        logger.error(f"Failed to initialize GenAI client: {error}", exc_info=True)
        return None
