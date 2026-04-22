import os

from app.config import PROMPTS_DIR
from app.utils.logger import logger


def load_prompt(filename: str) -> str:
    """
    Load prompts from the prompts directory
    """
    prompt = os.path.join(PROMPTS_DIR, filename)

    try:
        with open(prompt, "r", encoding="utf-8") as file:
            logger.debug(f"{filename} prompt loaded.")
            return file.read()
    except Exception as e:
        logger.error(f"Could not read {filename} prompt file: {e}")
        return ""
