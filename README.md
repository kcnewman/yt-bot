# YouTube to Twi Audio Bot

An AI-powered pipeline that consumes a YouTube video link, extracts its transcript, generates a concise summary, translates it into Twi (Akan), and delivers a native voice note directly to the user via Telegram.

**Status**: MVP (Minimum Viable Product)

---

## Features

- **Seamless Chat Interface**: Users paste a YouTube link into Telegram
- **Live Status Updates**: User is updated on status of request
- **AI Summarization**: Google Gemini 2.5 Flash Lite generates summaries
- **Twi Translation & TTS**: Khaya AI provides translation and natural voice synthesis
- **Video Cache**: Processed videos are cached to reduce repeated external API calls
- **Request Logging**: Processing attempts are stored for debugging
- **Graceful Failures**: User receives text fallback if audio generation fails


---

## Project Structure

```
app/
├── core/              # Exceptions, validators, constants, clients
├── services/          # Business logic (orchestrator, transcript, summarize, etc.)
├── utils/             # Helpers (logger, youtube, prompt)
├── config.py          # Environment configuration
└── main.py            # FastAPI entry point
```

---

## Installation & Setup

### 1. Prerequisites
- Python 3.12+
- uv (Python package manager)
- ngrok (for local Telegram webhook testing)

#### API Requirements:
- **Google Cloud**: Vertex AI enabled, credentials configured
- **Khaya AI**: API key for translation and TTS
- **Telegram**: Bot token and secret from [@BotFather](https://t.me/botfather)

### 2. Clone & Install

```bash
git clone https://github.com/kcnewman/yt-bot.git
cd yt-bot
uv sync
source .venv/bin/activate
```

### 3. Environment Variables

Create a `.env` file:

```env
# Telegram
TELEGRAM_BOT_TOKEN="your_bot_token"
TELEGRAM_SECRET_TOKEN="your_secret_token"

# Google Cloud
GCP_PROJECT_ID="your-project-id"
GCP_REGION="us-central1"

# External APIs
KHAYA_API_KEY="your_khaya_api_key"
YOUTUBE_PROXY_URL=""  # Optional, recommended for Cloud Run transcript fetching

# Optional
TTS_TEMPO="1.0"  # Audio speed adjustment (0.5-2.0)

# Runtime / database
APP_ENV="development"
AUTO_INIT_DB="true"
DATABASE_URL=""  # Defaults to local SQLite when unset
```

### 4. Google Cloud Authentication

```bash
gcloud auth application-default login
```

---

## Running Locally

### Terminal 1: Start FastAPI server

```bash
uv run uvicorn app.main:app --reload --port 8000
```

### Terminal 2: Expose with ngrok

```bash
ngrok http 8000
```

### Terminal 3: Configure Telegram webhook

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"url":"https://<NGROK_URL>/webhook/telegram","secret_token":"<SECRET>"}' \
  "https://api.telegram.org/bot<TOKEN>/setWebhook"
```

---

## Pipeline Flow

```
User sends YouTube URL
         ↓
    [Validate URL]
         ↓
    [Extract Transcript]
         ↓
    [Classify Content]
         ↓
    [Generate Summary]
         ↓
    [Translate to Twi]
         ↓
    [Generate Audio]
         ↓
    [Send Voice Note]
```

> Check logs if any component fails for traceback

---

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for Cloud Run deployment notes.

## Tests

```bash
uv run --extra dev pytest -q
```

---

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Detailed structure and patterns
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Google Vertex AI](https://cloud.google.com/vertex-ai/docs)
- [Khaya AI](https://www.ghananlp.org/)
