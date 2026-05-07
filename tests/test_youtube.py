"""Tests for YouTube utilities."""

import pytest

from app.utils.youtube import extract_video_id


class TestExtractVideoId:
    """Tests for extract_video_id function."""

    def test_standard_youtube_url(self):
        """Should extract video ID from standard URL."""
        video_id = extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert video_id == "dQw4w9WgXcQ"

    def test_youtube_short_url(self):
        """Should extract video ID from youtu.be short URL."""
        video_id = extract_video_id("https://youtu.be/dQw4w9WgXcQ")
        assert video_id == "dQw4w9WgXcQ"

    def test_youtube_shorts_url(self):
        """Should extract video ID from YouTube Shorts URL."""
        video_id = extract_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ")
        assert video_id == "dQw4w9WgXcQ"

    def test_youtube_embed_url(self):
        """Should extract video ID from embed URL."""
        video_id = extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ")
        assert video_id == "dQw4w9WgXcQ"

    def test_url_without_protocol(self):
        """Should extract video ID from URL without protocol."""
        video_id = extract_video_id("youtu.be/dQw4w9WgXcQ")
        assert video_id == "dQw4w9WgXcQ"

    def test_empty_url_returns_none(self):
        """Should return None for empty URL."""
        video_id = extract_video_id("")
        assert video_id is None

    def test_none_url_returns_none(self):
        """Should return None for None URL."""
        video_id = extract_video_id(None)
        assert video_id is None

    def test_invalid_url_returns_none(self):
        """Should return None for non-YouTube URL."""
        video_id = extract_video_id("https://www.google.com")
        assert video_id is None

    def test_url_with_extra_parameters(self):
        """Should extract video ID from URL with extra parameters."""
        video_id = extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10s")
        assert video_id == "dQw4w9WgXcQ"
