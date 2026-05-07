"""Custom exceptions for the application."""


class BotException(Exception):
    """Base exception for all bot errors."""

    pass


class ConfigError(BotException):
    """Raised when configuration is missing or invalid."""

    pass


class ExternalAPIError(BotException):
    """Raised when external API calls fail."""

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


class TelegramError(BotException):
    """Raised when Telegram API operations fail."""

    pass


class ValidationError(BotException):
    """Raised when input validation fails."""

    pass
