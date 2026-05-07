import requests
from requests.exceptions import RequestException

from app.config import TELEGRAM_BOT_TOKEN
from app.utils.logger import logger

REQUEST_TIMEOUT_SECONDS = 30


def _method_url(method: str) -> str:
    """Build Telegram Bot API URL for a method."""
    return f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"


def send_text(chat_id: int, text: str) -> int | None:
    """Send a text message and return its Telegram message id."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is missing")
        return None

    url = _method_url("sendMessage")
    payload = {"chat_id": chat_id, "text": text}

    try:
        response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()

        data = response.json()
        if not data.get("ok", False):
            logger.error(f"Telegram sendMessage failed: {data}")
            return None

        return data.get("result", {}).get("message_id")

    except (RequestException, ValueError) as error:
        logger.error(f"Failed to send Telegram message: {error}")
        return None


def edit_text(chat_id: int, message_id: int | None, new_text: str) -> None:
    """Edit an existing text message."""
    if not message_id:
        return

    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is missing")
        return

    url = _method_url("editMessageText")
    payload = {"chat_id": chat_id, "message_id": message_id, "text": new_text}

    try:
        response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except RequestException as error:
        logger.error(f"Failed to edit Telegram message: {error}")


def delete_message(chat_id: int, message_id: int | None) -> None:
    """Delete a message from chat."""
    if not message_id:
        return

    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is missing")
        return

    url = _method_url("deleteMessage")
    payload = {"chat_id": chat_id, "message_id": message_id}

    try:
        response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except RequestException as error:
        logger.error(f"Failed to delete Telegram message: {error}")


def send_audio(chat_id: int, audio_path: str) -> None:
    """Upload and send an audio file as Telegram voice note."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is missing")
        return

    url = _method_url("sendVoice")

    try:
        with open(audio_path, "rb") as audio_file:
            files = {"voice": audio_file}
            data = {"chat_id": chat_id}
            response = requests.post(
                url,
                data=data,
                files=files,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
    except (OSError, RequestException) as error:
        logger.error(f"Failed to send Telegram voice note: {error}")
