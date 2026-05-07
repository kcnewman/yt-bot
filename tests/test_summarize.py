"""Tests for summarization service."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from app.core.exceptions import SummarizationError
from app.services.summarize import (
    _count_words,
    _should_rewrite,
    summarize_transcript,
)


class TestCountWords:
    """Tests for _count_words helper function."""

    def test_count_simple_sentence(self):
        """Should count words in simple sentence."""
        count = _count_words("hello world test")
        assert count == 3

    def test_count_with_punctuation(self):
        """Should count words with punctuation."""
        count = _count_words("Hello, world! How are you?")
        assert count == 5

    def test_count_empty_string(self):
        """Should return 0 for empty string."""
        count = _count_words("")
        assert count == 0

    def test_count_with_contractions(self):
        """Should handle contractions."""
        count = _count_words("don't won't can't")
        assert count == 3


class TestShouldRewrite:
    """Tests for _should_rewrite helper function."""

    def test_no_rewrite_if_summary_is_short(self):
        """Should not rewrite if summary is short."""
        summary = "short summary"
        source_words = 100
        assert not _should_rewrite(summary, source_words)

    def test_rewrite_if_summary_too_long(self):
        """Should rewrite if summary length equals or exceeds source."""
        summary = "a " * 50  # 50 words
        source_words = 40
        assert _should_rewrite(summary, source_words)

    def test_rewrite_if_too_complex(self):
        """Should rewrite if contains too many long words."""
        # Create a summary with >10% words having length >= 11
        summary = "The extraordinarily comprehensive philosophical examination necessitates meticulous consideration"
        source_words = 100
        assert _should_rewrite(summary, source_words)

    def test_no_rewrite_if_simple(self):
        """Should not rewrite if summary is simple."""
        summary = "This is a simple and clear summary of the main points."
        source_words = 100
        assert not _should_rewrite(summary, source_words)


class TestSummarizeTranscript:
    """Tests for summarize_transcript function."""

    def test_empty_transcript_raises_error(self):
        """Should raise SummarizationError for empty transcript."""
        with pytest.raises(SummarizationError, match="Transcript cannot be empty"):
            summarize_transcript("")

    def test_none_transcript_raises_error(self):
        """Should raise SummarizationError for None transcript."""
        with pytest.raises(SummarizationError, match="Transcript cannot be empty"):
            summarize_transcript(None)

    @patch("app.services.summarize.load_prompt")
    @patch("app.services.summarize.client")
    def test_successful_summarization(self, mock_client, mock_load_prompt):
        """Should generate summary successfully."""
        # Setup mocks
        mock_load_prompt.return_value = "Summarize: {transcript}"
        mock_response = Mock()
        mock_response.text = "This is a summary"
        mock_client.models.generate_content.return_value = mock_response

        transcript = "This is a long transcript about topics. " * 10

        result = summarize_transcript(transcript)

        assert result == "This is a summary"
        mock_load_prompt.assert_called()

    @patch("app.services.summarize.load_prompt")
    @patch("app.services.summarize.client", None)
    def test_no_client_raises_error(self, mock_load_prompt):
        """Should raise error when client is not available."""
        mock_load_prompt.return_value = "Summarize: {transcript}"
        transcript = "test transcript"

        with pytest.raises(SummarizationError, match="GenAI client is not available"):
            summarize_transcript(transcript)

    @patch("app.services.summarize.load_prompt")
    @patch("app.services.summarize.client")
    def test_empty_model_response_raises_error(self, mock_client, mock_load_prompt):
        """Should raise error when model returns empty response."""
        mock_load_prompt.return_value = "Summarize: {transcript}"
        mock_response = Mock()
        mock_response.text = ""
        mock_client.models.generate_content.return_value = mock_response

        transcript = "test transcript content here"

        with pytest.raises(SummarizationError, match="Model returned empty response"):
            summarize_transcript(transcript)

    @patch("app.services.summarize.load_prompt")
    @patch("app.services.summarize.client")
    def test_api_error_raises_error(self, mock_client, mock_load_prompt):
        """Should raise error when API call fails."""
        mock_load_prompt.return_value = "Summarize: {transcript}"
        mock_client.models.generate_content.side_effect = Exception("API error")

        transcript = "test transcript content"

        with pytest.raises(SummarizationError, match="LLM generation failed"):
            summarize_transcript(transcript)

    @patch("app.services.summarize.load_prompt")
    @patch("app.services.summarize.client")
    def test_missing_template_value_raises_error(self, mock_client, mock_load_prompt):
        """Should raise error when template has missing values."""
        mock_load_prompt.return_value = "Summarize: {transcript} for {missing}"
        transcript = "test content"

        with pytest.raises(SummarizationError, match="Missing template value"):
            summarize_transcript(transcript)

    @patch("app.services.summarize.load_prompt")
    @patch("app.services.summarize.client")
    def test_custom_content_type(self, mock_client, mock_load_prompt):
        """Should use content_type parameter."""
        mock_load_prompt.return_value = "Summarize {content_type}: {transcript}"
        mock_response = Mock()
        mock_response.text = "Short summary only"
        mock_client.models.generate_content.return_value = mock_response

        transcript = "Educational content here " * 50

        result = summarize_transcript(transcript, content_type="educational")

        assert result == "Short summary only"
