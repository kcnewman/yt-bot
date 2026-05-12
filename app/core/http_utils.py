"""Shared HTTP utilities."""

from app.config import KHAYA_API_KEY


def build_khaya_headers() -> dict[str, str]:
    """Build HTTP headers for Khaya AI APIs (translation and TTS)."""
    return {
        "Ocp-Apim-Subscription-Key": KHAYA_API_KEY or "",
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
    }
