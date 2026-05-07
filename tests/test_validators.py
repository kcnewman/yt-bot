"""Tests for validators module."""

import pytest

from app.core.exceptions import ValidationError
from app.core.validators import (
    validate_chat_id,
    validate_text,
    validate_youtube_url,
)


class TestValidateYoutubeUrl:
    """Tests for validate_youtube_url function."""

    def test_valid_standard_url(self):
        """Should extract video ID from standard youtube.com URL."""
        video_id = validate_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert video_id == "dQw4w9WgXcQ"

    def test_valid_short_url(self):
        """Should extract video ID from youtu.be short URL."""
        video_id = validate_youtube_url("https://youtu.be/dQw4w9WgXcQ")
        assert video_id == "dQw4w9WgXcQ"

    def test_valid_shorts_url(self):
        """Should extract video ID from youtube shorts URL."""
        video_id = validate_youtube_url("https://www.youtube.com/shorts/dQw4w9WgXcQ")
        assert video_id == "dQw4w9WgXcQ"

    def test_empty_url_raises_error(self):
        """Should raise ValidationError for empty URL."""
        with pytest.raises(ValidationError, match="URL cannot be empty"):
            validate_youtube_url("")

    def test_none_url_raises_error(self):
        """Should raise ValidationError for None URL."""
        with pytest.raises(ValidationError, match="URL cannot be empty"):
            validate_youtube_url(None)

    def test_invalid_url_raises_error(self):
        """Should raise ValidationError for invalid URL."""
        with pytest.raises(ValidationError, match="Invalid YouTube URL"):
            validate_youtube_url("https://www.google.com")

    def test_whitespace_trimmed(self):
        """Should handle URLs with surrounding whitespace."""
        video_id = validate_youtube_url("  https://youtu.be/dQw4w9WgXcQ  ")
        assert video_id == "dQw4w9WgXcQ"


class TestValidateText:
    """Tests for validate_text function."""

    def test_valid_text(self):
        """Should return cleaned text."""
        result = validate_text("hello world")
        assert result == "hello world"

    def test_text_with_whitespace_trimmed(self):
        """Should trim whitespace."""
        result = validate_text("  hello world  ")
        assert result == "hello world"

    def test_empty_text_raises_error(self):
        """Should raise ValidationError for empty text."""
        with pytest.raises(ValidationError, match="Text cannot be empty"):
            validate_text("")

    def test_empty_text_allowed_when_flag_set(self):
        """Should allow empty text when allow_empty=True."""
        result = validate_text("", allow_empty=True)
        assert result == ""

    def test_whitespace_only_raises_error(self):
        """Should raise error for whitespace-only text."""
        with pytest.raises(ValidationError, match="Text cannot be empty"):
            validate_text("   ")

    def test_non_string_raises_error(self):
        """Should raise ValidationError for non-string input."""
        with pytest.raises(ValidationError, match="Text must be a string"):
            validate_text(123)


class TestValidateChatId:
    """Tests for validate_chat_id function."""

    def test_valid_positive_chat_id(self):
        """Should accept positive integer chat ID."""
        result = validate_chat_id(12345)
        assert result == 12345

    def test_zero_chat_id_raises_error(self):
        """Should reject zero chat ID."""
        with pytest.raises(ValidationError, match="Chat ID must be positive"):
            validate_chat_id(0)

    def test_negative_chat_id_raises_error(self):
        """Should reject negative chat ID."""
        with pytest.raises(ValidationError, match="Chat ID must be positive"):
            validate_chat_id(-123)

    def test_non_integer_raises_error(self):
        """Should raise ValidationError for non-integer input."""
        with pytest.raises(ValidationError, match="Chat ID must be an integer"):
            validate_chat_id("12345")

    def test_float_raises_error(self):
        """Should raise ValidationError for float input."""
        with pytest.raises(ValidationError, match="Chat ID must be an integer"):
            validate_chat_id(123.45)
