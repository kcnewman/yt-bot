"""Summarization service using LLM."""

import re

from google import genai

from app.core.clients import create_genai_client
from app.core.constants import (
    SUMMARIZE_BASE_PROMPT,
    SUMMARIZE_MODEL,
    SUMMARIZE_REWRITE_PROMPT,
)
from app.core.exceptions import SummarizationError
from app.utils.logger import logger
from app.utils.prompt import load_prompt

WORD_PATTERN = re.compile(r"\b[\w'-]+\b")

client: genai.Client | None = create_genai_client()


def _count_words(text: str) -> int:
    """Count the number of words in text."""
    return len(WORD_PATTERN.findall(text))


def _should_rewrite(summary: str, source_word_count: int) -> bool:
    """
    Determine if a summary needs rewriting for simplicity and length.

    Args:
        summary: The summary text.
        source_word_count: The number of words in the source transcript.

    Returns:
        True if rewriting is needed.
    """
    summary_words = _count_words(summary)
    words = WORD_PATTERN.findall(summary.lower())
    long_words = [w for w in words if len(w) >= 11]

    too_long = summary_words >= source_word_count
    too_complex = bool(words) and (len(long_words) / len(words)) > 0.10

    return too_long or too_complex


def _render_prompt(template_name: str, **values: str | int) -> str:
    """
    Load and render a prompt template with given values.

    Args:
        template_name: The template filename.
        **values: Values to interpolate into the template.

    Returns:
        The rendered prompt.

    Raises:
        SummarizationError: If template loading or rendering fails.
    """
    template = load_prompt(template_name).strip()
    if not template:
        raise SummarizationError(f"Prompt template is missing: {template_name}")

    try:
        return template.format(**values)
    except KeyError as error:
        raise SummarizationError(f"Missing template value for {template_name}: {error}")


def _generate_text(prompt: str) -> str:
    """
    Generate text using the LLM.

    Args:
        prompt: The prompt to send to the model.

    Returns:
        The generated text.

    Raises:
        SummarizationError: If generation fails.
    """
    if client is None:
        raise SummarizationError("GenAI client is not available.")

    try:
        response = client.models.generate_content(
            model=SUMMARIZE_MODEL, contents=prompt
        )
        if not response.text:
            raise SummarizationError("Model returned empty response.")
        return response.text.strip()
    except SummarizationError:
        raise
    except Exception as error:
        raise SummarizationError(f"LLM generation failed: {error}")


def summarize_transcript(transcript: str, content_type: str = "general") -> str:
    """
    Generate a concise summary from a transcript.

    Args:
        transcript: The transcript to summarize.
        content_type: The classification of the content (used for prompt selection).

    Returns:
        The generated summary.

    Raises:
        SummarizationError: If summarization fails.
    """
    if not transcript or not transcript.strip():
        raise SummarizationError("Transcript cannot be empty.")

    clean_transcript = transcript.strip()
    transcript_words = _count_words(clean_transcript)

    base_prompt = _render_prompt(
        SUMMARIZE_BASE_PROMPT,
        content_type=content_type,
        source_words=transcript_words,
        transcript=clean_transcript,
    )

    try:
        summary = _generate_text(base_prompt)

        if _should_rewrite(summary, transcript_words):
            rewrite_prompt = _render_prompt(
                SUMMARIZE_REWRITE_PROMPT,
                source_words=transcript_words,
                summary=summary,
            )
            rewritten = _generate_text(rewrite_prompt)
            summary = rewritten

        logger.info(f"Generated summary of {len(summary)} characters.")
        return summary

    except SummarizationError:
        raise
    except Exception as error:
        logger.error(f"Unexpected error during summarization: {error}", exc_info=True)
        raise SummarizationError(f"Summarization failed: {error}")
