# LLM summarization
import re

from google import genai

from app.config import GCP_PROJECT_ID, GCP_REGION
from app.utils.logger import logger
from app.utils.prompt import load_prompt

MODEL_NAME = "gemini-2.5-flash-lite"
BASE_PROMPT_FILE = "summarization.txt"
REWRITE_PROMPT_FILE = "summarization_rewrite.txt"
WORD_PATTERN = re.compile(r"\b[\w'-]+\b")


def _create_client() -> genai.Client | None:
    """Create and return the GenAI client."""
    try:
        client = genai.Client(
            vertexai=True,
            project=GCP_PROJECT_ID,
            location=GCP_REGION,
        )
        logger.info("Google GenAI Client initialized successfully.")
        return client
    except Exception as error:
        logger.error(f"Failed to initialize GenAI Client: {error}", exc_info=True)
        return None


client: genai.Client | None = _create_client()


def _word_count(text: str) -> int:
    """Return number of words in text."""
    return len(WORD_PATTERN.findall(text))


def _needs_rewrite(summary: str, source_word_count: int) -> bool:
    """Check whether summary should be simplified or shortened."""
    summary_words = _word_count(summary)
    words = WORD_PATTERN.findall(summary.lower())
    long_words = [w for w in words if len(w) >= 11]

    too_long = summary_words >= source_word_count
    too_complex = bool(words) and (len(long_words) / len(words)) > 0.10
    return too_long or too_complex


def _render_prompt(template_name: str, **values: str | int) -> str | None:
    """Load and render a prompt template."""
    template = load_prompt(template_name).strip()
    if not template:
        logger.error(f"Prompt template is empty or missing: {template_name}")
        return None

    try:
        return template.format(**values)
    except KeyError as error:
        logger.error(f"Missing template value for {template_name}: {error}")
        return None


def _generate_text(prompt: str) -> str | None:
    """Generate text from the model using a prompt."""
    if client is None:
        logger.error("GenAI client is not available.")
        return None

    response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
    if not response.text:
        return None

    text = response.text.strip()
    return text or None


def summarize_transcript(transcript: str, content_type: str = "general") -> str | None:
    """Generate a short, simple summary from raw transcript text."""
    if not transcript or not transcript.strip():
        return None

    clean_transcript = transcript.strip()
    transcript_words = _word_count(clean_transcript)

    base_prompt = _render_prompt(
        BASE_PROMPT_FILE,
        content_type=content_type,
        source_words=transcript_words,
        transcript=clean_transcript,
    )
    if base_prompt is None:
        return None

    try:
        summary = _generate_text(base_prompt)
        if summary is None:
            return None

        if _needs_rewrite(summary, transcript_words):
            rewrite_prompt = _render_prompt(
                REWRITE_PROMPT_FILE,
                source_words=transcript_words,
                summary=summary,
            )
            if rewrite_prompt is not None:
                rewritten = _generate_text(rewrite_prompt)
                if rewritten:
                    summary = rewritten

        logger.info(f"Generated summary of: {len(summary)} characters.")
        return summary

    except Exception as error:
        logger.error(f"Summarization failed: {error}", exc_info=True)
        return None
