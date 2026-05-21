"""
ScotlandAI Navigator — Discovery Answer Validation

These schemas validate the five answers collected during the discovery conversation
BEFORE they reach Gemini. This is critical because:

  Nonsensical input → nonsensical brief → credibility destroyed

Every validation rule here maps to a specific rule in ai_rules.md.
Pydantic V2 catches problems at the boundary, not in the AI layer.

Why Pydantic, not manual validation:
- Runtime type checking with clear error messages
- Auto-generates OpenAPI documentation
- Field-level validators run before the data leaves this layer
- If validation fails, the agent asks a clarifying question — never sends garbage to Gemini
"""

from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict


class RiskAppetite(str, Enum):
    """How quickly the organisation wants to see results."""
    quick_win = "quick_win"       # Prove value in 90 days
    strategic = "strategic"       # Longer-term transformation
    unknown = "unknown"           # Not sure yet — brief will recommend quick win


class TechnicalCapability(str, Enum):
    """Whether the organisation has internal technical capacity."""
    internal_team = "internal_team"     # Has developers/data team
    needs_support = "needs_support"     # Needs full delivery partner
    unknown = "unknown"                 # Not sure — brief will address both paths


class DiscoveryAnswers(BaseModel):
    """
    The five discovery answers, validated before brief generation.

    Each field maps to one question in the discovery conversation:
    1. organisation_and_bottleneck → "What do you do and what's your biggest pain point?"
    2. data_assets → "What data do you already have digitally?"
    3. value_of_improvement → "What would a meaningful improvement be worth?"
    4. risk_appetite → "Quick win or strategic transformation?"
    5. technical_capability → "Do you have a tech team or need full support?"
    """

    model_config = ConfigDict(
        extra="forbid",  # Reject unexpected fields — security measure
        str_strip_whitespace=True,
    )

    organisation_and_bottleneck: str = Field(
        ...,
        min_length=20,
        max_length=2000,
        description="What the organisation does and their single biggest operational bottleneck",
        examples=[
            "We're a council processing 400 planning applications monthly, each taking 3 hours to review and route manually."
        ],
    )

    data_assets: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="What data the organisation already has in digital form",
        examples=[
            "PDFs of all applications going back 10 years, SQL database tracking decisions, Excel tracker for officer assignments."
        ],
    )

    value_of_improvement: str = Field(
        ...,
        min_length=5,
        max_length=1000,
        description="What a meaningful improvement in the bottleneck would be worth — time, money, or outcomes",
        examples=[
            "About £80,000 per year — roughly 2 full-time officers."
        ],
    )

    risk_appetite: RiskAppetite = Field(
        ...,
        description="Whether the organisation wants a quick win (90 days) or strategic transformation",
    )

    technical_capability: TechnicalCapability = Field(
        ...,
        description="Whether the organisation has internal technical capacity or needs full delivery support",
    )

    # ── Validators ──
    # Each validator prevents a specific failure mode identified in ai_rules.md

    @field_validator("organisation_and_bottleneck")
    @classmethod
    def validate_not_placeholder(cls, v: str) -> str:
        """
        Rule 7 compliance: reject placeholder answers.
        If someone types "N/A" or "test", the agent should ask again,
        not send garbage to Gemini.
        """
        blocked = {"n/a", "na", "none", "nothing", "test", "asdf", "hello", "hi", "xxx"}
        if v.strip().lower() in blocked:
            raise ValueError(
                "Please describe your organisation and its biggest operational challenge. "
                "The more specific you are, the more useful the brief will be."
            )
        return v

    @field_validator("data_assets")
    @classmethod
    def validate_data_mentioned(cls, v: str) -> str:
        """
        Rule 1 compliance: at least one data source must be mentioned.
        Without data, we cannot recommend AI products — we'd be guessing.
        A brief built on guesses destroys trust.
        """
        blocked = {"none", "n/a", "nothing", "no", "no data", "we don't have any"}
        if v.strip().lower() in blocked:
            raise ValueError(
                "Every AI product needs data to work with. Even spreadsheets, email archives, "
                "or paper records that could be digitised count. What do you have?"
            )
        return v

    @field_validator("value_of_improvement")
    @classmethod
    def validate_value_not_zero(cls, v: str) -> str:
        """
        Catch obviously invalid value estimates.
        Free text is accepted — "saves 2 hours a day" is as valid as "£80,000/year".
        """
        blocked = {"0", "nothing", "n/a", "none", "no value", "don't know"}
        if v.strip().lower() in blocked:
            raise ValueError(
                "Any measure is useful — time saved, money saved, fewer errors, faster delivery. "
                "Even a rough estimate helps make the brief specific."
            )
        return v
