"""Content classification service."""

from google import genai

from app.core.clients import create_genai_client
from app.core.constants import (
    CLASSIFY_ALLOWED,
    CLASSIFY_DEFAULT,
    CLASSIFY_MODEL,
    CLASSIFY_PROMPT,
    CLASSIFY_SAMPLE_CHARS,
)
from app.utils.logger import logger
from app.utils.prompt import load_prompt

ContentType = str

client: genai.Client | None = create_genai_client()


def _render_classification_prompt(transcript: str) -> str:
    template = load_prompt(CLASSIFY_PROMPT).strip()
    if not template:
        raise Exception(f"Classification prompt template is missing: {CLASSIFY_PROMPT}")

    return template.format(transcript=transcript[:CLASSIFY_SAMPLE_CHARS])


def _validate_content_type(value: str | None) -> str:
    if not value:
        return CLASSIFY_DEFAULT

    content_type = value.strip().lower()
    if content_type in CLASSIFY_ALLOWED:
        return content_type

    logger.warning(
        f"Unknown content type returned: {value}, using default: {CLASSIFY_DEFAULT}"
    )
    return CLASSIFY_DEFAULT


def classify_content(transcript: str) -> str:
    if not transcript or not transcript.strip():
        logger.info(f"Empty transcript, using default content type: {CLASSIFY_DEFAULT}")
        return CLASSIFY_DEFAULT

    if client is None:
        logger.error("GenAI client is unavailable, using default content type.")
        return CLASSIFY_DEFAULT

    try:
        prompt = _render_classification_prompt(transcript.strip())
        response = client.models.generate_content(model=CLASSIFY_MODEL, contents=prompt)
        if not response.text:
            logger.warning("Gemini returned empty response for classification.")
            return CLASSIFY_DEFAULT
        content_type = _validate_content_type(response.text)
        logger.info(f"Classified content type: {content_type}")
        return content_type

    except Exception as error:
        logger.error(f"Content classification failed: {error}", exc_info=True)
        return CLASSIFY_DEFAULT
