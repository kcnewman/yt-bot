# LLM summarization with type-aware prompts
from google import genai

from app.config import GCP_PROJECT_ID, GCP_REGION
from app.utils.logger import logger
from app.utils.prompt import load_prompt

try:
    client = genai.Client(vertexai=True, project=GCP_PROJECT_ID, location=GCP_REGION)
    logger.info("Google GenAI Client initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize GenAI Client: {e}: {e}")


def summarize_transcript(transcript: str) -> str | None:
    """
    Takes raw video transcript and uses Gemini to summarize it.
    """
    if not transcript:
        return None

    base_prompt = load_prompt("summarization.txt")
    if not base_prompt:
        base_prompt = (
            "Summarize the following transcript in 300-500 words.\n\nTranscript:\n"
        )

    full_prompt = f"{base_prompt}\n{transcript}"

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite", contents=full_prompt
        )
        summary = response.text.strip()
        logger.info(f"Generated summary of: {len(summary)} characters.")
        return summary

    except Exception as e:
        logger.error(f"Summarization failed: {e}", exc_info=True)
        return None
