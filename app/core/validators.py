"""Input validators for the application."""

from app.core.exceptions import ValidationError
from app.utils.youtube import extract_video_id


def validate_youtube_url(url: str | None) -> str:
    if not url or not url.strip():
        raise ValidationError("URL cannot be empty.")

    video_id = extract_video_id(url.strip())
    if not video_id:
        raise ValidationError("Invalid YouTube URL provided.")

    return video_id


def validate_chat_id(chat_id: int) -> int:
    if type(chat_id) is not int:
        raise ValidationError("Chat ID must be an integer.")

    if chat_id == 0:
        raise ValidationError("Chat ID cannot be zero.")

    return chat_id
