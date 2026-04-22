# FastAPI app, webhook handlers
from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request

from app.config import TELEGRAM_SECRET_TOKEN
from app.services.orchestrator import process_video
from app.services.telegram import send_text
from app.utils.youtube import is_valid_url

app = FastAPI()


@app.post("/webhook/telegram")
async def telegram_route(
    request: Request,
    background_task: BackgroundTasks,
    x_telegram_bot_api_secret_token: str = Header(None),
):
    if x_telegram_bot_api_secret_token != TELEGRAM_SECRET_TOKEN:
        raise HTTPException(status_code=401)

    body = await request.json()
    if "message" in body:
        chat_id = body["message"]["chat"]["id"]
        text = body["message"].get("text", "")

        if is_valid_url(text):
            send_text(chat_id, "Got your video!, working the problem...")

            background_task.add_task(process_video, text, chat_id)
        else:
            send_text(chat_id, "Hi! Please send me a valid YouTube link to summarize.")

    return {"status": "ok"}
