# FastAPI app, webhook handlers
from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request

from app.config import TELEGRAM_SECRET_TOKEN
from app.services.telegram import send_text

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

        send_text(chat_id, "Got it! Working the problem...")

    return {"status": "ok"}
