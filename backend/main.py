"""
ScotlandAI Navigator — FastAPI Application Entry Point

This is where the backend starts. It:
1. Creates the FastAPI application with metadata for auto-generated docs
2. Configures CORS (which origins can call this API)
3. Registers the API router
4. Sets up logging

ARCHITECTURE NOTE:
The backend is deliberately thin. The OpenClaw agent handles the 5-question
discovery conversation. The backend only activates when all 5 answers are
collected and validated. One POST request in, one brief out.

No sessions. No database. No user accounts. Stateless by design.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from api.router import router

# ── Logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════
# Application
# ═══════════════════════════════════════════════

app = FastAPI(
    title="ScotlandAI Navigator API",
    description=(
        "Generates AI Opportunity Briefs for Scottish organisations on DataVita infrastructure. "
        "Takes 5 discovery answers, produces 3 specific AI product recommendations "
        "with infrastructure mapping, and generates a downloadable PDF."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── CORS Middleware ──
# Allows the OpenClaw agent and web clients to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ── Routes ──
app.include_router(router)


# ── Startup Event ──
@app.on_event("startup")
async def startup():
    """Log configuration on startup (without exposing secrets)."""
    logger.info("=" * 60)
    logger.info("ScotlandAI Navigator API starting up")
    logger.info(f"  Environment: {settings.ENVIRONMENT}")
    logger.info(f"  Base URL: {settings.BASE_URL}")
    logger.info(f"  PDF expiry: {settings.PDF_EXPIRY_MINUTES} minutes")
    logger.info(f"  CORS origins: {settings.ALLOWED_ORIGINS}")
    logger.info(f"  Gemini API key: {'configured' if settings.GEMINI_API_KEY else 'MISSING'}")
    logger.info("=" * 60)
