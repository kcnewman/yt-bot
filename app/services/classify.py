from typing import Literal, cast

from google import genai

from app.config import GCP_PROJECT_ID, GCP_REGION
from app.utils.logger import logger
from app.utils.prompt import load_prompt

MODEL_NAME = "gemini-2.5-flash-lite"
PROMPT_FILE = "classification.txt"
DEFAULT_CONTENT_TYPE = "general"
CLASSIFICATION_SAMPLE_CHARS = 8000

ContentType = Literal[
    "tutorial",
    "interview",
    "news",
    "explainer",
    "review",
    "story",
    "general",
]
ALLOWED_CONTENT_TYPES: set[ContentType] = {
    "tutorial",
    "interview",
    "news",
    "explainer",
    "review",
    "story",
    "general",
}


def _create_client() -> genai.Client | None:
    """Create and return the GenAI client."""
    try:
        return genai.Client(
            vertexai=True,
            project=GCP_PROJECT_ID,
            location=GCP_REGION,
        )
    except Exception as error:
        logger.error(f"Failed to initialize classifier client: {error}", exc_info=True)
        return None


client: genai.Client | None = _create_client()


def _render_prompt(transcript: str) -> str | None:
    """Load and render the classification prompt."""
    template = load_prompt(PROMPT_FILE).strip()
    if not template:
        logger.error(f"Prompt template is empty or missing: {PROMPT_FILE}")
        return None

    return template.format(transcript=transcript[:CLASSIFICATION_SAMPLE_CHARS])


def _parse_content_type(value: str | None) -> ContentType:
    """Return a valid content type."""
    if not value:
        return DEFAULT_CONTENT_TYPE

    content_type = value.strip().lower()
    if content_type in ALLOWED_CONTENT_TYPES:
        return cast(ContentType, content_type)

    logger.warning(f"Unknown content type returned: {value}")
    return DEFAULT_CONTENT_TYPE


def classify_content(transcript: str) -> ContentType:
    """Classify transcript content type."""
    if not transcript or not transcript.strip():
        return DEFAULT_CONTENT_TYPE

    if client is None:
        logger.error("Classifier client is not available.")
        return DEFAULT_CONTENT_TYPE

    prompt = _render_prompt(transcript.strip())
    if prompt is None:
        return DEFAULT_CONTENT_TYPE

    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        content_type = _parse_content_type(response.text)
        logger.info(f"Classified content type: {content_type}")
        return content_type
    except Exception as error:
        logger.error(f"Content classification failed: {error}", exc_info=True)
        return DEFAULT_CONTENT_TYPE
