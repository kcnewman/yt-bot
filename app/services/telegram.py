"""Telegram bot API client."""

import requests
from requests.exceptions import RequestException

from app.config import TELEGRAM_BOT_TOKEN
from app.core.constants import TELEGRAM_API_BASE, TIMEOUT_SECONDS
from app.utils.logger import logger


def _build_url(method: str) -> str:
    """Build the Telegram Bot API endpoint URL."""
    return f"{TELEGRAM_API_BASE}/bot{TELEGRAM_BOT_TOKEN}/{method}"


def send_text(chat_id: int, text: str) -> int | None:
    """
    Send a text message to a chat.

    Args:
        chat_id: The Telegram chat ID.
        text: The message text.

    Returns:
        The message ID if successful, None otherwise.
    """
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not configured.")
        return None

    if not text or not text.strip():
        logger.warning("Cannot send empty text message.")
        return None

    url = _build_url("sendMessage")
    payload = {"chat_id": chat_id, "text": text.strip()}

    try:
        response = requests.post(url, json=payload, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()

        data = response.json()
        if not data.get("ok", False):
            logger.error(f"Telegram API error: {data}")
            return None

        message_id = data.get("result", {}).get("message_id")
        logger.info(f"Sent text message to chat {chat_id}, message_id: {message_id}")
        return message_id

    except (RequestException, ValueError) as error:
        logger.error(f"Failed to send text message to chat {chat_id}: {error}")
        return None
    except Exception as error:
        logger.error(f"Unexpected error sending text message: {error}", exc_info=True)
        return None


def edit_text(chat_id: int, message_id: int | None, new_text: str) -> bool:
    """
    Edit an existing text message.

    Args:
        chat_id: The Telegram chat ID.
        message_id: The message ID to edit.
        new_text: The new message text.

    Returns:
        True if successful, False otherwise.
    """
    if not message_id:
        logger.warning("Cannot edit message without message_id.")
        return False

    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not configured.")
        return False

    if not new_text or not new_text.strip():
        logger.warning("Cannot edit message with empty text.")
        return False

    url = _build_url("editMessageText")
    payload = {"chat_id": chat_id, "message_id": message_id, "text": new_text.strip()}

    try:
        response = requests.post(url, json=payload, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        logger.info(f"Edited message {message_id} in chat {chat_id}")
        return True
    except RequestException as error:
        logger.error(f"Failed to edit message {message_id}: {error}")
        return False
    except Exception as error:
        logger.error(f"Unexpected error editing message: {error}", exc_info=True)
        return False


def delete_message(chat_id: int, message_id: int | None) -> bool:
    """
    Delete a message from a chat.

    Args:
        chat_id: The Telegram chat ID.
        message_id: The message ID to delete.

    Returns:
        True if successful, False otherwise.
    """
    if not message_id:
        logger.warning("Cannot delete message without message_id.")
        return False

    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not configured.")
        return False

    url = _build_url("deleteMessage")
    payload = {"chat_id": chat_id, "message_id": message_id}

    try:
        response = requests.post(url, json=payload, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        logger.info(f"Deleted message {message_id} from chat {chat_id}")
        return True
    except RequestException as error:
        logger.error(f"Failed to delete message {message_id}: {error}")
        return False
    except Exception as error:
        logger.error(f"Unexpected error deleting message: {error}", exc_info=True)
        return False


def send_audio(chat_id: int, audio_path: str) -> bool:
    """
    Send an audio file as a Telegram voice note.

    Args:
        chat_id: The Telegram chat ID.
        audio_path: Path to the audio file.

    Returns:
        True if successful, False otherwise.
    """
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not configured.")
        return False

    if not audio_path or not audio_path.strip():
        logger.warning("Cannot send audio without file path.")
        return False

    url = _build_url("sendVoice")

    try:
        with open(audio_path.strip(), "rb") as audio_file:
            files = {"voice": audio_file}
            data = {"chat_id": chat_id}
            response = requests.post(
                url,
                data=data,
                files=files,
                timeout=TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            logger.info(f"Sent audio to chat {chat_id}")
            return True

    except RequestException as error:
        logger.error(f"Failed to read audio file {audio_path}: {error}")
        return False
    except Exception as error:
        logger.error(f"Unexpected error sending audio: {error}", exc_info=True)
        return False
