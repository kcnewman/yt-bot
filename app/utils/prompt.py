"""Prompt template loading utilities."""

import os

from app.config import PROMPTS_DIR
from app.utils.logger import logger


def load_prompt(filename: str) -> str:
    """
    Load a prompt template from the prompts directory.

    Args:
        filename: The name of the prompt file to load.

    Returns:
        The prompt content as a string, or empty string if loading fails.
    """
    if not filename or not filename.strip():
        logger.error("Prompt filename cannot be empty.")
        return ""

    prompt_path = PROMPTS_DIR / filename

    try:
        if not prompt_path.exists():
            logger.error(f"Prompt file not found: {filename}")
            return ""

        with open(prompt_path, "r", encoding="utf-8") as file:
            content = file.read()
            if not content or not content.strip():
                logger.warning(f"Prompt file is empty: {filename}")
                return ""

            logger.debug(f"Loaded prompt: {filename}")
            return content

    except OSError as error:
        logger.error(f"Failed to read prompt file {filename}: {error}")
        return ""
    except Exception as error:
        logger.error(
            f"Unexpected error loading prompt {filename}: {error}", exc_info=True
        )
        return ""
