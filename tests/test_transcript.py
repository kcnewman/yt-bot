"""Tests for transcript service."""

from unittest.mock import Mock, patch

import pytest

from app.core.exceptions import TranscriptError
from app.services.transcript import (
    _fetch_with_ytdlp,
    _parse_json_subs,
    _parse_vtt,
    fetch_captions,
)


class TestSubtitleParsers:
    """Tests for VTT and JSON subtitle parsers."""

    def test_parse_vtt_removes_headers_timestamps_and_tags(self):
        vtt = """WEBVTT
Kind: captions
Language: en

00:00:00.000 --> 00:00:02.000
Hello <c>world</c>

00:00:02.500 --> 00:00:04.000
Foo bar"""
        assert _parse_vtt(vtt) == "Hello world Foo bar"

    def test_parse_vtt_empty(self):
        assert _parse_vtt("") == ""

    def test_parse_vtt_handles_html_entities(self):
        vtt = "It&apos;s a &quot;test&quot; &amp; more"
        assert _parse_vtt(vtt) == "It's a \"test\" & more"

    def test_parse_json_subs(self):
        data = '{"events": [{"segs": [{"utf8": "Hello "}, {"utf8": "world"}]}]}'
        assert _parse_json_subs(data) == "Hello world"

    def test_parse_json_subs_empty(self):
        assert _parse_json_subs("{}") == ""

    def test_parse_json_subs_missing_segs(self):
        data = '{"events": [{"tStartMs": 0}]}'
        assert _parse_json_subs(data) == ""


class TestFetchWithYtdlp:
    """Tests for yt-dlp fallback function."""

    @patch("yt_dlp.YoutubeDL")
    def test_fallback_success_vtt(self, mock_ydl_class):
        """Should extract VTT subtitles via yt-dlp."""
        mock_response = Mock()
        mock_response.read.return_value = (
            b"WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nHello world"
        )

        mock_ydl = Mock()
        mock_ydl.extract_info.return_value = {
            "subtitles": {
                "en": [{"ext": "vtt", "url": "http://example.com/sub.vtt"}]
            }
        }
        mock_ydl.urlopen.return_value = mock_response
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        result = _fetch_with_ytdlp("test123")

        assert result == "Hello world"
        mock_ydl.extract_info.assert_called_once_with("test123", download=False)

    @patch("yt_dlp.YoutubeDL")
    def test_fallback_success_json(self, mock_ydl_class):
        """Should extract JSON (srv3) subtitles via yt-dlp."""
        mock_response = Mock()
        mock_response.read.return_value = (
            b'{"events": [{"segs": [{"utf8": "Hello "}]},'
            b'{"segs": [{"utf8": "world"}]}]}'
        )

        mock_ydl = Mock()
        mock_ydl.extract_info.return_value = {
            "subtitles": {
                "en": [{"ext": "srv3", "url": "http://example.com/sub.srv3"}]
            }
        }
        mock_ydl.urlopen.return_value = mock_response
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        result = _fetch_with_ytdlp("test123")

        assert result == "Hello world"

    @patch("yt_dlp.YoutubeDL")
    def test_fallback_favors_manual_over_auto_captions(self, mock_ydl_class):
        """Should prefer manual subtitles over automatic captions."""
        mock_response = Mock()
        mock_response.read.return_value = (
            b"WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nManual captions"
        )

        mock_ydl = Mock()
        mock_ydl.extract_info.return_value = {
            "subtitles": {
                "en": [{"ext": "vtt", "url": "http://example.com/manual.vtt"}]
            },
            "automatic_captions": {
                "en": [{"ext": "vtt", "url": "http://example.com/auto.vtt"}]
            },
        }
        mock_ydl.urlopen.return_value = mock_response
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        result = _fetch_with_ytdlp("test123")

        assert result == "Manual captions"
        mock_ydl.urlopen.assert_called_once_with("http://example.com/manual.vtt")

    @patch("yt_dlp.YoutubeDL")
    def test_fallback_raises_error_when_no_captions(self, mock_ydl_class):
        """Should raise TranscriptError when no captions available."""
        mock_ydl = Mock()
        mock_ydl.extract_info.return_value = {
            "subtitles": {}, "automatic_captions": {}
        }
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        with pytest.raises(TranscriptError, match="No captions found via yt-dlp"):
            _fetch_with_ytdlp("test123")


class TestFetchCaptions:
    """Tests for fetch_captions function (primary + fallback)."""

    @patch("app.services.transcript.YouTubeTranscriptApi")
    def test_primary_path_succeeds(self, mock_api_class):
        """Should use youtube-transcript-api result directly."""
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

    @patch("app.services.transcript._fetch_with_ytdlp")
    @patch("app.services.transcript.YouTubeTranscriptApi")
    def test_fallback_when_api_returns_empty(self, mock_api_class, mock_fallback):
        """Should try yt-dlp when youtube-transcript-api returns empty."""
        mock_api = Mock()
        mock_api_class.return_value = mock_api
        mock_transcript = Mock()
        mock_api.list.return_value.find_transcript.return_value = mock_transcript
        mock_transcript.fetch.return_value = []

        with patch("app.services.transcript.TextFormatter") as mock_formatter:
            mock_formatter_instance = Mock()
            mock_formatter.return_value = mock_formatter_instance
            mock_formatter_instance.format_transcript.return_value = ""

            mock_fallback.return_value = "Fallback transcript"

            result = fetch_captions("dQw4w9WgXcQ")

        assert result == "Fallback transcript"
        mock_fallback.assert_called_once_with("dQw4w9WgXcQ")

    @patch("app.services.transcript._fetch_with_ytdlp")
    @patch("app.services.transcript.YouTubeTranscriptApi")
    def test_fallback_when_api_raises(self, mock_api_class, mock_fallback):
        """Should try yt-dlp when youtube-transcript-api raises."""
        mock_api = Mock()
        mock_api_class.return_value = mock_api
        mock_api.list.side_effect = Exception("API error")

        mock_fallback.return_value = "Fallback transcript"

        result = fetch_captions("dQw4w9WgXcQ")

        assert result == "Fallback transcript"
        mock_fallback.assert_called_once_with("dQw4w9WgXcQ")

    @patch("app.services.transcript._fetch_with_ytdlp")
    @patch("app.services.transcript.YouTubeTranscriptApi")
    def test_both_fail_raises_error(self, mock_api_class, mock_fallback):
        """Should raise TranscriptError when both methods fail."""
        mock_api = Mock()
        mock_api_class.return_value = mock_api
        mock_api.list.side_effect = Exception("API error")

        mock_fallback.side_effect = TranscriptError("fallback also failed")

        with pytest.raises(TranscriptError, match="fallback also failed"):
            fetch_captions("dQw4w9WgXcQ")

    @patch("app.services.transcript._fetch_with_ytdlp")
    @patch("app.services.transcript.YouTubeTranscriptApi")
    def test_whitespace_still_trimmed_for_both_methods(self, mock_api_class, mock_fallback):
        """Should trim whitespace for both API and fallback."""
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
