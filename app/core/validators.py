"""Input validators for the application."""

from app.core.exceptions import ValidationError
from app.utils.youtube import extract_video_id


def validate_youtube_url(url: str) -> str:
    """
    Validate a YouTube URL and return the video ID.

    Args:
        url: The URL to validate.

    Returns:
        The video ID if valid.

    Raises:
        ValidationError: If the URL is invalid.
    """
    if not url or not url.strip():
        raise ValidationError("URL cannot be empty.")

    video_id = extract_video_id(url.strip())
    if not video_id:
        raise ValidationError("Invalid YouTube URL provided.")

    return video_id


def validate_text(text: str, allow_empty: bool = False) -> str:
    """
    Validate and clean text input.

    Args:
        text: The text to validate.
        allow_empty: Whether to allow empty strings.

    Returns:
        The cleaned text.

    Raises:
        ValidationError: If validation fails.
    """
    if not isinstance(text, str):
        raise ValidationError("Text must be a string.")

    cleaned = text.strip()

    if not cleaned and not allow_empty:
        raise ValidationError("Text cannot be empty.")

    return cleaned


def validate_chat_id(chat_id: int) -> int:
    """
    Validate a chat ID.

    Args:
        chat_id: The chat ID to validate.

    Returns:
        The chat ID if valid.

    Raises:
        ValidationError: If validation fails.
    """
    if not isinstance(chat_id, int) or isinstance(chat_id, bool):
        raise ValidationError("Chat ID must be an integer.")

    if chat_id == 0:
        raise ValidationError("Chat ID cannot be zero.")

    return chat_id
