# Environment variable loading
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_SECRET_TOKEN = os.getenv("TELEGRAM_SECRET_TOKEN")

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_REGION = os.getenv("GCP_REGION")

KHAYA_API_KEY = os.getenv("KHAYA_API_KEY")
_tts_tempo_str = os.getenv("TTS_TEMPO", "1.0")
TTS_TEMPO: float = float(_tts_tempo_str) if _tts_tempo_str else 1.0

BASE_DIR = Path(__file__).resolve().parents[1]
PROMPTS_DIR = BASE_DIR / "prompts"
