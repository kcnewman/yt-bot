"""Transcript extraction service."""

import html
import json
import os
import random
import re
import time
from pathlib import Path
from typing import Any

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

from app.config import YOUTUBE_COOKIES_FILE, YOUTUBE_PROXY_URL
from app.core.constants import (
    TRANSCRIPT_INITIAL_DELAY,
    TRANSCRIPT_LANGUAGES,
    TRANSCRIPT_RETRIES,
)
from app.core.exceptions import TranscriptError
from app.utils.logger import logger

VTT_TAG_RE = re.compile(r"<[^>]+>")

_USER_AGENTS = [
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) "
        "Gecko/20100101 Firefox/127.0"
    ),
    (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/17.5 Safari/605.1.15"
    ),
    ("Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:127.0) Gecko/20100101 Firefox/127.0"),
]


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


def _build_http_headers() -> dict[str, str]:
    """Build realistic browser-like HTTP headers."""
    return {
        "User-Agent": random.choice(_USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


def _build_ydl_opts() -> Any:
    """Build yt-dlp options with browser-like headers and optional proxy/cookies."""
    opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "http_headers": _build_http_headers(),
        "extractor_args": {"youtube": {"skip": ["dash", "hls"]}},
    }

    if YOUTUBE_PROXY_URL:
        opts["proxy"] = YOUTUBE_PROXY_URL

    if YOUTUBE_COOKIES_FILE:
        cookies_path = Path(YOUTUBE_COOKIES_FILE)
        if cookies_path.exists():
            opts["cookiefile"] = str(cookies_path)
            logger.debug(f"Using cookies file: {YOUTUBE_COOKIES_FILE}")
        else:
            logger.warning(f"Cookies file not found: {YOUTUBE_COOKIES_FILE}")

    return opts


def _call_transcript_api(video_id: str) -> str | None:
    """Try youtube-transcript-api. Returns text or None on failure."""
    try:
        os.environ.pop("HTTP_PROXY", None)
        os.environ.pop("HTTPS_PROXY", None)
        if YOUTUBE_PROXY_URL:
            os.environ["HTTP_PROXY"] = YOUTUBE_PROXY_URL
            os.environ["HTTPS_PROXY"] = YOUTUBE_PROXY_URL

        api = YouTubeTranscriptApi()
        transcript_data = (
            api.list(video_id).find_transcript(TRANSCRIPT_LANGUAGES).fetch()
        )
        transcript_text = TextFormatter().format_transcript(transcript_data).strip()

        if transcript_text:
            logger.info(
                f"youtube-transcript-api: {len(transcript_text)} chars for {video_id}"
            )
            return transcript_text

        logger.warning(f"youtube-transcript-api returned empty for {video_id}")

    except Exception as error:
        logger.warning(f"youtube-transcript-api failed for {video_id}: {error}")

    finally:
        if YOUTUBE_PROXY_URL:
            os.environ.pop("HTTP_PROXY", None)
            os.environ.pop("HTTPS_PROXY", None)

    return None


def _fetch_with_ytdlp(video_id: str) -> str:
    """Fallback: extract English captions using yt-dlp with browser-like headers."""
    import yt_dlp

    ydl_opts = _build_ydl_opts()

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


def _attempt_fetch(video_id: str) -> str:
    """Try youtube-transcript-api, then fall back to yt-dlp."""
    result = _call_transcript_api(video_id)
    if result is not None:
        return result

    logger.info(f"Falling back to yt-dlp for {video_id}")
    return _fetch_with_ytdlp(video_id)


def fetch_captions(video_id: str | None) -> str:
    """
    Fetch English captions for a YouTube video with retry and backoff.

    Tries youtube-transcript-api first, then falls back to yt-dlp.
    Retries up to TRANSCRIPT_RETRIES times with exponential backoff.

    Args:
        video_id: The YouTube video ID.

    Returns:
        The transcript text.

    Raises:
        TranscriptError: If transcript extraction fails after all retries.
    """
    if not video_id or not video_id.strip():
        raise TranscriptError("Video ID cannot be empty.")

    clean_video_id = video_id.strip()

    for attempt in range(1, TRANSCRIPT_RETRIES + 1):
        try:
            return _attempt_fetch(clean_video_id)
        except TranscriptError:
            if attempt < TRANSCRIPT_RETRIES:
                delay = TRANSCRIPT_INITIAL_DELAY * (
                    2 ** (attempt - 1)
                ) + random.uniform(0, 0.5)
                logger.info(
                    f"Transcript extraction failed (attempt {attempt}/{TRANSCRIPT_RETRIES}), "
                    f"retrying in {delay:.1f}s..."
                )
                time.sleep(delay)
            else:
                raise

    raise TranscriptError("Could not extract transcript after all retries.")
