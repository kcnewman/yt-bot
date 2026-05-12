"""FastAPI application entry point."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException, Request
from sqlalchemy import text

from app.config import AUTO_INIT_DB, PIPELINE_WORKERS, TELEGRAM_SECRET_TOKEN
from app.core.exceptions import ValidationError
from app.core.validators import validate_chat_id, validate_youtube_url
from app.db import SessionLocal, init_db
from app.services.orchestrator import process_video
from app.services.telegram import send_text
from app.utils.logger import logger

_pool: ThreadPoolExecutor | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _pool
    if AUTO_INIT_DB:
        init_db()
        logger.info("Database schema initialized.")
    _pool = ThreadPoolExecutor(max_workers=PIPELINE_WORKERS)
    logger.info(f"Pipeline thread pool started (workers={PIPELINE_WORKERS}).")
    yield
    _pool.shutdown(wait=True)
    logger.info("Pipeline thread pool shut down.")


app = FastAPI(title="YouTube to Twi Bot", version="0.1.0", lifespan=lifespan)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
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
    x_telegram_bot_api_secret_token: str | None = Header(None),
):
    if x_telegram_bot_api_secret_token != TELEGRAM_SECRET_TOKEN:
        logger.warning("Unauthorized webhook access attempt.")
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        body = await request.json()
    except Exception as error:
        logger.error(f"Failed to parse webhook body: {error}")
        raise HTTPException(status_code=400, detail="Invalid JSON")

    if "message" in body:
        try:
            chat_id = validate_chat_id(body["message"]["chat"]["id"])
            text = body["message"].get("text", "").strip()

            if not text:
                logger.debug(f"Ignoring empty message from chat {chat_id}")
                return {"status": "ok"}

            try:
                video_id = validate_youtube_url(text)
                logger.info(f"Valid YouTube URL detected: {video_id}")
                if _pool is not None:
                    _pool.submit(process_video, text, chat_id)
                else:
                    logger.error("Pipeline thread pool not available.")
            except ValidationError:
                msg = (
                    "Hi! 👋 Please send me a valid YouTube link to summarize "
                    "and convert to audio."
                )
                send_text(chat_id, msg)

        except Exception as error:
            logger.error(f"Error processing webhook: {error}", exc_info=True)

    return {"status": "ok"}
