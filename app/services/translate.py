"""Translation service."""

import requests
from requests.exceptions import RequestException

from app.config import KHAYA_API_KEY
from app.core.constants import TIMEOUT_SECONDS, TRANSLATE_LANG, TRANSLATE_URL
from app.core.exceptions import TranslationError
from app.utils.logger import logger


def _build_headers() -> dict[str, str]:
    """Build HTTP headers for Khaya translation API."""
    return {
        "Ocp-Apim-Subscription-Key": KHAYA_API_KEY or "",
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
    }


def translate(text: str) -> str:
    """
    Translate English text to Twi using Khaya AI API.

    Args:
        text: The English text to translate.

    Returns:
        The translated Twi text.

    Raises:
        TranslationError: If translation fails.
    """
    if not text or not text.strip():
        raise TranslationError("Text to translate cannot be empty.")

    if not KHAYA_API_KEY:
        raise TranslationError("KHAYA_API_KEY is not configured.")

    clean_text = text.strip()
    payload = {"in": clean_text, "lang": TRANSLATE_LANG}

    try:
        response = requests.post(
            TRANSLATE_URL,
            json=payload,
            headers=_build_headers(),
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()

        translation = response.text.strip()
        if not translation:
            raise TranslationError("Translation API returned empty response.")

        logger.info(f"Successfully translated {len(clean_text)} characters.")
        return translation

    except RequestException as error:
        error_msg = f"Translation API request failed: {error}"
        if hasattr(error, "response") and error.response is not None:
            error_msg += f" (Server: {error.response.text})"
        logger.error(error_msg)
        raise TranslationError(error_msg)
    except TranslationError:
        raise
    except Exception as error:
        logger.error(f"Unexpected error during translation: {error}", exc_info=True)
        raise TranslationError(f"Translation failed: {error}")
