import requests
from requests.exceptions import RequestException

from app.config import KHAYA_API_KEY
from app.utils.logger import logger

TRANSLATE_URL = "https://translation-api.ghananlp.org/v2/translate"
TRANSLATE_LANG = "en-tw"
REQUEST_TIMEOUT_SECONDS = 30


def _headers() -> dict[str, str]:
    """Build request headers for Khaya translation."""
    return {
        "Ocp-Apim-Subscription-Key": KHAYA_API_KEY or "",
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
    }


def translate(text: str) -> str | None:
    """Translate English text to Twi."""
    if not text or not text.strip():
        return None

    if not KHAYA_API_KEY:
        logger.error("KHAYA_API_KEY is missing")
        return None

    payload = {"in": text.strip(), "lang": TRANSLATE_LANG}

    try:
        response = requests.post(
            TRANSLATE_URL,
            json=payload,
            headers=_headers(),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()

        translation = response.text.strip()
        return translation or None

    except RequestException as error:
        logger.error(f"Translation API request failed: {error}")

        if error.response is not None:
            logger.error(f"Server response: {error.response.text}")
        return None

    except Exception as error:
        logger.error(f"Unexpected error during translation: {error}", exc_info=True)
        return None
