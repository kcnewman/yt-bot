# Khaya AI translation
import requests
from requests.exceptions import RequestException

from app.config import KHAYA_API_KEY
from app.utils.logger import logger


def translate(text: str) -> str | None:
    """
    Translatesd the English summary to Twi using Khaya AI
    """
    if not text:
        return None

    if not KHAYA_API_KEY:
        logger.error("Missing KHAYA API KEY")
        return None

    url = "https://translation-api.ghananlp.org/v2/translate"

    headers = {
        "Ocp-Apim-Subscription-Key": KHAYA_API_KEY,
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
    }

    payload = {"in": text, "lang": "en-tw"}

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        translation = response.text
        return translation

    except RequestException as e:
        logger.error(f"API request failed: {e}")

        if e.response is not None:
            logger.error(f"Server response: {e.response.text}")
        return None

    except Exception as e:
        logger.error(f"Unexpected error during translation: {e}", exc_info=True)
        return None
