# Architecture

## Overview

The project is structured around a linear pipeline: validate input, extract transcript, classify content, summarize, translate, generate audio, deliver to user. Each step is an isolated module with a single responsibility.

## Principles

- **Separation of concerns** — each module has one job
- **Explicit error handling** — services raise specific exceptions
- **Reusability** — common logic in shared utilities
- **Simplicity** — no unnecessary abstractions

## Directory Structure

```
app/
├── __init__.py
├── config.py                # Environment config with validation
├── main.py                  # FastAPI entry point
├── core/
│   ├── __init__.py
│   ├── constants.py         # All magic strings and numbers
│   ├── exceptions.py        # Custom exception classes
│   ├── validators.py        # Input validation
│   └── clients.py           # External API client init
├── db/
│   ├── __init__.py
│   ├── database.py          # DB connection and session management
│   ├── models.py            # SQLAlchemy ORM models
│   └── repository.py        # Data access layer
├── services/
│   ├── __init__.py
│   ├── orchestrator.py      # Pipeline coordinator
│   ├── transcript.py        # YouTube transcript extraction
│   ├── classify.py          # Content type classification
│   ├── summarize.py         # LLM summarization
│   ├── translate.py         # Twi translation
│   ├── tts.py               # Text-to-speech
│   └── telegram.py          # Telegram API client
└── utils/
    ├── __init__.py
    ├── logger.py            # Structured logging
    ├── youtube.py           # URL parsing
    └── prompt.py            # Prompt template loading
prompts/                     # LLM prompt templates
migrations/                  # SQL schema migrations
```

## Core Module

### Exceptions (`core/exceptions.py`)

Exception hierarchy for type-safe error handling:

- `BotException` — base class
- `TranscriptError` — transcript extraction failure
- `SummarizationError` — summarization failure
- `TranslationError` — translation failure
- `TTSError` — audio generation failure
- `ValidationError` — input validation failure

### Constants (`core/constants.py`)

All API endpoints, model names, status messages, and error messages in one file. No magic strings in service code.

### Validators (`core/validators.py`)

- `validate_youtube_url()` — extract and validate video ID
- `validate_text()` — validate non-empty text
- `validate_chat_id()` — validate Telegram chat ID

### Clients (`core/clients.py`)

Centralized external API client setup:

- `create_genai_client()` — Google GenAI client with error handling

## Services

### Orchestrator

Runs the pipeline in sequence: validate → transcript → classify → summarize → translate → TTS → Telegram. Each step has its own try/except block. Converts exceptions to user-facing messages.

### Transcript

Extracts English captions via `youtube_transcript_api`. Raises `TranscriptError` on failure.

### Classify

Classifies content type (tutorial, interview, news, etc.) using Gemini. Falls back to "general" on error.

### Summarize

Generates a summary using Gemini. Validates output length/quality. Retries if quality checks fail. Raises `SummarizationError` on failure.

### Translate

Translates English to Twi via Khaya AI API. Raises `TranslationError` on failure.

### TTS

Converts Twi text to speech via Khaya AI API. Applies tempo adjustment with ffmpeg. Raises `TTSError` on failure.

### Telegram

Wrapper around the Telegram Bot API. Returns `bool`/`int` on success, `False`/`None` on failure (no exceptions — graceful degradation).

## Error Handling

- **Services** raise typed exceptions for failures
- **Orchestrator** catches each exception and sends a user-friendly message
- **Telegram service** returns `False`/`None` instead of raising — ensures the user always gets a response (audio or text fallback)

## Logging

Levels:
- `debug` — development details
- `info` — major pipeline steps
- `warning` — recoverable issues
- `error` — failures with traceback

Output to console. On Cloud Run, logs are picked up by Cloud Logging from stdout.

## Testing

Services are designed for straightforward testing:
- Validators: unit test with valid/invalid input
- Services: mock external APIs, assert exception types
- Orchestrator: mock services, verify error paths

## Adding a New Feature

1. Add endpoints/params to `core/constants.py`
2. Create service in `services/`
3. Raise typed exception on failure
4. Add try/except in orchestrator
5. Map exception to user message

## Security

- Webhook secret token validation
- API keys in environment variables only
- Input validation at all boundaries
- Error messages do not leak internals
