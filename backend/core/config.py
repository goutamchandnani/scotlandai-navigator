"""
ScotlandAI Navigator — Configuration

All configuration is loaded from environment variables.
API keys are NEVER hardcoded, logged, or transmitted to clients.

This is a deliberate architectural decision:
- Environment variables are the industry standard for secret management
- Render injects them at runtime, they never touch the codebase
- Pydantic Settings validates them at startup — if GEMINI_API_KEY is missing,
  the server fails loudly instead of silently producing empty briefs
"""

from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # ── Required ──
    GEMINI_API_KEY: str = Field(
        ...,
        description="Google Gemini API key from aistudio.google.com"
    )

    # ── Server ──
    ENVIRONMENT: str = Field(
        default="development",
        description="'development' or 'production'"
    )
    BASE_URL: str = Field(
        default="http://localhost:8000",
        description="Public base URL of this API (for PDF download links)"
    )

    # ── Security ──
    SECRET_KEY: str = Field(
        default="dev-secret-change-in-production",
        description="Secret key for signing PDF download tokens"
    )

    # ── PDF ──
    PDF_EXPIRY_MINUTES: int = Field(
        default=60,
        description="How long PDF download links remain valid"
    )

    # ── CORS ──
    ALLOWED_ORIGINS: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:8000",
            "https://scotland-ai-navigator.onrender.com",
        ],
        description="Origins allowed to call this API"
    )


# Singleton — imported everywhere as `from core.config import settings`
settings = Settings()
