"""Main orchestrator for the video processing pipeline."""

import os
import tempfile
from pathlib import Path

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
from app.db.repository import DatabaseRepository
from app.services.classify import classify_content
from app.services.summarize import summarize_transcript
from app.services.telegram import delete_message, edit_text, send_audio, send_text
from app.services.transcript import fetch_captions
from app.services.translate import translate
from app.services.tts import generate_audio
from app.utils.logger import logger
from app.utils.youtube import extract_video_id

db_repository = DatabaseRepository()


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


def _read_audio_file(file_path: str | None) -> bytes | None:
    """Read generated audio bytes for caching."""
    if not file_path:
        return None

    try:
        return Path(file_path).read_bytes()
    except OSError as error:
        logger.warning(f"Failed to read audio file for cache: {error}")
        return None


def _write_cached_audio(audio_data: bytes) -> str:
    """Write cached audio bytes to a temporary MP3 file for Telegram upload."""
    with tempfile.NamedTemporaryFile(
        prefix="audio_cache_",
        suffix=".mp3",
        delete=False,
    ) as audio_file:
        audio_file.write(audio_data)
        return audio_file.name


def _create_request_log(chat_id: int, url: str, video_id: str | None) -> int | None:
    """Create a request log without allowing database issues to stop processing."""
    try:
        return db_repository.create_request_log(
            chat_id=chat_id,
            url=url,
            video_id=video_id,
        )
    except Exception as error:
        logger.warning(f"Failed to create request log: {error}")
        return None


def _complete_request_log(
    log_id: int | None,
    *,
    status: str,
    cache_hit: bool = False,
    error_message: str | None = None,
) -> None:
    """Complete a request log without allowing database issues to stop processing."""
    if log_id is None:
        return

    try:
        db_repository.complete_request_log(
            log_id,
            status=status,
            cache_hit=cache_hit,
            error_message=error_message,
        )
    except Exception as error:
        logger.warning(f"Failed to complete request log: {error}")


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
    request_log_id: int | None = None
    cache_hit = False

    # Validate input
    try:
        video_id = extract_video_id(url)
        if not video_id:
            raise ValidationError("Invalid YouTube URL.")
    except ValidationError:
        request_log_id = _create_request_log(chat_id, url, None)
        _complete_request_log(
            request_log_id,
            status="invalid_url",
            error_message="Invalid YouTube URL.",
        )
        send_text(chat_id, MSG_INVALID_URL)
        logger.error("Invalid YouTube URL provided.")
        return

    request_log_id = _create_request_log(chat_id, url, video_id)

    # Send initial status
    status_msg = send_text(chat_id, STATUS_EXTRACTING)
    if not status_msg:
        logger.error("Failed to send initial status message.")
        _complete_request_log(
            request_log_id,
            status="failed",
            error_message="Failed to send initial status message.",
        )
        return

    # Use cached processed output when available.
    try:
        cached_video = db_repository.get_processed_video(video_id)
    except Exception as error:
        cached_video = None
        logger.warning(f"Failed to read video cache: {error}")

    if cached_video and cached_video.audio_data:
        cache_hit = True
        logger.info(f"Video cache hit: {video_id}")
        audio_path = None
        try:
            edit_text(chat_id, status_msg, STATUS_RECORDING)
            audio_path = _write_cached_audio(cached_video.audio_data)
            delete_message(chat_id, status_msg)
            success = send_audio(chat_id, audio_path)
            if success:
                _complete_request_log(
                    request_log_id,
                    status="success",
                    cache_hit=True,
                )
                logger.info("Pipeline completed successfully from cache!")
            else:
                send_text(chat_id, MSG_AUDIO_FAILED_PREFIX + cached_video.twi_text)
                _complete_request_log(
                    request_log_id,
                    status="failed",
                    cache_hit=True,
                    error_message="Failed to send cached audio.",
                )
        finally:
            _cleanup_file(audio_path)
        return

    # Extract transcript
    try:
        logger.info(f"Extracting transcript for video: {video_id}")
        transcript = fetch_captions(video_id)
    except TranscriptError as error:
        logger.warning(f"Transcript extraction failed: {error}")
        edit_text(chat_id, status_msg, MSG_NO_CAPTIONS)
        _complete_request_log(
            request_log_id,
            status="failed",
            cache_hit=cache_hit,
            error_message=str(error),
        )
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
        _complete_request_log(
            request_log_id,
            status="failed",
            cache_hit=cache_hit,
            error_message=str(error),
        )
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
        _complete_request_log(
            request_log_id,
            status="failed",
            cache_hit=cache_hit,
            error_message=str(error),
        )
        return

    # Generate audio
    audio_path: str | None = None
    try:
        edit_text(chat_id, status_msg, STATUS_RECORDING)
        logger.info("Generating audio...")
        audio_path = generate_audio(twi_text)
    except TTSError as error:
        logger.error(f"Audio generation failed: {error}")
        delete_message(chat_id, status_msg)
        send_text(chat_id, MSG_AUDIO_FAILED_PREFIX + twi_text)
        _complete_request_log(
            request_log_id,
            status="failed",
            cache_hit=cache_hit,
            error_message=str(error),
        )
        return

    audio_data = _read_audio_file(audio_path)
    try:
        db_repository.upsert_processed_video(
            video_id=video_id,
            source_url=url,
            transcript=transcript,
            content_type=content_type,
            summary=summary,
            twi_text=twi_text,
            audio_data=audio_data,
            audio_content_type="audio/mpeg" if audio_data else None,
        )
    except Exception as error:
        logger.warning(f"Failed to write video cache: {error}")

    # Send audio
    delete_message(chat_id, status_msg)
    try:
        success = send_audio(chat_id, audio_path)
        if success:
            logger.info("Pipeline completed successfully!")
            _complete_request_log(
                request_log_id,
                status="success",
                cache_hit=cache_hit,
            )
        else:
            logger.warning("Audio sent with issues.")
            send_text(chat_id, MSG_AUDIO_FAILED_PREFIX + twi_text)
            _complete_request_log(
                request_log_id,
                status="failed",
                cache_hit=cache_hit,
                error_message="Failed to send generated audio.",
            )
    finally:
        _cleanup_file(audio_path)
