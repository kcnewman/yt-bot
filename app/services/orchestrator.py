import os

from app.services.summarize import summarize_transcript
from app.services.telegram import delete_message, edit_text, send_audio, send_text
from app.services.transcript import fetch_captions
from app.services.translate import translate
from app.services.tts import generate_audio
from app.utils.logger import logger
from app.utils.youtube import extract_video_id

STATUS_EXTRACTING = "Got your video! Extracting transcript..."
STATUS_SUMMARIZING = "Reading the transcript and generating a summary..."
STATUS_TRANSLATING = "Translating the summary into Twi..."
STATUS_RECORDING = "Recording the Twi voice note..."

MSG_INVALID_URL = "I couldn't extract a valid Video ID from the link."
MSG_NO_CAPTIONS = (
    "Sorry, I couldn't find English captions for this video. "
    "(Audio fallback coming soon!)"
)
MSG_SUMMARY_FAILED = "Oops, my AI brain failed to generate a summary. Please try again."
MSG_TRANSLATION_FAILED_PREFIX = (
    "Sorry, the translation failed. Here is the English version for now:\n\n"
)
MSG_AUDIO_FAILED_PREFIX = (
    "I couldn't generate the audio, but here is your Twi summary:\n\n"
)


def _remove_file(path: str | None) -> None:
    """Delete a local file if it exists."""
    if not path:
        return
    if os.path.exists(path):
        os.remove(path)


def process_video(url: str, chat_id: int) -> None:
    """Run the full YouTube to Twi voice-note pipeline."""
    logger.info(f"Starting pipeline for URL: {url} (Chat ID: {chat_id})")

    status_msg = send_text(chat_id, STATUS_EXTRACTING)

    video_id = extract_video_id(url)
    if not video_id:
        edit_text(chat_id, status_msg, MSG_INVALID_URL)
        return

    transcript = fetch_captions(video_id)
    if not transcript:
        edit_text(chat_id, status_msg, MSG_NO_CAPTIONS)
        return

    edit_text(chat_id, status_msg, STATUS_SUMMARIZING)
    summary = summarize_transcript(transcript)
    if not summary:
        edit_text(chat_id, status_msg, MSG_SUMMARY_FAILED)
        return

    edit_text(chat_id, status_msg, STATUS_TRANSLATING)
    twi_text = translate(summary)
    if not twi_text:
        delete_message(chat_id, status_msg)
        send_text(chat_id, MSG_TRANSLATION_FAILED_PREFIX + summary)
        return

    edit_text(chat_id, status_msg, STATUS_RECORDING)
    audio = generate_audio(twi_text)

    delete_message(chat_id, status_msg)

    if audio:
        try:
            send_audio(chat_id, audio)
        finally:
            _remove_file(audio)
    else:
        send_text(chat_id, MSG_AUDIO_FAILED_PREFIX + twi_text)

    logger.info("Pipeline completed entirely!")
