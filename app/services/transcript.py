"""Transcript extraction service."""

import html
import json
import re
from typing import Any

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

from app.core.constants import TRANSCRIPT_LANGUAGES
from app.core.exceptions import TranscriptError
from app.utils.logger import logger

VTT_TAG_RE = re.compile(r"<[^>]+>")


def _parse_vtt(text: str) -> str:
    """Strip WebVTT / SRT formatting and return plain text."""
    lines: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if (
            line.startswith("WEBVTT")
            or line.startswith("Kind:")
            or line.startswith("Language:")
        ):
            continue
        if "-->" in line:
            continue
        line = html.unescape(line)
        line = VTT_TAG_RE.sub("", line)
        lines.append(line)
    return " ".join(lines).strip()


def _parse_json_subs(text: str) -> str:
    """Parse YouTube JSON subtitle format (json3 / srv3 / srv2)."""
    data = json.loads(text)
    parts: list[str] = []

    events = data if isinstance(data, list) else data.get("events", [])
    for event in events:
        segs = event.get("segs", []) if isinstance(event, dict) else []
        for seg in segs:
            utf8 = seg.get("utf8", "") if isinstance(seg, dict) else ""
            if utf8:
                parts.append(utf8.strip())

    return " ".join(parts).strip()


def _fetch_with_ytdlp(video_id: str) -> str:
    """Fallback: extract English captions using yt-dlp."""
    import yt_dlp

    ydl_opts: Any = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_id, download=False)

        for source_key in ("subtitles", "automatic_captions"):
            subs = info.get(source_key, {}).get("en", [])
            if not subs:
                continue

            preferred = ("vtt", "srv3", "json3", "ttml", "srv2", "srv1")
            sub_url = next(
                (s["url"] for s in subs if s.get("ext") in preferred and s.get("url")),
                None,
            )
            if not sub_url:
                sub_url = subs[0].get("url")

            if not sub_url:
                continue

            response = ydl.urlopen(sub_url)
            raw = response.read().decode("utf-8", errors="replace")

            text = (
                _parse_json_subs(raw)
                if raw.strip().startswith(("{", "["))
                else _parse_vtt(raw)
            )

            if text:
                fmt = "json" if raw.strip().startswith(("{", "[")) else "vtt"
                logger.info(
                    f"yt-dlp extracted transcript from {source_key} (format={fmt}, "
                    f"{len(text)} chars)"
                )
                return text

    raise TranscriptError("No captions found via yt-dlp fallback.")


def fetch_captions(video_id: str) -> str:
    """
    Fetch English captions for a YouTube video.

    Tries youtube-transcript-api first, then falls back to yt-dlp.

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

    # Primary path: youtube-transcript-api
    try:
        transcript_data = (
            api.list(clean_video_id).find_transcript(TRANSCRIPT_LANGUAGES).fetch()
        )
        transcript_text = TextFormatter().format_transcript(transcript_data).strip()

        if transcript_text:
            logger.info(
                f"youtube-transcript-api: {len(transcript_text)} chars for {clean_video_id}"
            )
            return transcript_text

        logger.warning(f"youtube-transcript-api returned empty for {clean_video_id}")

    except Exception as error:
        logger.warning(f"youtube-transcript-api failed for {clean_video_id}: {error}")

    # Fallback: yt-dlp
    logger.info(f"Falling back to yt-dlp for {clean_video_id}")
    try:
        return _fetch_with_ytdlp(clean_video_id)
    except TranscriptError:
        raise
    except Exception as error:
        logger.error(f"yt-dlp fallback also failed for {clean_video_id}: {error}")
        raise TranscriptError(f"Could not extract transcript: {error}") from error
