"""Application constants."""

# API Configuration
TIMEOUT_SECONDS = 30

# Transcript
TRANSCRIPT_LANGUAGES = ["en"]
TRANSCRIPT_RETRIES = 3
TRANSCRIPT_INITIAL_DELAY = 1.5

# Summarization
SUMMARIZE_MODEL = "gemini-2.5-flash-lite"
SUMMARIZE_BASE_PROMPT = "summarization.txt"
SUMMARIZE_REWRITE_PROMPT = "summarization_rewrite.txt"

# Classification
CLASSIFY_MODEL = "gemini-2.5-flash-lite"
CLASSIFY_PROMPT = "classification.txt"
CLASSIFY_SAMPLE_CHARS = 8000
CLASSIFY_DEFAULT = "general"
CLASSIFY_ALLOWED = {
    "tutorial",
    "interview",
    "news",
    "explainer",
    "review",
    "story",
    "general",
}

# Translation
TRANSLATE_URL = "https://translation-api.ghananlp.org/v2/translate"
TRANSLATE_LANG = "en-tw"

# Text-to-Speech
TTS_URL = "https://translation-api.ghananlp.org/tts/v2/synthesize"
TTS_LANGUAGE = "twi"
TTS_FORMAT = "mp3"

# Telegram
TELEGRAM_API_BASE = "https://api.telegram.org"

# Pipeline Status Messages
STATUS_EXTRACTING = "Got your video! Extracting transcript..."
STATUS_CLASSIFYING = "Checking the video type..."
STATUS_SUMMARIZING = "Reading the transcript and generating a summary..."
STATUS_TRANSLATING = "Translating the summary into Twi..."
STATUS_RECORDING = "Recording the Twi voice note..."

# Error Messages
MSG_INVALID_URL = "I couldn't extract a valid Video ID from the link."
MSG_NO_CAPTIONS = "Sorry, I couldn't find English captions for this video."
MSG_SUMMARY_FAILED = "Oops, my AI brain failed to generate a summary. Please try again."
MSG_TRANSLATION_FAILED_PREFIX = (
    "Sorry, the translation failed. Here is the English version for now:\n\n"
)
MSG_AUDIO_FAILED_PREFIX = (
    "I couldn't generate the audio, but here is your Twi summary:\n\n"
)
MSG_GENERIC_ERROR = (
    "Something went wrong while processing your video. Please try again."
)
