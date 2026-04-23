# Telegram API send functions
import requests
from requests.exceptions import RequestException

from app.config import TELEGRAM_BOT_TOKEN
from app.utils.logger import logger


def send_text(chat_id: int, text: str) -> int | None:
    """
    Sends a text message.
    Returns the message_id so it can be edited/deleted later.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()

        data = response.json()
        return data.get("result", {}).get("message_id")

    except RequestException as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return None


def edit_text(chat_id: int, message_id: int | None, new_text: str):
    """
    Overwrites an existing message with new text.
    """
    if not message_id:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageText"
    payload = {"chat_id": chat_id, "message_id": message_id, "text": new_text}

    try:
        requests.post(url, json=payload)
    except Exception as e:
        logger.error(f"Failed to edit Telegram message: {e}")


def delete_message(chat_id: int, message_id: int | None):
    """
    Permanently deletes a message from the chat.
    """
    if not message_id:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteMessage"
    payload = {"chat_id": chat_id, "message_id": message_id}

    try:
        requests.post(url, json=payload)
    except Exception as e:
        logger.error(f"Failed to delete Telegram message: {e}")
