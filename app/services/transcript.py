# Caption fetch + Whisper fallback
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

from app.utils.logger import logger


def fetch_captions(video_id: str) -> str | None:
    """
    Fetch captions added to the video if available.
    Returns transcript as a string, None if it fails
    """
    ytt_api = YouTubeTranscriptApi()
    try:
        transcript = ytt_api.list(video_id).find_transcript(["en"])
        transcript_data = transcript.fetch()
        formatter = TextFormatter()
        transcript_text = formatter.format_transcript(transcript_data)

        logger.info(f"Extracted {len(transcript_text)} characters of text.")

        return transcript_text
    except Exception as e:
        logger.warning(f"Could not fetch text captions for {video_id}: {e}")
        return None
