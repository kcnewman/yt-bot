# YouTube → Twi Audio Bot

A Telegram bot that takes a YouTube URL, extracts the transcript, summarizes it, translates the summary into Twi (Akan), and delivers a voice note.

## Features

- Telegram chat interface — paste a YouTube link, receive a voice note
- Status messages during processing
- AI summarization via Google Gemini 2.5 Flash Lite
- Twi translation and TTS via Khaya AI
- Video cache to reduce redundant external API calls
- Request logging for debugging
- Text fallback when audio generation fails

## Project Structure

```
app/
├── core/              # Exceptions, validators, constants, clients
├── db/                # Database models, repository, connection
├── services/          # Business logic (orchestrator, transcript, summarize, etc.)
├── utils/             # Helpers (logger, youtube, prompt)
├── config.py          # Environment configuration
└── main.py            # FastAPI entry point
prompts/               # LLM prompt templates
migrations/            # Database schema migrations
```

## Prerequisites

- Python 3.12+
- uv
- ngrok (for local Telegram webhook testing)

### API Credentials

- **Google Cloud**: Vertex AI enabled, credentials configured
- **Khaya AI**: API key for translation and TTS
- **Telegram**: Bot token from [@BotFather](https://t.me/botfather)

## Setup

```bash
git clone https://github.com/kcnewman/yt-bot.git
cd yt-bot
uv sync
source .venv/bin/activate
```

Create `.env`:

```env
TELEGRAM_BOT_TOKEN="your_bot_token"
TELEGRAM_SECRET_TOKEN="your_secret_token"
GCP_PROJECT_ID="your-project-id"
GCP_REGION="us-central1"
KHAYA_API_KEY="your_khaya_api_key"
TTS_TEMPO="1.0"
LOG_LEVEL="INFO"
APP_ENV="development"
AUTO_INIT_DB="true"
DATABASE_URL=""  # Defaults to local SQLite when unset
```

Authenticate with Google Cloud:

```bash
gcloud auth application-default login
```

## Running Locally

Terminal 1 — start the API server:

```bash
uv run uvicorn app.main:app --reload --port 8000
```

Terminal 2 — expose with ngrok:

```bash
ngrok http 8000
```

Terminal 3 — set the Telegram webhook:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"url":"https://<NGROK_URL>/webhook/telegram","secret_token":"<SECRET>"}' \
  "https://api.telegram.org/bot<TOKEN>/setWebhook"
```

## Pipeline

```
User sends YouTube URL
  → Validate URL
  → Extract Transcript
  → Classify Content
  → Generate Summary
  → Translate to Twi
  → Generate Audio
  → Send Voice Note
```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md).

## Tests

```bash
uv run --extra dev pytest -q
```

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) — code structure and patterns
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Google Vertex AI](https://cloud.google.com/vertex-ai/docs)
- [Khaya AI](https://www.ghananlp.org/)
