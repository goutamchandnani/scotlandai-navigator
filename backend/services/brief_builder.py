"""
ScotlandAI Navigator — Brief Builder

This is the core intelligence of the system. It takes five validated discovery
answers and produces a structured AI Opportunity Brief.

HOW IT WORKS:
1. Discovery answers arrive (already validated by Pydantic)
2. Infrastructure is mapped deterministically by Python (services/infrastructure.py)
3. A structured prompt is built combining:
   - The organisation's specific answers
   - DataVita's real infrastructure specs (injected, not generated)
   - The predetermined infrastructure recommendation (decided by Python)
   - Explicit rules: no vague language, no invented data, no jargon
4. Gemini 3 Flash Preview generates the brief as structured JSON
5. The JSON is validated again by Pydantic (schemas/brief.py)
6. If validation fails (vague language, jargon), Gemini retries with a tighter prompt

WHY STRUCTURED JSON OUTPUT:
- Gemini's response_schema feature guarantees valid JSON matching our Pydantic model
- No parsing errors, no malformed output, no "here's your brief:" preamble
- The brief object can be directly rendered as text, PDF, or API response

WHY RETRY LOGIC:
- Even with a good prompt, Gemini occasionally produces vague language
- The retry prompt is more constrained: "Your previous output contained [specific issue]"
- Max 2 retries — if it still fails, we return what we have with a quality flag
"""

import json
import logging
from google import genai
from google.genai import types

from core.config import settings
from knowledge.datavita import get_infrastructure_context
from services.infrastructure import get_infrastructure_for_brief
from schemas.discovery import DiscoveryAnswers
from schemas.brief import BriefResponse, Opportunity

logger = logging.getLogger(__name__)


# ── System Prompt ──
# This defines WHO Gemini is when generating the brief.
# It is NOT the agent's conversational prompt — that's in antigravity_prompt.md.
# This is specifically for the structured brief generation call.

BRIEF_SYSTEM_PROMPT = """You are a senior AI solutions consultant producing a board-ready
AI Opportunity Brief for a Scottish organisation considering AI adoption
on DataVita's infrastructure.

Your output must be:
1. SPECIFIC — every recommendation must reference the organisation's actual data and situation
2. QUANTIFIED — expected impact must include numbers wherever possible
3. ACTIONABLE — a board member reading this must understand what to do next
4. HONEST — never recommend AI products that require data the organisation doesn't have

You must produce output as a valid JSON object matching the provided schema exactly.
No preamble. No markdown. No explanation outside the JSON structure.

RULES YOU MUST FOLLOW:
- Every AI opportunity must use data sources the organisation explicitly mentioned
- Do NOT invent data sources the organisation did not mention
- Executive summary must be 3 sentences, readable by a non-technical board member
- Executive summary must NOT contain: API, LLM, RAG, vector, embedding, inference,
  GPU, kW, PUE, Tier III, co-location, hyperscale, latency, throughput, tokenisation
- Do NOT use vague phrases: 'improve efficiency', 'leverage your data', 'gain insights',
  'AI-powered solution', 'explore opportunities', 'cloud infrastructure'
- Recommended first step must be achievable in 90 days
- Do NOT use words like 'transform', 'overhaul', or 'rebuild' in the first step
- Infrastructure recommendations must match the provided mapping EXACTLY
"""


def _build_user_prompt(
    answers: DiscoveryAnswers,
    infra_context: str,
    workload_type: str,
    infra_recommendation: str,
) -> str:
    """
    Build the user prompt that tells Gemini exactly what to produce.

    The prompt structure is deliberate:
    1. Discovery answers (what we know about this organisation)
    2. Infrastructure context (DataVita's real specs)
    3. Infrastructure mapping (predetermined by Python)
    4. Explicit rules (what NOT to do)
    """
    return f"""Produce an AI Opportunity Brief for this organisation.

DISCOVERY ANSWERS (from a 5-question conversation):
1. Organisation & Bottleneck: {answers.organisation_and_bottleneck}
2. Data Assets: {answers.data_assets}
3. Value of Improvement: {answers.value_of_improvement}
4. Risk Appetite: {answers.risk_appetite.value}
5. Technical Capability: {answers.technical_capability.value}

{infra_context}

INFRASTRUCTURE MAPPING (use this exactly for all 3 opportunities):
Workload classified as: {workload_type}
Recommended facility: {infra_recommendation}

IMPORTANT INSTRUCTIONS:
- Produce exactly 3 AI opportunities, each specific to THIS organisation
- Each opportunity must use ONLY data sources mentioned in answer #2
- Map each opportunity to the infrastructure specified above
- Quantify expected impact using numbers from answer #3 as a baseline
- If risk appetite is 'quick_win', focus on opportunities achievable in 90 days
- If technical capability is 'needs_support', note that DataVita can provide full delivery support
- The recommended first step must be the single smallest, most valuable thing they could do in 90 days
"""


def _get_brief_schema() -> dict:
    """
    Return the JSON schema for structured output.
    This tells Gemini exactly what shape the response must take.
    """
    return {
        "type": "object",
        "properties": {
            "executive_summary": {
                "type": "string",
                "description": "3 sentences maximum. Board-ready. Zero jargon. What AI can do for them, what they should do first, and what the expected impact is."
            },
            "opportunities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Specific name for the AI product"},
                        "what_it_does": {"type": "string", "description": "One sentence: what this AI product does"},
                        "problem_solved": {"type": "string", "description": "One sentence: what problem this solves"},
                        "data_required": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of specific data sources needed (must match what they said they have)"
                        },
                        "expected_impact": {"type": "string", "description": "Quantified: time saved, money saved, outcomes improved"},
                        "infrastructure": {"type": "string", "description": "Specific DataVita facility — use the mapping provided"},
                        "build_complexity": {"type": "string", "enum": ["Simple", "Medium", "Complex"]},
                        "time_to_value": {"type": "string", "description": "How long until this produces value"}
                    },
                    "required": ["name", "what_it_does", "problem_solved", "data_required",
                                 "expected_impact", "infrastructure", "build_complexity", "time_to_value"]
                },
                "minItems": 3,
                "maxItems": 3
            },
            "recommended_first_step": {
                "type": "string",
                "description": "The single most valuable thing achievable in 90 days. Specific and actionable."
            }
        },
        "required": ["executive_summary", "opportunities", "recommended_first_step"]
    }


async def generate_brief(answers: DiscoveryAnswers) -> BriefResponse:
    """
    Generate an AI Opportunity Brief from validated discovery answers.

    This is the main entry point. It:
    1. Maps infrastructure deterministically
    2. Builds the Gemini prompt
    3. Calls Gemini with structured JSON output
    4. Validates the response with Pydantic
    5. Retries if validation fails (up to 2 times)

    Returns a validated BriefResponse ready for PDF generation and API response.
    """
    # Step 1: Deterministic infrastructure mapping (Python, not AI)
    workload_type, infra_rec = get_infrastructure_for_brief(
        organisation_text=answers.organisation_and_bottleneck,
        data_text=answers.data_assets,
    )

    logger.info(f"Workload classified as: {workload_type} → {infra_rec.facility}")

    # Step 2: Build the prompt
    infra_context = get_infrastructure_context()
    user_prompt = _build_user_prompt(
        answers=answers,
        infra_context=infra_context,
        workload_type=workload_type,
        infra_recommendation=f"{infra_rec.facility} — {infra_rec.reason}",
    )

    # Step 3: Call Gemini with retry logic
    max_retries = 2
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            brief_data = await _call_gemini(
                user_prompt=user_prompt,
                attempt=attempt,
                last_error=str(last_error) if last_error else None,
            )

            # Step 4: Validate with Pydantic
            brief = BriefResponse(**brief_data)
            logger.info(f"Brief generated successfully on attempt {attempt + 1}")
            return brief

        except Exception as e:
            last_error = e
            logger.warning(f"Brief generation attempt {attempt + 1} failed: {e}")

            if attempt == max_retries:
                logger.error(f"All {max_retries + 1} attempts failed. Last error: {e}")
                raise ValueError(
                    f"Brief generation failed after {max_retries + 1} attempts. "
                    f"Last error: {e}"
                )

    # Should never reach here, but just in case
    raise ValueError("Brief generation failed unexpectedly")


async def _call_gemini(
    user_prompt: str,
    attempt: int = 0,
    last_error: str | None = None,
) -> dict:
    """
    Call Gemini 3 Flash Preview with structured JSON output.

    Uses the google-genai SDK for clean, typed interaction.
    Temperature 0.3 for brief generation — consistent, specific output.
    """
    # Initialize client
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    # Adjust prompt on retry
    system_prompt = BRIEF_SYSTEM_PROMPT
    if attempt > 0 and last_error:
        system_prompt += f"""

IMPORTANT: Your previous attempt was rejected because: {last_error}
Please fix this specific issue in your new response.
Be MORE specific. Use MORE concrete numbers. Avoid ALL vague language.
"""

    # Call Gemini with structured output
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.3,
            response_mime_type="application/json",
            response_schema=_get_brief_schema(),
        ),
    )

    # Parse the JSON response
    if response.text:
        return json.loads(response.text)
    else:
        raise ValueError("Gemini returned an empty response")


def extract_organisation_name(bottleneck_text: str) -> str:
    """
    Best-effort extraction of the organisation name from their first answer.
    Used for the PDF header — not critical, just presentational.
    """
    # Look for common patterns
    lower = bottleneck_text.lower()

    # "We're a [name] council" or "We are [name]"
    for prefix in ["we're a ", "we are a ", "we're an ", "we are an ",
                    "we're the ", "we are the ", "i work at ", "i work for "]:
        if prefix in lower:
            idx = lower.index(prefix) + len(prefix)
            # Take the next few words as the name
            remaining = bottleneck_text[idx:].strip()
            words = remaining.split()
            # Take up to 4 words or until a common stop word
            stop_words = {"and", "with", "that", "which", "processing", "handling", "managing", "our", "we"}
            name_words = []
            for word in words[:6]:
                if word.lower() in stop_words:
                    break
                name_words.append(word)
            if name_words:
                return " ".join(name_words).rstrip(",.")

    return "Organisation"
