"""Main orchestrator for the video processing pipeline."""

import os

from app.core.constants import (
    MSG_AUDIO_FAILED_PREFIX,
    MSG_INVALID_URL,
    MSG_NO_CAPTIONS,
    MSG_SUMMARY_FAILED,
    MSG_TRANSLATION_FAILED_PREFIX,
    STATUS_CLASSIFYING,
    STATUS_EXTRACTING,
    STATUS_RECORDING,
    STATUS_SUMMARIZING,
    STATUS_TRANSLATING,
)
from app.core.exceptions import (
    SummarizationError,
    TranscriptError,
    TranslationError,
    TTSError,
    ValidationError,
)
from app.services.classify import classify_content
from app.services.summarize import summarize_transcript
from app.services.telegram import delete_message, edit_text, send_audio, send_text
from app.services.transcript import fetch_captions
from app.services.translate import translate
from app.services.tts import generate_audio
from app.utils.logger import logger
from app.utils.youtube import extract_video_id


def _cleanup_file(file_path: str | None) -> None:
    """
    Delete a local file if it exists.

    Args:
        file_path: Path to the file to delete.
    """
    if not file_path:
        return

    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"Cleaned up temporary file: {file_path}")
    except OSError as error:
        logger.warning(f"Failed to delete temporary file {file_path}: {error}")


def process_video(url: str, chat_id: int) -> None:
    """
    Execute the complete video-to-audio pipeline.

    This function orchestrates all steps:
    1. Validate input
    2. Extract transcript
    3. Classify content
    4. Summarize
    5. Translate to Twi
    6. Generate audio
    7. Send to user

    Args:
        url: The YouTube video URL.
        chat_id: The Telegram chat ID for updates.
    """
    logger.info(f"Starting pipeline: URL={url}, Chat={chat_id}")

    # Validate input
    try:
        video_id = extract_video_id(url)
        if not video_id:
            raise ValidationError("Invalid YouTube URL.")
    except ValidationError:
        send_text(chat_id, MSG_INVALID_URL)
        logger.error("Invalid YouTube URL provided.")
        return

    # Send initial status
    status_msg = send_text(chat_id, STATUS_EXTRACTING)
    if not status_msg:
        logger.error("Failed to send initial status message.")
        return

    # Extract transcript
    try:
        logger.info(f"Extracting transcript for video: {video_id}")
        transcript = fetch_captions(video_id)
    except TranscriptError as error:
        logger.warning(f"Transcript extraction failed: {error}")
        edit_text(chat_id, status_msg, MSG_NO_CAPTIONS)
        return

    # Classify content
    try:
        edit_text(chat_id, status_msg, STATUS_CLASSIFYING)
        logger.info("Classifying content...")
        content_type = classify_content(transcript)
    except Exception as error:
        logger.warning(f"Content classification failed: {error}")
        content_type = "general"

    # Summarize
    try:
        edit_text(chat_id, status_msg, STATUS_SUMMARIZING)
        logger.info("Generating summary...")
        summary = summarize_transcript(transcript, content_type)
    except SummarizationError as error:
        logger.error(f"Summarization failed: {error}")
        edit_text(chat_id, status_msg, MSG_SUMMARY_FAILED)
        return

    # Translate
    try:
        edit_text(chat_id, status_msg, STATUS_TRANSLATING)
        logger.info("Translating to Twi...")
        twi_text = translate(summary)
    except TranslationError as error:
        logger.error(f"Translation failed: {error}")
        delete_message(chat_id, status_msg)
        send_text(chat_id, MSG_TRANSLATION_FAILED_PREFIX + summary)
        return

    # Generate audio
    try:
        edit_text(chat_id, status_msg, STATUS_RECORDING)
        logger.info("Generating audio...")
        audio_path = generate_audio(twi_text)
    except TTSError as error:
        logger.error(f"Audio generation failed: {error}")
        delete_message(chat_id, status_msg)
        send_text(chat_id, MSG_AUDIO_FAILED_PREFIX + twi_text)
        return

    # Send audio
    delete_message(chat_id, status_msg)
    try:
        success = send_audio(chat_id, audio_path)
        if success:
            logger.info("Pipeline completed successfully!")
        else:
            logger.warning("Audio sent with issues.")
            send_text(chat_id, MSG_AUDIO_FAILED_PREFIX + twi_text)
    finally:
        _cleanup_file(audio_path)
