"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request
from sqlalchemy import text

from app.config import AUTO_INIT_DB, TELEGRAM_SECRET_TOKEN
from app.core.validators import validate_chat_id, validate_youtube_url
from app.db import SessionLocal, init_db
from app.services.orchestrator import process_video
from app.services.telegram import send_text
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize runtime resources."""
    if AUTO_INIT_DB:
        init_db()
        logger.info("Database schema initialized.")
    yield


app = FastAPI(title="YouTube to Twi Bot", version="0.1.0", lifespan=lifespan)


@app.get("/healthz")
def healthz():
    """Lightweight liveness check for Cloud Run."""
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    """Readiness check that verifies database connectivity."""
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as error:
        logger.error(f"Readiness check failed: {error}")
        raise HTTPException(status_code=503, detail="Database unavailable")


@app.post("/webhook/telegram")
async def telegram_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_telegram_bot_api_secret_token: str = Header(None),
):
    """
    Webhook endpoint for Telegram bot updates.

    Args:
        request: The HTTP request from Telegram.
        background_tasks: FastAPI background tasks manager.
        x_telegram_bot_api_secret_token: Secret token from Telegram header.

    Returns:
        JSON response confirming receipt.

    Raises:
        HTTPException: If authentication fails.
    """
    # Verify secret token
    if x_telegram_bot_api_secret_token != TELEGRAM_SECRET_TOKEN:
        logger.warning("Unauthorized webhook access attempt.")
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        body = await request.json()
    except Exception as error:
        logger.error(f"Failed to parse webhook body: {error}")
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Process message
    if "message" in body:
        try:
            chat_id = validate_chat_id(body["message"]["chat"]["id"])
            text = body["message"].get("text", "").strip()

            if not text:
                logger.debug(f"Ignoring empty message from chat {chat_id}")
                return {"status": "ok"}

            # Check if URL and queue for processing
            try:
                video_id = validate_youtube_url(text)
                logger.info(f"Valid YouTube URL detected: {video_id}")
                background_tasks.add_task(process_video, text, chat_id)
            except Exception:
                # Not a valid YouTube URL, send help message
                msg = (
                    "Hi! 👋 Please send me a valid YouTube link to summarize "
                    "and convert to audio."
                )
                send_text(chat_id, msg)

        except Exception as error:
            logger.error(f"Error processing webhook: {error}", exc_info=True)

    return {"status": "ok"}
