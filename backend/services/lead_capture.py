"""
ScotlandAI Navigator — Lead Capture Service (v1.1)

Forwards opted-in lead data to the configured webhook URL.

HOW IT WORKS:
  1. Agent collects name + email after user says "yes" to follow-up
  2. Agent POSTs to /capture-lead with name, email, and brief context
  3. This service builds a rich webhook payload and POSTs it to
     LEAD_CAPTURE_WEBHOOK (Airtable, Make, Zapier, or any HTTP endpoint)
  4. DataVita's AI Solutions team sees the lead with full brief context
     — no follow-up questions needed to understand what was discussed

IF WEBHOOK IS NOT SET:
  The function exits cleanly — no error, no side effect.
  This means lead capture can be enabled/disabled by simply setting or
  unsetting one environment variable. Zero code change required.

WEBHOOK PAYLOAD FORMAT:
  Sent as a JSON POST. Compatible with Airtable's Create Record API,
  Make/Zapier webhook triggers, and any generic HTTP endpoint.

  {
    "name": "Jane Smith",
    "email": "jane@example.gov.uk",
    "organisation": "Fife Council",
    "brief_summary": "Fife Council processes 400 planning...",
    "infrastructure_recommended": "DV1 Lanarkshire",
    "captured_at": "2026-05-22T13:00:00Z",
    "source": "ScotlandAI Navigator v1.1"
  }
"""

import logging
from datetime import datetime, timezone

import httpx

from core.config import settings
from schemas.lead import LeadCaptureRequest

logger = logging.getLogger(__name__)


async def send_lead_to_webhook(lead: LeadCaptureRequest) -> bool:
    """
    POST lead data to the configured LEAD_CAPTURE_WEBHOOK.

    Returns True if the webhook accepted the payload (2xx response).
    Returns False if the webhook is not configured or the call fails.

    NEVER raises an exception — a webhook failure must not degrade the
    user's experience. The brief has already been delivered. Lead capture
    is best-effort.
    """
    if not settings.LEAD_CAPTURE_WEBHOOK:
        logger.info("Lead capture webhook not configured — skipping.")
        return False

    payload = {
        "name": lead.name,
        "email": lead.email,
        "organisation": lead.organisation,
        "brief_summary": lead.brief_summary or "",
        "infrastructure_recommended": lead.infrastructure_recommended or "",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "source": "ScotlandAI Navigator v1.1",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                settings.LEAD_CAPTURE_WEBHOOK,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            logger.info(
                f"Lead captured for {lead.email} — webhook responded {response.status_code}"
            )
            return True

    except httpx.TimeoutException:
        logger.warning(f"Lead capture webhook timed out for {lead.email}")
        return False

    except httpx.HTTPStatusError as e:
        logger.warning(
            f"Lead capture webhook returned {e.response.status_code} for {lead.email}"
        )
        return False

    except Exception as e:
        logger.error(f"Lead capture webhook failed unexpectedly for {lead.email}: {e}")
        return False
