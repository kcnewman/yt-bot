# Telegram API send functions
import requests

from app.config import TELEGRAM_BOT_TOKEN
from app.utils.logger import logger


def send_text(chat_id: int, text: str):

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Telegram API error: {e}")


def send_audio():
    pass
