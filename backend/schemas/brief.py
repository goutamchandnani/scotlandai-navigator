"""
ScotlandAI Navigator — Brief Response Schemas

These schemas validate what Gemini PRODUCES, not what the user sends.
This is the second validation boundary:

  1. Discovery answers validated before Gemini sees them (discovery.py)
  2. Brief content validated after Gemini produces it (this file)

If Gemini's output contains vague language, technical jargon in the
executive summary, or fewer than 3 opportunities — it's rejected and
Gemini is asked to try again.

This double validation is why the output is consistently specific and
board-ready, not generic AI slop.
"""

from typing import Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict


# ── Banned Phrases (from ai_rules.md Rule 2) ──
# If any of these appear in an opportunity, the brief is rejected.
BANNED_OPPORTUNITY_PHRASES = [
    "improve efficiency",
    "leverage your data",
    "gain insights",
    "ai-powered solution",
    "explore opportunities",
    "cloud infrastructure",
    "digital transformation",
    "unlock value",
    "harness the power",
    "cutting-edge",
    "next-generation",
    "state-of-the-art",
]

# ── Blocked Executive Summary Terms (from ai_rules.md Rule 4) ──
# Technical jargon that a non-technical board member should never see.
BLOCKED_EXEC_TERMS = [
    "API", "LLM", "RAG", "vector", "embedding", "inference",
    "GPU", "kW", "PUE", "Tier III", "co-location", "hyperscale",
    "latency", "throughput", "tokenisation", "tokenization",
    "fine-tuning", "fine tuning", "neural network", "transformer",
]


class Opportunity(BaseModel):
    """
    A single AI opportunity in the brief.
    Must be specific enough that a board member can understand
    what would be built, why it matters, and where it would run.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        ...,
        min_length=5,
        max_length=200,
        description="Name of the AI product — specific, not generic",
        examples=["Planning Application Triage Agent"],
    )

    what_it_does: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="One sentence: what this AI product actually does",
    )

    problem_solved: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="One sentence: what specific problem this solves for the organisation",
    )

    data_required: list[str] = Field(
        ...,
        min_length=1,
        description="Specific data sources needed — must match what the organisation said they have",
        examples=[["PDF planning applications archive", "SQL decisions database"]],
    )

    expected_impact: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Quantified impact — time saved, money saved, outcomes improved",
        examples=["~2 hours saved per application × 400/month = approximately £80,000/year"],
    )

    infrastructure: str = Field(
        ...,
        min_length=5,
        max_length=300,
        description="Specific DataVita infrastructure tier — DV1, DV2, or CoreWeave GPU",
        examples=["DV1 Lanarkshire — sovereign Scottish hosting for sensitive planning data"],
    )

    build_complexity: Literal["Simple", "Medium", "Complex"] = Field(
        ...,
        description="How complex this is to build",
    )

    time_to_value: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="How long until this produces value — e.g. '90 days'",
    )

    @field_validator("what_it_does", "problem_solved", "expected_impact")
    @classmethod
    def reject_vague_language(cls, v: str) -> str:
        """Rule 2: No vague, generic language in opportunities."""
        lower = v.lower()
        for phrase in BANNED_OPPORTUNITY_PHRASES:
            if phrase in lower:
                raise ValueError(
                    f"Vague language detected: '{phrase}'. "
                    f"Every opportunity must be specific to this organisation's actual situation."
                )
        return v


class BriefResponse(BaseModel):
    """
    The complete AI Opportunity Brief returned to the user.

    This is what gets presented at board level. Every field is validated
    to ensure it meets the quality bar defined in ai_rules.md.
    """

    model_config = ConfigDict(extra="forbid")

    executive_summary: str = Field(
        ...,
        min_length=50,
        max_length=1000,
        description="3 sentences, board-ready, zero jargon",
    )

    opportunities: list[Opportunity] = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Exactly 3 specific AI opportunities",
    )

    recommended_first_step: str = Field(
        ...,
        min_length=20,
        max_length=500,
        description="The single most valuable thing achievable in 90 days",
    )

    @field_validator("executive_summary")
    @classmethod
    def validate_readability(cls, v: str) -> str:
        """
        Rule 4: Executive summary must be readable by a non-technical board member.
        If it contains jargon, it's rejected.
        """
        for term in BLOCKED_EXEC_TERMS:
            # Case-sensitive check for acronyms (API, LLM, RAG, GPU)
            # Case-insensitive for regular words
            if term.isupper():
                if term in v:
                    raise ValueError(
                        f"Executive summary contains technical jargon: '{term}'. "
                        f"This summary must be readable by a non-technical board member."
                    )
            else:
                if term.lower() in v.lower():
                    raise ValueError(
                        f"Executive summary contains technical jargon: '{term}'. "
                        f"This summary must be readable by a non-technical board member."
                    )
        return v

    @field_validator("recommended_first_step")
    @classmethod
    def validate_achievable(cls, v: str) -> str:
        """
        Rule 5: First step must be achievable, not transformational.
        Words like 'transform' or 'overhaul' signal something too big for 90 days.
        """
        blocked_words = ["transform", "overhaul", "rebuild", "replace entirely", "complete redesign"]
        lower = v.lower()
        for word in blocked_words:
            if word in lower:
                raise ValueError(
                    f"Recommended first step contains '{word}'. "
                    f"The first step must be achievable in 90 days — specific and small enough to start."
                )
        return v


class APIBriefResponse(BriefResponse):
    """Extended brief response with PDF download URL — this is what the API returns."""

    model_config = ConfigDict(extra="allow")

    organisation_name: str = Field(
        default="Organisation",
        description="Extracted or inferred organisation name",
    )

    pdf_url: str | None = Field(
        default=None,
        description="Pre-signed download URL for the PDF brief (valid 60 minutes)",
    )

    next_step: str = Field(
        default="To explore any of these opportunities on DataVita's infrastructure, contact the AI Solutions team at datavita.co.uk/contact",
        description="CTA for DataVita",
    )
