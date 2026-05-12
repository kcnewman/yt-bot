"""Application configuration."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Local development convenience. In production, real environment variables win.
load_dotenv(override=False)


def _get_env(key: str, default: str | None = None) -> str | None:
    value = os.getenv(key)
    if value is None or not value.strip():
        return default
    return value.strip()


def _get_required_env(key: str) -> str | None:
    """Return an environment variable and warn when it is missing."""
    value = _get_env(key)
    if not value:
        from app.utils.logger import logger

        logger.warning(f"Environment variable {key} is not set.")
    return value


def _get_optional_env(key: str, default: str = "") -> str:
    """Return an optional environment variable with a default."""
    return _get_env(key, default) or ""


def _get_bool_env(key: str, default: bool = False) -> bool:
    """Return a boolean environment variable."""
    value = _get_env(key)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


# Runtime Configuration
APP_ENV = _get_optional_env("APP_ENV", "development")
IS_PRODUCTION = APP_ENV.lower() == "production"

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

# Pipeline Configuration
_pipeline_workers_str = _get_optional_env("PIPELINE_WORKERS", "2")
try:
    PIPELINE_WORKERS: int = max(1, int(_pipeline_workers_str))
except ValueError:
    from app.utils.logger import logger

    logger.warning(
        f"Invalid PIPELINE_WORKERS value: {_pipeline_workers_str}, using default 2"
    )
    PIPELINE_WORKERS = 2

# Paths
BASE_DIR = Path(__file__).resolve().parents[1]
PROMPTS_DIR = BASE_DIR / "prompts"

# Database Configuration
_database_url = _get_env("DATABASE_URL")
DATABASE_URL = _database_url or f"sqlite:///{BASE_DIR / 'data' / 'yt_bot.db'}"
AUTO_INIT_DB = _get_bool_env("AUTO_INIT_DB", default=not IS_PRODUCTION)


def _validate_production_config() -> None:
    """Fail fast when production starts without required secrets or services."""
    if not IS_PRODUCTION:
        return

    missing = [
        key
        for key, value in {
            "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
            "TELEGRAM_SECRET_TOKEN": TELEGRAM_SECRET_TOKEN,
            "GCP_PROJECT_ID": GCP_PROJECT_ID,
            "KHAYA_API_KEY": KHAYA_API_KEY,
            "DATABASE_URL": _database_url,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(
            "Missing required production environment variables: "
            + ", ".join(sorted(missing))
        )


_validate_production_config()
