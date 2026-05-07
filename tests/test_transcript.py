"""Tests for transcript service."""

from unittest.mock import Mock, patch

import pytest

from app.core.exceptions import TranscriptError
from app.services.transcript import fetch_captions


class TestFetchCaptions:
    """Tests for fetch_captions function."""

    @patch("app.services.transcript.YouTubeTranscriptApi")
    def test_successful_caption_fetch(self, mock_api_class):
        """Should fetch and format captions successfully."""
        # Setup mock
        mock_api = Mock()
        mock_api_class.return_value = mock_api

        mock_transcript = Mock()
        mock_api.list.return_value.find_transcript.return_value = mock_transcript
        mock_transcript.fetch.return_value = [
            {"text": "Hello ", "start": 0, "duration": 1},
            {"text": "world", "start": 1, "duration": 1},
        ]

        with patch("app.services.transcript.TextFormatter") as mock_formatter:
            mock_formatter_instance = Mock()
            mock_formatter.return_value = mock_formatter_instance
            mock_formatter_instance.format_transcript.return_value = "Hello world"

            result = fetch_captions("dQw4w9WgXcQ")

            assert result == "Hello world"
            mock_api.list.assert_called_once_with("dQw4w9WgXcQ")

    def test_empty_video_id_raises_error(self):
        """Should raise TranscriptError for empty video ID."""
        with pytest.raises(TranscriptError, match="Video ID cannot be empty"):
            fetch_captions("")

    def test_none_video_id_raises_error(self):
        """Should raise TranscriptError for None video ID."""
        with pytest.raises(TranscriptError, match="Video ID cannot be empty"):
            fetch_captions(None)

    @patch("app.services.transcript.YouTubeTranscriptApi")
    def test_empty_transcript_raises_error(self, mock_api_class):
        """Should raise TranscriptError when transcript is empty."""
        # Setup mock to return empty transcript
        mock_api = Mock()
        mock_api_class.return_value = mock_api
        mock_transcript = Mock()
        mock_api.list.return_value.find_transcript.return_value = mock_transcript
        mock_transcript.fetch.return_value = []

        with patch("app.services.transcript.TextFormatter") as mock_formatter:
            mock_formatter_instance = Mock()
            mock_formatter.return_value = mock_formatter_instance
            mock_formatter_instance.format_transcript.return_value = ""

            with pytest.raises(TranscriptError, match="Transcript is empty"):
                fetch_captions("dQw4w9WgXcQ")

    @patch("app.services.transcript.YouTubeTranscriptApi")
    def test_api_error_raises_error(self, mock_api_class):
        """Should raise TranscriptError when API call fails."""
        mock_api = Mock()
        mock_api_class.return_value = mock_api
        mock_api.list.side_effect = Exception("API error")

        with pytest.raises(TranscriptError, match="Could not extract transcript"):
            fetch_captions("dQw4w9WgXcQ")

    @patch("app.services.transcript.YouTubeTranscriptApi")
    def test_whitespace_trimmed(self, mock_api_class):
        """Should trim whitespace from video ID."""
        mock_api = Mock()
        mock_api_class.return_value = mock_api
        mock_transcript = Mock()
        mock_api.list.return_value.find_transcript.return_value = mock_transcript
        mock_transcript.fetch.return_value = [
            {"text": "test", "start": 0, "duration": 1}
        ]

        with patch("app.services.transcript.TextFormatter") as mock_formatter:
            mock_formatter_instance = Mock()
            mock_formatter.return_value = mock_formatter_instance
            mock_formatter_instance.format_transcript.return_value = "test"

            fetch_captions("  dQw4w9WgXcQ  ")

            mock_api.list.assert_called_once_with("dQw4w9WgXcQ")
