# 🎙️ YouTube to Twi Audio Bot (Telegram MVP)

An AI-powered automated pipeline that consumes a YouTube video link, extracts its transcript, generates a concise summary, translates it into Twi (Akan), and delivers a native voice note directly to the user via Telegram.

This project serves as the Minimum Viable Product (MVP) for what will eventually become a WhatsApp-based service. Currently, it uses Telegram as the primary interface for rapid iteration and testing.

---

## ✨ Features

- Seamless Chat Interface: Users paste a YouTube link into the chat  
- Smart Orchestration: FastAPI uses background tasks to prevent webhook timeouts  
- Live Status Updates: Single message updates (e.g., ⏳ Extracting transcript... → 🎤 Recording voice note...)  
- AI Summarization: Google Gemini 2.5 Flash Lite via Vertex AI generates 300–500 word summaries  
- Twi Translation & TTS: Khaya AI provides translation and natural voice synthesis  
- Optimized Audio: Native .ogg output for Telegram voice notes (no ffmpeg required)

---

## 🏗️ Architecture & Pipeline Flow

1. Input: User sends a YouTube URL  
2. Webhook Ack: FastAPI returns 200 OK, offloads to background task  
3. Transcript Extraction: Pull captions from YouTube APIs  
4. Summarization: Gemini generates conversational summary  
5. Translation: English → Twi via Khaya AI  
6. TTS: Twi text → .ogg audio  
7. Delivery: Send voice note + fallback text  

---

## 📂 Project Structure

twi-summary-bot/
│
├── app/
│   ├── main.py
│   ├── config.py
│   ├── services/
│   │   ├── orchestrator.py
│   │   ├── transcript.py
│   │   ├── summarize.py
│   │   ├── translate.py
│   │   ├── tts.py
│   │   └── telegram.py
│   └── utils/
│       ├── logger.py
│       ├── youtube.py
│       └── prompts.py
│
├── prompts/
│   ├── summarization.txt
│   └── classification.txt
│
├── .env
└── README.md
---

## 🚀 Installation & Local Setup

### 1. Prerequisites
- Python 3.10+
- uv (Python package manager)
- ngrok

#### API Access:
- Google Cloud (Vertex AI enabled)
- Khaya AI API Key
- Telegram Bot Token

---

### 2. Clone Repository
bash git clone <repository-url> cd twi-summary-bot 

---

### 3. Install Dependencies
bash uv venv source .venv/bin/activate uv add fastapi uvicorn requests google-genai python-dotenv 

---

### 4. Environment Variables

Create .env:

env TELEGRAM_BOT_TOKEN="your_token" TELEGRAM_SECRET_TOKEN="your_secret"  GCP_PROJECT_ID="your_project" GCP_REGION="us-central1"  KHAYA_API_KEY="your_key" 

---

### 5. Google Cloud Auth
bash gcloud auth application-default login 

---

## ▶️ Running the Bot

### Terminal 1
bash uvicorn app.main:app --reload --port 8000 

### Terminal 2
bash ngrok http 8000 

---

## 🔗 Configure Telegram Webhook

bash curl -F "url=https://<NGROK_URL>/webhook/telegram" \      -F "secret_token=<SECRET>" \      https://api.telegram.org/bot<TELEGRAM_TOKEN>/setWebhook 

---

## ✅ Test

- Open Telegram  
- Send a YouTube link  
- Observe pipeline execution  

---

## 🔮 Roadmap

- WhatsApp API migration  
- Audio fallback (Whisper / Khaya ASR)  
- Long video chunking  
- Docker + Cloud Run deployment
