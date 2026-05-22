"""
ScotlandAI Navigator — Telegram Bot Service

Runs as a webhook handler INSIDE the FastAPI backend on Render.
No OpenClaw required. No pairing codes. Always on 24/7.

Any judge can message t.me/ScotlandAINavigtorBot and get the full
5-question discovery → brief → PDF → lead capture experience.

CONVERSATION FLOW:
  /start          → Welcome + Question 1 (organisation & bottleneck)
  Answer 1        → Question 2 (data assets)
  Answer 2        → Question 3 (value of improvement)
  Answer 3        → Question 4 (risk appetite)
  Answer 4        → Question 5 (technical capability)
  Answer 5        → Generate brief → Send text + PDF link
  yes/no          → Lead capture opt-in
  yes → name      → Email address → Forward to webhook → Confirm

STATE MANAGEMENT:
  In-memory dict keyed by Telegram user_id.
  Resets per session. Acceptable for a competition demo.
  (A production version would use Redis for persistence across restarts.)

WEBHOOK vs POLLING:
  We use webhook mode — Telegram pushes updates to our Render endpoint.
  This is the correct production approach: no persistent connection, no
  polling loop, no threading issues with async FastAPI.
"""

import logging
from datetime import datetime, timezone

from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.constants import ParseMode

from core.config import settings
from services.brief_builder import generate_brief, extract_organisation_name
from services.lead_capture import send_lead_to_webhook
from services.pdf_generator import generate_pdf, save_pdf
from schemas.discovery import DiscoveryAnswers, RiskAppetite, TechnicalCapability
from schemas.lead import LeadCaptureRequest
from core.security import generate_download_token
from fastapi.concurrency import run_in_threadpool
from pathlib import Path

BRIEFS_DIR = Path("static/briefs")
BRIEFS_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)

# ── In-memory session store ──
# { user_id (int): session dict }
_sessions: dict[int, dict] = {}


# ── Conversation questions ──
# Each tuple: (field_name, question_text)
QUESTIONS = [
    (
        "organisation_and_bottleneck",
        (
            "What does your organisation do, and what is your single biggest "
            "operational challenge right now?\n\n"
            "_Be as specific as you can — the more detail you share, the more "
            "useful the brief I'll produce._"
        ),
    ),
    (
        "data_assets",
        (
            "What data do you already have digitally?\n\n"
            "_Think: documents, databases, spreadsheets, sensor feeds, "
            "customer records, transaction logs — anything digital._"
        ),
    ),
    (
        "value_of_improvement",
        (
            "What would a meaningful improvement in that challenge be worth "
            "to your organisation?\n\n"
            "_Rough is fine — staff time saved, cost reduced, revenue gained. "
            "Any measure helps me quantify the opportunity._"
        ),
    ),
    (
        "risk_appetite",
        (
            "Are you looking for a *quick win* you can prove in 90 days, "
            "or a *longer strategic transformation*?\n\n"
            "_Reply with: quick win or strategic_"
        ),
    ),
    (
        "technical_capability",
        (
            "Last one: do you have an internal technical team who could support "
            "a build, or would you need full delivery support from a partner?\n\n"
            "_Reply with: internal team or need support_"
        ),
    ),
]

WELCOME = (
    "🏴󠁧󠁢󠁳󠁣󠁴󠁥 *Welcome to ScotlandAI Navigator*\n\n"
    "I help Scottish organisations turn AI ambition into a concrete, "
    "board\\-ready opportunity brief — in under 10 minutes\\.\n\n"
    "I'll ask you five quick questions, then produce a specific brief "
    "with three AI products your organisation could realistically build, "
    "each mapped to DataVita's world\\-class infrastructure\\.\n\n"
    "Let's start\\.\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━\n"
    "*Question 1 of 5*\n\n"
)


# ── Session helpers ──

def _session(user_id: int) -> dict:
    """Get or create a session for this user."""
    if user_id not in _sessions:
        _sessions[user_id] = {
            "step": 0,
            "answers": {},
            "brief": None,
            "pdf_url": None,
            "infrastructure": "DV1 Lanarkshire",
            "org_name": "Organisation",
            "awaiting_opt_in": False,
            "awaiting_name": False,
            "awaiting_email": False,
            "lead_name": None,
        }
    return _sessions[user_id]


def _reset(user_id: int):
    _sessions.pop(user_id, None)


# ── Input normalisation ──

def _map_risk_appetite(text: str) -> RiskAppetite:
    lower = text.lower()
    if any(w in lower for w in ["quick", "win", "fast", "90", "short", "soon", "pilot"]):
        return RiskAppetite.quick_win
    if any(w in lower for w in ["strategic", "long", "transform", "full", "big"]):
        return RiskAppetite.strategic
    return RiskAppetite.quick_win  # safe default


def _map_technical_capability(text: str) -> TechnicalCapability:
    lower = text.lower()
    if any(w in lower for w in ["internal", "team", "have", "yes", "own", "we do", "in-house"]):
        return TechnicalCapability.internal_team
    return TechnicalCapability.needs_support


# ── Brief formatter ──

def _format_brief_for_telegram(brief, org_name: str, pdf_url: str | None) -> list[str]:
    """
    Format the brief as a list of Telegram messages.
    Split into multiple messages to avoid Telegram's 4096-char limit.
    Uses MarkdownV2 escaping for special characters.
    """
    def esc(text: str) -> str:
        """Escape special MarkdownV2 characters."""
        for ch in r"_*[]()~`>#+-=|{}.!":
            text = text.replace(ch, f"\\{ch}")
        return text

    messages = []

    # Message 1: Header + Executive Summary
    header = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🏴󠁧󠁢󠁳󠁣󠁴󠁥 *SCOTLAND AI OPPORTUNITY BRIEF*\n"
        f"_{esc(org_name)}_\n"
        f"_Generated: {esc(datetime.now(timezone.utc).strftime('%d %B %Y'))}_\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "*EXECUTIVE SUMMARY*\n\n"
        f"{esc(brief.executive_summary)}"
    )
    messages.append(header)

    # Messages 2-4: One message per opportunity
    for i, opp in enumerate(brief.opportunities, 1):
        data_list = "\n".join(f"  • {esc(d)}" for d in opp.data_required)
        opp_text = (
            f"*OPPORTUNITY {i} — {esc(opp.name)}*\n\n"
            f"*What it does:* {esc(opp.what_it_does)}\n\n"
            f"*Problem it solves:* {esc(opp.problem_solved)}\n\n"
            f"*Data required:*\n{data_list}\n\n"
            f"*Expected impact:* {esc(opp.expected_impact)}\n\n"
            f"*Infrastructure:* {esc(opp.infrastructure)}\n\n"
            f"*Complexity:* {esc(opp.build_complexity)} \\| "
            f"*Time to value:* {esc(opp.time_to_value)}"
        )
        messages.append(opp_text)

    # Message 5: First step + PDF + CTA
    footer_parts = [
        "*RECOMMENDED FIRST STEP*\n\n"
        f"{esc(brief.recommended_first_step)}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📞 [datavita\\.co\\.uk/contact](https://datavita.co.uk/contact) \\| AI Solutions team"
    ]

    if pdf_url:
        footer_parts.append(
            f"\n\n📎 [Download your PDF brief]({pdf_url})\n"
            "_Link valid for 60 minutes_"
        )

    messages.append("".join(footer_parts))

    return messages


# ── Handlers ──

async def handle_start(update: Update, context) -> None:
    """Handle /start — reset session and begin discovery."""
    user_id = update.effective_user.id
    _reset(user_id)
    session = _session(user_id)
    session["step"] = 1

    first_question = QUESTIONS[0][1]
    await update.message.reply_text(
        WELCOME + first_question,
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def handle_message(update: Update, context) -> None:
    """Route all incoming messages to the right conversation stage."""
    user_id = update.effective_user.id
    session = _session(user_id)
    text = update.message.text.strip()

    # ── Lead capture: waiting for name ──
    if session["awaiting_name"]:
        session["lead_name"] = text
        session["awaiting_name"] = False
        session["awaiting_email"] = True
        await update.message.reply_text("What's your email address?")
        return

    # ── Lead capture: waiting for email ──
    if session["awaiting_email"]:
        session["awaiting_email"] = False
        email = text
        name = session.get("lead_name", "")

        lead = LeadCaptureRequest(
            name=name,
            email=email,
            organisation=session["answers"].get("organisation_and_bottleneck", "")[:200],
            brief_summary=session.get("brief_summary", ""),
            infrastructure_recommended=session.get("infrastructure", "DV1 Lanarkshire"),
        )

        # Best-effort — never tell user if this fails
        try:
            await send_lead_to_webhook(lead)
        except Exception:
            pass

        # Escape email for MarkdownV2 — pre-computed to avoid backslash in f-string (Python 3.11)
        safe_email = email.replace('.', '\\.').replace('-', '\\-').replace('_', '\\_')
        await update.message.reply_text(
            f"\u2705 Done\\. The DataVita AI Solutions team will be in touch at {safe_email}\\.\n\n"
            "The PDF brief has everything they'll need to get started\\.",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    # ── Opt-in response ──
    if session["awaiting_opt_in"]:
        session["awaiting_opt_in"] = False
        lower = text.lower()

        if any(w in lower for w in ["yes", "yeah", "yep", "sure", "ok", "please", "y"]):
            session["awaiting_name"] = True
            await update.message.reply_text("What's your name?")
        else:
            await update.message.reply_text(
                "No problem at all\\. The brief is yours to use however you need\\.\n\n"
                "📞 [datavita\\.co\\.uk/contact](https://datavita.co.uk/contact) is always "
                "there if you change your mind\\.",
                parse_mode=ParseMode.MARKDOWN_V2,
            )
        return

    # ── Not started ──
    step = session["step"]
    if step == 0:
        await handle_start(update, context)
        return

    # ── Brief already delivered ──
    if step > 5:
        await update.message.reply_text(
            "Your brief has been delivered\\. Type /start to run a new discovery\\.",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    # ── Collecting discovery answers ──
    field, _ = QUESTIONS[step - 1]

    if field == "risk_appetite":
        session["answers"][field] = _map_risk_appetite(text)
    elif field == "technical_capability":
        session["answers"][field] = _map_technical_capability(text)
    else:
        session["answers"][field] = text

    session["step"] += 1

    if session["step"] <= 5:
        # Ask next question — pre-compute step to avoid quotes-in-f-string (Python 3.11)
        next_step = session["step"]
        _, next_question = QUESTIONS[next_step - 1]
        await update.message.reply_text(
            f"*Question {next_step} of 5*\n\n{next_question}",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
    else:
        # All 5 answers — generate the brief
        await _run_brief_generation(update, session)


async def _run_brief_generation(update: Update, session: dict) -> None:
    """Generate the brief and send it back in multiple messages."""
    await update.message.reply_text(
        "🏴󠁧󠁢󠁳󠁣󠁴󠁥 Got everything I need\\. Building your brief now\\.\n\n"
        "_This usually takes 10–15 seconds\\._",
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    try:
        # Build validated DiscoveryAnswers
        answers = DiscoveryAnswers(
            organisation_and_bottleneck=session["answers"]["organisation_and_bottleneck"],
            data_assets=session["answers"]["data_assets"],
            value_of_improvement=session["answers"]["value_of_improvement"],
            risk_appetite=session["answers"]["risk_appetite"],
            technical_capability=session["answers"]["technical_capability"],
        )

        # Generate brief (Gemini call with retry logic)
        brief = await generate_brief(answers)

        # Extract org name for the PDF header
        org_name = extract_organisation_name(answers.organisation_and_bottleneck)
        session["org_name"] = org_name
        session["brief"] = brief
        session["brief_summary"] = brief.executive_summary[:500]

        # Store infrastructure recommendation for lead capture
        if brief.opportunities:
            session["infrastructure"] = brief.opportunities[0].infrastructure

        # Generate PDF
        pdf_url = None
        try:
            filename, pdf_bytes = await run_in_threadpool(
                generate_pdf, brief, org_name, answers.model_dump()
            )
            await run_in_threadpool(save_pdf, filename, pdf_bytes)
            token = generate_download_token(filename)
            pdf_url = f"{settings.BASE_URL}/download/{token}"
            session["pdf_url"] = pdf_url
        except Exception as e:
            logger.warning(f"PDF generation failed for Telegram user: {e}")

        # Send brief in multiple messages
        messages = _format_brief_for_telegram(brief, org_name, pdf_url)
        for msg in messages:
            await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN_V2)

        # Lead capture opt-in
        session["awaiting_opt_in"] = True
        await update.message.reply_text(
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Would you like DataVita's AI Solutions team to reach out and "
            "discuss any of these opportunities with you?\n\n"
            "Reply *yes* to share your contact details, or *no* if you'd prefer not to\\.\n\n"
            "_No pressure — the brief is yours either way\\._",
            parse_mode=ParseMode.MARKDOWN_V2,
        )

    except Exception as e:
        logger.error(f"Brief generation failed for Telegram user: {e}")
        await update.message.reply_text(
            "⚠️ Something went wrong generating your brief\\. Please try again with /start\\.\n\n"
            "If this keeps happening, contact "
            "[datavita\\.co\\.uk/contact](https://datavita.co.uk/contact) directly\\.",
            parse_mode=ParseMode.MARKDOWN_V2,
        )


# ── Application builder ──

def build_telegram_app() -> Application:
    """
    Build and return the python-telegram-bot Application.
    Called once at FastAPI startup. The application is used
    to process webhook updates via process_update().
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is not configured")

    app = (
        Application.builder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .updater(None)          # No polling — we use webhooks
        .build()
    )

    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("reset", handle_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    return app
