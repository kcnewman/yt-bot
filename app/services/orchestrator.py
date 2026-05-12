"""Main orchestrator for the video processing pipeline."""

import tempfile
import threading
from pathlib import Path

from app.core.constants import (
    MSG_AUDIO_FAILED_PREFIX,
    MSG_GENERIC_ERROR,
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

_pipeline_locks: dict[str, threading.Lock] = {}
_pipeline_locks_lock = threading.Lock()


def _get_pipeline_lock(video_id: str) -> threading.Lock:
    with _pipeline_locks_lock:
        if video_id not in _pipeline_locks:
            _pipeline_locks[video_id] = threading.Lock()
        return _pipeline_locks[video_id]


def _cleanup_file(file_path: str | None) -> None:
    if not file_path:
        return
    try:
        Path(file_path).unlink(missing_ok=True)
    except OSError as error:
        logger.warning(f"Failed to delete temporary file {file_path}: {error}")


def _read_audio_file(file_path: str | None) -> bytes | None:
    if not file_path:
        return None
    try:
        return Path(file_path).read_bytes()
    except OSError as error:
        logger.warning(f"Failed to read audio file for cache: {error}")
        return None


def _write_cached_audio(audio_data: bytes) -> str:
    with tempfile.NamedTemporaryFile(
        prefix="audio_cache_",
        suffix=".mp3",
        delete=False,
    ) as audio_file:
        audio_file.write(audio_data)
        return audio_file.name


def process_video(url: str, chat_id: int) -> None:
    logger.info(f"Starting pipeline: URL={url}, Chat={chat_id}")
    request_log_id: int | None = None
    log_completed = False
    cache_hit = False
    status_msg: int | None = None

    def _complete(
        status: str,
        error_message: str | None = None,
        failed_cache_hit: bool | None = None,
    ) -> None:
        nonlocal log_completed
        if request_log_id is None or log_completed:
            return
        try:
            db_repository.complete_request_log(
                request_log_id,
                status=status,
                cache_hit=failed_cache_hit
                if failed_cache_hit is not None
                else cache_hit,
                error_message=error_message,
            )
            log_completed = True
        except Exception as e:
            logger.warning(f"Failed to complete request log: {e}")

    # Validate input
    try:
        video_id = extract_video_id(url)
        if not video_id:
            raise ValidationError("Invalid YouTube URL.")
    except ValidationError:
        request_log_id = db_repository.create_request_log(
            chat_id=chat_id, url=url, video_id=None
        )
        _complete(status="invalid_url", error_message="Invalid YouTube URL.")
        send_text(chat_id, MSG_INVALID_URL)
        return

    try:
        with db_repository.request_scope():
            request_log_id = db_repository.create_request_log(
                chat_id=chat_id, url=url, video_id=video_id
            )

            status_msg = send_text(chat_id, STATUS_EXTRACTING)
            if not status_msg:
                _complete(
                    status="failed",
                    error_message="Failed to send initial status message.",
                )
                return

            # Per-video lock to prevent cache stampede
            lock = _get_pipeline_lock(video_id)
            lock.acquire()
            try:
                cached_video = db_repository.get_processed_video(video_id)
                if cached_video and cached_video.audio_data:
                    cache_hit = True
                    logger.info(f"Video cache hit: {video_id}")
                    audio_path: str | None = None
                    try:
                        edit_text(chat_id, status_msg, STATUS_RECORDING)
                        audio_path = _write_cached_audio(cached_video.audio_data)
                        delete_message(chat_id, status_msg)
                        if send_audio(chat_id, audio_path):
                            _complete(status="success")
                        else:
                            send_text(
                                chat_id, MSG_AUDIO_FAILED_PREFIX + cached_video.twi_text
                            )
                            _complete(
                                status="failed",
                                error_message="Failed to send cached audio.",
                                failed_cache_hit=True,
                            )
                    finally:
                        _cleanup_file(audio_path)
                    return
            finally:
                lock.release()

            # Extract transcript
            try:
                transcript = fetch_captions(video_id)
            except TranscriptError as error:
                edit_text(chat_id, status_msg, MSG_NO_CAPTIONS)
                _complete(status="failed", error_message=str(error))
                return

            # Classify content
            try:
                edit_text(chat_id, status_msg, STATUS_CLASSIFYING)
                content_type = classify_content(transcript)
            except Exception as error:
                logger.warning(f"Content classification failed: {error}")
                content_type = "general"

            # Summarize
            try:
                edit_text(chat_id, status_msg, STATUS_SUMMARIZING)
                summary = summarize_transcript(transcript, content_type)
            except SummarizationError as error:
                edit_text(chat_id, status_msg, MSG_SUMMARY_FAILED)
                _complete(status="failed", error_message=str(error))
                return

            # Translate
            try:
                edit_text(chat_id, status_msg, STATUS_TRANSLATING)
                twi_text = translate(summary)
            except TranslationError as error:
                delete_message(chat_id, status_msg)
                send_text(chat_id, MSG_TRANSLATION_FAILED_PREFIX + summary)
                _complete(status="failed", error_message=str(error))
                return

            # Generate audio
            audio_path = None
            try:
                edit_text(chat_id, status_msg, STATUS_RECORDING)
                audio_path = generate_audio(twi_text)
            except TTSError as error:
                delete_message(chat_id, status_msg)
                send_text(chat_id, MSG_AUDIO_FAILED_PREFIX + twi_text)
                _complete(status="failed", error_message=str(error))
                return

            # Cache the result (still within request_scope)
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
                if send_audio(chat_id, audio_path):
                    _complete(status="success")
                else:
                    send_text(chat_id, MSG_AUDIO_FAILED_PREFIX + twi_text)
                    _complete(
                        status="failed", error_message="Failed to send generated audio."
                    )
            finally:
                _cleanup_file(audio_path)

    except Exception as error:
        logger.error(f"Unexpected pipeline error: {error}", exc_info=True)
        _complete(status="failed", error_message=str(error))
        if status_msg is not None:
            try:
                delete_message(chat_id, status_msg)
            except Exception:
                pass
        send_text(chat_id, MSG_GENERIC_ERROR)
