# Khaya AI TTS + ffmpeg conversion
import uuid

import requests

from app.config import KHAYA_API_KEY
from app.utils.logger import logger


def generate_audio(text: str) -> str | None:
    """
    Fetches audio of summary
    """
    if not text:
        return None

    if not KHAYA_API_KEY:
        logger.error("KAHAYA_API_KEY is missing")
        return None

    url = "https://translation-api.ghananlp.org/tts/v2/synthesize"
    headers = {
        "Ocp-Apim-Subscription-Key": KHAYA_API_KEY,
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
    }
    payload = {"text": text, "language": "twi", "format": "ogg"}

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        audio = f"/tmp/audio_{uuid.uuid4().hex}.ogg"
        with open(audio, "wb") as f:
            f.write(response.content)

        return audio
    except requests.exceptions.RequestException as e:
        logger.error(f"TTS API failed: {e}")
        if e.response is not None:
            logger.error(f"Server response: {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during TTS: {e}", exc_info=True)
        return None
