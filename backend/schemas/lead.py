"""
ScotlandAI Navigator — Lead Capture Schemas (v1.1)

Two models cover the lead capture flow:

  LeadCaptureRequest  — what the OpenClaw agent POSTs to /capture-lead
                        (name, email, brief summary, org context)

  WebhookPayload      — what this backend forwards to the configured
                        LEAD_CAPTURE_WEBHOOK (Airtable, Make, Zapier, etc.)

WHY SEPARATE MODELS:
  The agent sends minimal data (what the user volunteered).
  The webhook payload enriches it with server-side metadata
  (timestamp, brief summary, infrastructure recommendation) so
  DataVita's sales team has full context without needing to ask again.

CONSENT:
  This endpoint only activates when a user explicitly opts in during
  the post-brief conversation. The agent never calls this endpoint
  without a clear "yes" from the user. Rule 10 compliance.
"""

from datetime import datetime, timezone
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class LeadCaptureRequest(BaseModel):
    """
    Data sent from the OpenClaw agent to POST /capture-lead.
    The user volunteered this information after receiving their brief.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    name: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Contact's full name",
        examples=["Jane Smith"],
    )

    email: EmailStr = Field(
        ...,
        description="Contact's email address — validated format",
        examples=["jane.smith@example.gov.uk"],
    )

    organisation: str = Field(
        ...,
        min_length=2,
        max_length=500,
        description="Organisation name or description (from brief context)",
        examples=["Fife Council"],
    )

    brief_summary: str | None = Field(
        default=None,
        max_length=2000,
        description="Executive summary from their brief — gives sales team instant context",
    )

    infrastructure_recommended: str | None = Field(
        default=None,
        max_length=200,
        description="DataVita infrastructure tier recommended in the brief",
        examples=["DV1 Lanarkshire"],
    )


class LeadCaptureResponse(BaseModel):
    """Returned to the agent after a successful lead capture."""

    success: bool
    message: str
