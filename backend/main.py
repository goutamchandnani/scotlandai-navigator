"""
ScotlandAI Navigator — FastAPI Application Entry Point

This is where the backend starts. It:
1. Creates the FastAPI application with metadata for auto-generated docs
2. Configures CORS (which origins can call this API)
3. Registers the API router (generate-brief, download, health, capture-lead)
4. Initialises the Telegram bot webhook (v1.2 — if TELEGRAM_BOT_TOKEN is set)
5. Sets up logging

ARCHITECTURE NOTE:
The backend handles two modes of interaction:
  - Direct API: OpenClaw agent POSTs to /generate-brief (5 answers → brief)
  - Telegram bot: Users message @ScotlandAINavigtorBot → webhook → conversation
    state → /generate-brief called internally → brief sent back via Telegram

Both paths use the same brief generation pipeline. The Telegram bot adds a
conversation state layer on top — managing the 5-question discovery in-process.

No sessions. No database. Stateless brief generation.
Telegram conversation state is in-memory (acceptable for competition demo).
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from api.router import router

# ── Logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ── Telegram bot (initialised at startup if token is configured) ──
_telegram_app = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    global _telegram_app

    logger.info("=" * 60)
    logger.info("ScotlandAI Navigator API starting up")
    logger.info(f"  Environment: {settings.ENVIRONMENT}")
    logger.info(f"  Base URL: {settings.BASE_URL}")
    logger.info(f"  PDF expiry: {settings.PDF_EXPIRY_MINUTES} minutes")
    logger.info(f"  Gemini API key: {'configured' if settings.GEMINI_API_KEY else 'MISSING'}")
    logger.info(f"  Lead capture: {'enabled' if settings.LEAD_CAPTURE_WEBHOOK else 'disabled'}")

    if settings.TELEGRAM_BOT_TOKEN:
        try:
            import asyncio
            from services.telegram_bot import build_telegram_app
            _telegram_app = build_telegram_app()
            await _telegram_app.initialize()

            webhook_url = f"{settings.BASE_URL}/telegram/webhook"

            # Check if webhook is already set correctly (avoids flood control
            # when 2 gunicorn workers both try to register at startup)
            current = await _telegram_app.bot.get_webhook_info()
            if current.url == webhook_url:
                logger.info(f"  Telegram bot: webhook already set at {webhook_url}")
            else:
                # Retry up to 3 times with backoff (handles flood control)
                for attempt in range(3):
                    try:
                        await _telegram_app.bot.set_webhook(
                            url=webhook_url,
                            allowed_updates=["message"],
                        )
                        logger.info(f"  Telegram bot: webhook registered at {webhook_url}")
                        break
                    except Exception as e:
                        if attempt < 2:
                            await asyncio.sleep(2 ** attempt)  # 1s, 2s backoff
                        else:
                            raise e

        except Exception as e:
            logger.error(f"  Telegram bot: failed to initialise — {e}")
    else:
        logger.info("  Telegram bot: TELEGRAM_BOT_TOKEN not set — bot disabled")

    logger.info("=" * 60)

    yield

    # Shutdown
    if _telegram_app:
        await _telegram_app.shutdown()
        logger.info("Telegram bot shut down cleanly")


# ═══════════════════════════════════════════════
# Application
# ═══════════════════════════════════════════════

app = FastAPI(
    title="ScotlandAI Navigator API",
    description=(
        "Generates AI Opportunity Briefs for Scottish organisations on DataVita infrastructure. "
        "Takes 5 discovery answers, produces 3 specific AI product recommendations "
        "with infrastructure mapping, and generates a downloadable PDF. "
        "Also powers the @ScotlandAINavigtorBot Telegram bot."
    ),
    version="1.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ── CORS Middleware ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ── Routes ──
app.include_router(router)


# ═══════════════════════════════════════════════
# POST /telegram/webhook — Telegram bot webhook
# ═══════════════════════════════════════════════

@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    """
    Receive updates from Telegram and process them through the bot.

    Telegram calls this endpoint for every message sent to the bot.
    We pass the update to python-telegram-bot for routing to the
    correct handler (start command, message, etc.).

    Returns 200 immediately — Telegram expects a fast response.
    """
    if _telegram_app is None:
        return Response(status_code=503, content="Telegram bot not configured")

    from telegram import Update
    data = await request.json()
    update = Update.de_json(data, _telegram_app.bot)
    await _telegram_app.process_update(update)
    return Response(status_code=200)
