"""Custom exceptions for the application."""


class BotException(Exception):
    """Base exception for all bot errors."""

    pass


class TranscriptError(BotException):
    """Raised when transcript extraction fails."""

    pass


class SummarizationError(BotException):
    """Raised when summarization fails."""

    pass


class TranslationError(BotException):
    """Raised when translation fails."""

    pass


class TTSError(BotException):
    """Raised when text-to-speech generation fails."""

    pass


class ValidationError(BotException):
    """Raised when input validation fails."""

    pass
