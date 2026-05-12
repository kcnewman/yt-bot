"""YouTube URL parsing utilities."""

import re

from app.utils.logger import logger

YOUTUBE_REGEX = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})"


def extract_video_id(url: str | None) -> str | None:
    """
    Extract the YouTube video ID from a URL.

    Supports various YouTube URL formats:
    - Standard: youtube.com/watch?v=...
    - Short: youtu.be/...
    - Shorts: youtube.com/shorts/...
    - Embedded: youtube.com/embed/...

    Args:
        url: The YouTube URL.

    Returns:
        The 11-character video ID, or None if invalid.
    """
    if not url or not url.strip():
        return None

    match = re.search(YOUTUBE_REGEX, url)
    if match:
        video_id = match.group(1)
        logger.debug(f"Extracted YouTube video ID: {video_id}")
        return video_id

    logger.debug(f"URL is not a valid YouTube URL: {url}")
    return None
