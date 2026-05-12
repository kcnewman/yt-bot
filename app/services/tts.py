"""Text-to-speech audio generation service."""

import subprocess
import uuid
from pathlib import Path

import requests

from app.config import KHAYA_API_KEY, TTS_TEMPO
from app.core.constants import TIMEOUT_SECONDS, TTS_FORMAT, TTS_LANGUAGE, TTS_URL
from app.core.exceptions import TTSError
from app.core.http_utils import build_khaya_headers
from app.utils.logger import logger


def _get_audio_path(prefix: str = "audio") -> str:
    """Generate a unique temporary audio file path."""
    return f"/tmp/{prefix}_{uuid.uuid4().hex}.mp3"


def _build_tempo_filter(tempo: float) -> str | None:
    """
    Build an ffmpeg atempo filter chain for tempo adjustment.

    Args:
        tempo: The target tempo multiplier.

    Returns:
        The filter expression, or None if no adjustment needed.
    """
    if tempo <= 0 or abs(tempo - 1.0) < 0.01:
        return None

    stages: list[float] = []
    remaining = tempo

    while remaining < 0.5:
        stages.append(0.5)
        remaining /= 0.5

    while remaining > 2.0:
        stages.append(2.0)
        remaining /= 2.0

    stages.append(remaining)
    return ",".join(f"atempo={stage:.5f}" for stage in stages)


def _apply_tempo_adjustment(audio_path: str, tempo: float) -> str:
    """
    Apply tempo adjustment to audio using ffmpeg.

    Args:
        audio_path: Path to the input audio file.
        tempo: The target tempo multiplier.

    Returns:
        Path to the adjusted audio file, or original path if adjustment fails.
    """
    filter_expr = _build_tempo_filter(tempo)
    if filter_expr is None:
        return audio_path

    output_path = _get_audio_path("audio_tempo")
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        audio_path,
        "-filter:a",
        filter_expr,
        "-vn",
        output_path,
    ]

    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
        logger.info(f"Applied tempo adjustment: {tempo:.2f}")
        Path(audio_path).unlink(missing_ok=True)
        return output_path
    except Exception as error:
        logger.warning(f"Tempo filter failed, using original audio. Error: {error}")
        return audio_path


def _request_audio_from_api(text: str) -> bytes:
    """
    Request MP3 audio bytes from Khaya TTS API.

    Args:
        text: The text to convert to speech.

    Returns:
        The audio bytes.

    Raises:
        TTSError: If the API request fails.
    """
    payload = {
        "text": text,
        "language": TTS_LANGUAGE,
        "format": TTS_FORMAT,
    }

    try:
        response = requests.post(
            TTS_URL,
            json=payload,
            headers=build_khaya_headers(),
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()

        if not response.content:
            raise TTSError("TTS API returned empty audio response.")

        return response.content

    except requests.exceptions.RequestException as error:
        error_msg = f"TTS API request failed: {error}"
        if hasattr(error, "response") and error.response is not None:
            error_msg += f" (Server: {error.response.text})"
        logger.error(error_msg)
        raise TTSError(error_msg)
    except Exception as error:
        logger.error(f"Unexpected error calling TTS API: {error}", exc_info=True)
        raise TTSError(f"TTS API call failed: {error}")


def generate_audio(text: str) -> str:
    """
    Generate Twi speech audio from text.

    Args:
        text: The Twi text to convert to speech.

    Returns:
        Path to the generated audio file.

    Raises:
        TTSError: If audio generation fails.
    """
    if not text or not text.strip():
        raise TTSError("Text to synthesize cannot be empty.")

    if not KHAYA_API_KEY:
        raise TTSError("KHAYA_API_KEY is not configured.")

    clean_text = text.strip()

    try:
        audio_bytes = _request_audio_from_api(clean_text)
        audio_path = _get_audio_path("audio")
        Path(audio_path).write_bytes(audio_bytes)

        adjusted_path = _apply_tempo_adjustment(audio_path, TTS_TEMPO)
        logger.info(f"Generated audio file: {adjusted_path}")
        return adjusted_path

    except Exception as error:
        logger.error(f"Unexpected error during TTS generation: {error}", exc_info=True)
        raise TTSError(f"Audio generation failed: {error}")
