from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

from app.utils.logger import logger

TRANSCRIPT_LANGUAGES = ["en"]


def _format_transcript_text(video_id: str, api: YouTubeTranscriptApi) -> str | None:
    """Fetch and format transcript text for a video."""
    transcript = api.list(video_id).find_transcript(TRANSCRIPT_LANGUAGES)
    transcript_data = transcript.fetch()
    transcript_text = TextFormatter().format_transcript(transcript_data).strip()
    return transcript_text or None


def fetch_captions(video_id: str) -> str | None:
    """Fetch English captions for a video."""
    if not video_id or not video_id.strip():
        return None

    api = YouTubeTranscriptApi()

    try:
        transcript_text = _format_transcript_text(video_id.strip(), api)
        if not transcript_text:
            logger.warning(f"Transcript is empty for video: {video_id}")
            return None

        logger.info(f"Extracted {len(transcript_text)} characters of text.")
        return transcript_text
    except Exception as error:
        logger.warning(f"Could not fetch text captions for {video_id}: {error}")
        return None
