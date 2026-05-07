"""Application configuration - environment variables and settings."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)


def _get_required_env(key: str) -> str | None:
    """Get an environment variable, log a warning if missing."""
    value = os.getenv(key)
    if not value:
        from app.utils.logger import logger

        logger.warning(f"Environment variable {key} is not set.")
    return value


def _get_optional_env(key: str, default: str = "") -> str:
    """Get an optional environment variable with a default."""
    return os.getenv(key, default)


# Telegram Configuration
TELEGRAM_BOT_TOKEN = _get_required_env("TELEGRAM_BOT_TOKEN")
TELEGRAM_SECRET_TOKEN = _get_required_env("TELEGRAM_SECRET_TOKEN")

# Google Cloud Configuration
GCP_PROJECT_ID = _get_required_env("GCP_PROJECT_ID")
GCP_REGION = _get_optional_env("GCP_REGION", "us-central1")

# External API Configuration
KHAYA_API_KEY = _get_required_env("KHAYA_API_KEY")

# TTS Tempo Configuration
_tts_tempo_str = _get_optional_env("TTS_TEMPO", "1.0")
try:
    TTS_TEMPO: float = float(_tts_tempo_str)
except ValueError:
    from app.utils.logger import logger

    logger.warning(f"Invalid TTS_TEMPO value: {_tts_tempo_str}, using default 1.0")
    TTS_TEMPO = 1.0

# Paths
BASE_DIR = Path(__file__).resolve().parents[1]
PROMPTS_DIR = BASE_DIR / "prompts"
