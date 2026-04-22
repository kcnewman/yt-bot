# bundles the execution together
from app.services.summarize import summarize_transcript
from app.services.telegram import send_text
from app.services.transcript import fetch_captions
from app.utils.logger import logger
from app.utils.youtube import extract_video_id


def process_video(url: str, chat_id: int):
    """
    Main pipeline, runs in the backgrounf to prevent telegram timeouts
    """
    logger.info(f"Starting pipeline for URL: {url} (Chat ID: {chat_id})")

    video_id = extract_video_id(url)
    if not video_id:
        send_text(chat_id, "I couldn't extract a valid Video ID from the link.")
        return

    send_text(chat_id, "Extracting video transcript...")
    transcript = fetch_captions(video_id)
    if not transcript:
        send_text(
            chat_id,
            "Sorry, I couldn't find English captions for this video. (Audio fallback coming soon!)",
        )
        return

    send_text(chat_id, "Reading the transcript and generating a summary...")
    summary = summarize_transcript(transcript)
    if not summary:
        send_text(
            chat_id, "Oops, my AI brain failed to generate a summary. Please try again."
        )
        return

    send_text(chat_id, f"Here is your summary:\n\n{summary}")
    logger.info("Pipeline completed and summary sent to Telegram!")
