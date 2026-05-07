"""Transcript extraction service."""

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

from app.core.constants import TRANSCRIPT_LANGUAGES
from app.core.exceptions import TranscriptError
from app.utils.logger import logger


def fetch_captions(video_id: str) -> str:
    """
    Fetch English captions for a YouTube video.

    Args:
        video_id: The YouTube video ID.

    Returns:
        The transcript text.

    Raises:
        TranscriptError: If transcript extraction fails.
    """
    if not video_id or not video_id.strip():
        raise TranscriptError("Video ID cannot be empty.")

    clean_video_id = video_id.strip()
    api = YouTubeTranscriptApi()

    try:
        transcript_data = (
            api.list(clean_video_id).find_transcript(TRANSCRIPT_LANGUAGES).fetch()
        )
        transcript_text = TextFormatter().format_transcript(transcript_data).strip()

        if not transcript_text:
            raise TranscriptError(f"Transcript is empty for video: {clean_video_id}")

        logger.info(
            f"Successfully extracted {len(transcript_text)} characters of transcript."
        )
        return transcript_text

    except TranscriptError:
        raise
    except Exception as error:
        logger.error(f"Failed to fetch transcript for {clean_video_id}: {error}")
        raise TranscriptError(f"Could not extract transcript: {error}")
