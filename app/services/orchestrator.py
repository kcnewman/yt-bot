# bundles the execution together
from app.services.summarize import summarize_transcript
from app.services.telegram import delete_message, edit_text, send_text
from app.services.transcript import fetch_captions
from app.services.translate import translate
from app.utils.logger import logger
from app.utils.youtube import extract_video_id


def process_video(url: str, chat_id: int):
    """
    Main pipeline, runs in the backgrounf to prevent telegram timeouts
    """
    logger.info(f"Starting pipeline for URL: {url} (Chat ID: {chat_id})")

    status_msg = send_text(chat_id, "Got your video! Extracting transcript...")

    video_id = extract_video_id(url)
    if not video_id:
        edit_text(
            chat_id, status_msg, "I couldn't extract a valid Video ID from the link."
        )
        return

    transcript = fetch_captions(video_id)
    if not transcript:
        edit_text(
            chat_id,
            status_msg,
            "Sorry, I couldn't find English captions for this video. (Audio fallback coming soon!)",
        )
        return

    edit_text(chat_id, status_msg, "Reading the transcript and generating a summary...")
    summary = summarize_transcript(transcript)
    if not summary:
        edit_text(
            chat_id,
            status_msg,
            "Oops, my AI brain failed to generate a summary. Please try again.",
        )
        return

    edit_text(chat_id, status_msg, "Translating the summary into Twi...")
    twi_text = translate(summary)
    if not twi_text:
        delete_message(chat_id, status_msg)
        send_text(
            chat_id,
            "Sorry, the translation failed. Here is the English version for now:\n\n"
            + summary,
        )
        return

    delete_message(chat_id, status_msg)
    send_text(chat_id, f"Here is your Twi summary:\n\n{twi_text}")
    logger.info("Pipeline completed and Twi summary sent to Telegram!")
