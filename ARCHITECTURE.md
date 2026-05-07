# Architecture & Code Organization

## Overview

This document explains the professional software engineering structure of the YouTube to Twi Bot project.

## Core Principles

- **Separation of Concerns**: Each module has a single, well-defined responsibility
- **Graceful Failure**: Services raise specific exceptions for structured error handling
- **Reusability**: Common logic extracted to utilities and constants
- **Simplicity**: Straightforward code without unnecessary abstractions
- **Logging**: Comprehensive, structured logging at each step

## Directory Structure

```
app/
├── __init__.py              # Package initialization
├── config.py                # Environment configuration & validation
├── main.py                  # FastAPI application entry point
├── core/                    # Core application abstractions
│   ├── __init__.py
│   ├── constants.py         # Centralized string & number constants
│   ├── exceptions.py        # Custom exception classes
│   ├── validators.py        # Input validation logic
│   └── clients.py           # External API client initialization
├── services/                # Business logic services
│   ├── __init__.py
│   ├── orchestrator.py      # Pipeline orchestration
│   ├── transcript.py        # YouTube transcript extraction
│   ├── classify.py          # Content type classification
│   ├── summarize.py         # LLM-based summarization
│   ├── translate.py         # Twi language translation
│   ├── tts.py               # Text-to-speech audio generation
│   └── telegram.py          # Telegram bot API client
└── utils/                   # Utility functions
    ├── __init__.py
    ├── logger.py            # Structured logging setup
    ├── youtube.py           # YouTube URL parsing
    ├── prompt.py            # Prompt template loading
    └── storage.py           # GCS utilities (future use)
```

## Key Components

### 1. Configuration (`config.py`)

- Loads environment variables with validation
- Provides sensible defaults
- Warns about missing required configuration
- Centralizes all config access

**Usage:**
```python
from app.config import TELEGRAM_BOT_TOKEN, GCP_PROJECT_ID
```

### 2. Core Module (`app/core/`)

#### Exceptions (`exceptions.py`)
Custom exception hierarchy for type-safe error handling:
- `BotException` - Base class
- `TranscriptError` - Transcript extraction failures
- `SummarizationError` - Summarization failures
- `TranslationError` - Translation failures
- `TTSError` - Audio generation failures
- `TelegramError` - Telegram API failures
- `ValidationError` - Input validation failures

**Usage:**
```python
try:
    transcript = fetch_captions(video_id)
except TranscriptError as e:
    logger.error(f"Failed to get transcript: {e}")
    # Handle gracefully
```

#### Constants (`constants.py`)
All magic strings and numbers in one place:
- API endpoints and configuration
- Status messages
- Error messages
- Model names and parameters

**Benefits:**
- No repeated strings across codebase
- Easy to modify messages without searching
- Centralized configuration of all services

#### Validators (`validators.py`)
Input validation at service boundaries:
- `validate_youtube_url()` - Validates and extracts video ID
- `validate_text()` - Validates text input
- `validate_chat_id()` - Validates Telegram chat ID

**Usage:**
```python
from app.core.validators import validate_youtube_url
try:
    video_id = validate_youtube_url(user_input)
except ValidationError as e:
    send_error_message(e.message)
```

#### Clients (`clients.py`)
Centralized initialization of external API clients:
- `create_genai_client()` - Google GenAI client initialization
- Handles authentication and error cases

### 3. Services (`app/services/`)

Each service is a focused module handling one aspect of the pipeline:

#### Orchestrator (`orchestrator.py`)
Main coordinator of the entire pipeline:
- Validates input
- Calls services in sequence
- Handles errors at each step
- Sends user updates via Telegram
- Cleans up temporary resources

**Flow:**
1. Validate YouTube URL
2. Extract transcript
3. Classify content type
4. Generate summary
5. Translate to Twi
6. Generate audio
7. Send to user

#### Transcript Service (`transcript.py`)
- Extracts English captions from YouTube videos
- Raises `TranscriptError` on failure
- Returns raw transcript text

#### Classification Service (`classify.py`)
- Classifies content type (tutorial, interview, news, etc.)
- Helps tailor summarization
- Falls back to "general" on error

#### Summarization Service (`summarize.py`)
- Generates concise summaries using LLM
- Validates summary quality (length, complexity)
- Reruns if needed
- Raises `SummarizationError` on failure

#### Translation Service (`translate.py`)
- Translates English summaries to Twi
- Calls Khaya AI API
- Raises `TranslationError` on failure

#### TTS Service (`tts.py`)
- Converts Twi text to speech audio
- Calls Khaya AI API
- Applies tempo adjustment
- Raises `TTSError` on failure

#### Telegram Service (`telegram.py`)
- Wrapper around Telegram Bot API
- Returns boolean/int to indicate success
- Handles file uploads
- Returns False/None on error instead of raising

### 4. Utilities (`app/utils/`)

#### Logger (`logger.py`)
Structured logging with:
- Console output (immediate feedback)
- File logging (persistent record)
- Daily log rotation (14-day retention)
- Consistent formatting

#### YouTube Utilities (`youtube.py`)
- Parses various YouTube URL formats
- Extracts 11-character video ID
- Used by validators

#### Prompt Loading (`prompt.py`)
- Loads prompt templates from disk
- Handles missing/empty files gracefully
- Returns empty string on error (fail-safe)

## Error Handling Strategy

### Service Layer
Services that call external APIs raise specific exceptions:
- Validation fails → `ValidationError`
- Transcript missing → `TranscriptError`
- LLM fails → `SummarizationError`
- Translation fails → `TranslationError`
- Audio generation fails → `TTSError`

### Orchestrator
Catches exceptions and converts to user messages:
```python
try:
    summary = summarize_transcript(transcript)
except SummarizationError as error:
    logger.error(f"Summarization failed: {error}")
    send_text(chat_id, "Oops, summarization failed. Try again?")
    return
```

### Telegram Service
Returns boolean for success instead of raising:
- Allows graceful degradation
- User messages always delivered (either audio or text)

## Logging

Consistent logging at each step:

```python
logger.info("Pipeline started")          # Major steps
logger.warning("Transcript empty")       # Recoverable issues
logger.error("API failed", exc_info=True) # Errors with context
logger.debug("Extracted video ID")       # Development info
```

## Adding New Features

### New External Service
1. Add URL/model to `constants.py`
2. Create service in `services/`
3. Raise specific exception on failure
4. Call from orchestrator with try/except
5. Convert exception to user message

### New Input Validation
1. Add validator to `core/validators.py`
2. Use in main.py webhook or service
3. Raise `ValidationError` if invalid

### New Constant
Add to `core/constants.py` instead of hardcoding.

## Testing Strategy

Services are designed to be testable:
- Validators can be unit tested
- Services can be mocked (raise exceptions)
- Orchestrator logic is linear and observable

Example:
```python
def test_summarize_empty_transcript():
    with pytest.raises(SummarizationError):
        summarize_transcript("")

def test_translate_missing_api_key():
    with pytest.raises(TranslationError):
        translate("hello")
```

## Performance Considerations

- FastAPI background tasks prevent webhook timeouts
- Single Telegram message edit for status updates (efficient)
- Temporary files cleaned up after sending
- Logging doesn't block execution

## Security

- Secret token validation on webhook
- API keys in environment variables (not hardcoded)
- Input validation at all boundaries
- Error messages don't expose internal details
