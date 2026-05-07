# Khaya AI TTS service
import subprocess
import uuid
from pathlib import Path

import requests

from app.config import KHAYA_API_KEY, TTS_TEMPO
from app.utils.logger import logger

TTS_URL = "https://translation-api.ghananlp.org/tts/v2/synthesize"
TTS_LANGUAGE = "twi"
TTS_FORMAT = "mp3"
REQUEST_TIMEOUT_SECONDS = 30


def _headers() -> dict[str, str]:
    """Build request headers for Khaya TTS."""
    return {
        "Ocp-Apim-Subscription-Key": KHAYA_API_KEY or "",
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
    }


def _audio_path(prefix: str) -> str:
    """Return a unique temporary MP3 path."""
    return f"/tmp/{prefix}_{uuid.uuid4().hex}.mp3"


def _build_tempo_filter(tempo: float) -> str | None:
    """Create an ffmpeg atempo filter chain."""
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


def _apply_tempo_filter(audio_path: str, tempo: float) -> str:
    """Apply tempo change and return output path, or original on failure."""
    filter_expr = _build_tempo_filter(tempo)
    if filter_expr is None:
        return audio_path

    output_path = _audio_path("audio_tempo")
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
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        return output_path
    except Exception as error:
        logger.warning(
            f"Tempo filter failed; using original audio. Error: {error}",
        )
        return audio_path


def _request_tts_audio(text: str) -> bytes | None:
    """Request MP3 audio bytes from Khaya TTS."""
    payload = {
        "text": text,
        "language": TTS_LANGUAGE,
        "format": TTS_FORMAT,
    }

    try:
        response = requests.post(
            TTS_URL,
            json=payload,
            headers=_headers(),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as error:
        logger.error(f"TTS API failed: {error}")
        if error.response is not None:
            logger.error(f"Server response: {error.response.text}")
        return None


def generate_audio(text: str) -> str | None:
    """Generate Twi speech audio file from text."""
    if not text or not text.strip():
        return None

    if not KHAYA_API_KEY:
        logger.error("KHAYA_API_KEY is missing")
        return None

    try:
        audio_bytes = _request_tts_audio(text.strip())
        if not audio_bytes:
            return None

        audio = _audio_path("audio")
        Path(audio).write_bytes(audio_bytes)

        adjusted = _apply_tempo_filter(audio, TTS_TEMPO)
        if adjusted != audio:
            logger.info(f"Applied tempo adjustment: {TTS_TEMPO:.2f}")
        return adjusted
    except Exception as error:
        logger.error(f"Unexpected error during TTS: {error}", exc_info=True)
        return None
