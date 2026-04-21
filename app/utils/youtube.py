# URL validation, video ID extraction
import re

from app.utils.logger import logger


def extract_video_id(url: str) -> str | None:
    """
    Returns the 11-character ID if valid, or None if invalid.
    """
    youtube_regex = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})"
    match = re.search(youtube_regex, url)

    if match:
        video_id = match.group(1)
        logger.info(f"Valid URL. Extracted ID: {video_id}")
        return video_id
    else:
        logger.warning("Invalid or non-Youtube URL provided")
        return None


def is_valid_url(url: str) -> bool:
    """
    Helper function to return true or false.
    """
    return extract_video_id(url) is not None
