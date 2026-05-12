"""Tests for validators module."""

import pytest

from app.core.exceptions import ValidationError
from app.core.validators import (
    validate_chat_id,
    validate_youtube_url,
)


class TestValidateYoutubeUrl:
    def test_valid_standard_url(self):
        video_id = validate_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert video_id == "dQw4w9WgXcQ"

    def test_valid_short_url(self):
        video_id = validate_youtube_url("https://youtu.be/dQw4w9WgXcQ")
        assert video_id == "dQw4w9WgXcQ"

    def test_valid_shorts_url(self):
        video_id = validate_youtube_url("https://www.youtube.com/shorts/dQw4w9WgXcQ")
        assert video_id == "dQw4w9WgXcQ"

    def test_empty_url_raises_error(self):
        with pytest.raises(ValidationError, match="URL cannot be empty"):
            validate_youtube_url("")

    def test_none_url_raises_error(self):
        with pytest.raises(ValidationError, match="URL cannot be empty"):
            validate_youtube_url(None)  # type: ignore[arg-type]

    def test_invalid_url_raises_error(self):
        with pytest.raises(ValidationError, match="Invalid YouTube URL"):
            validate_youtube_url("https://www.google.com")

    def test_whitespace_trimmed(self):
        video_id = validate_youtube_url("  https://youtu.be/dQw4w9WgXcQ  ")
        assert video_id == "dQw4w9WgXcQ"


class TestValidateChatId:
    def test_valid_positive_chat_id(self):
        result = validate_chat_id(12345)
        assert result == 12345

    def test_zero_chat_id_raises_error(self):
        with pytest.raises(ValidationError, match="Chat ID cannot be zero"):
            validate_chat_id(0)

    def test_negative_chat_id_is_valid_for_groups(self):
        assert validate_chat_id(-123) == -123

    def test_non_integer_raises_error(self):
        with pytest.raises(ValidationError, match="Chat ID must be an integer"):
            validate_chat_id("12345")  # pyright: ignore[reportArgumentType]

    def test_float_raises_error(self):
        with pytest.raises(ValidationError, match="Chat ID must be an integer"):
            validate_chat_id(123.45)  # pyright: ignore[reportArgumentType]

    def test_bool_raises_error(self):
        with pytest.raises(ValidationError, match="Chat ID must be an integer"):
            validate_chat_id(True)
