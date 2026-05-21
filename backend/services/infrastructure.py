"""
ScotlandAI Navigator — Deterministic Infrastructure Mapping

THIS IS THE MOST IMPORTANT ARCHITECTURAL DECISION IN THE ENTIRE SYSTEM.

Gemini writes the narrative. Python decides the infrastructure. Always.

Why:
- Infrastructure recommendations must be 100% accurate — a wrong PUE figure,
  an invented rack density, or a facility that doesn't exist is immediately
  detectable by anyone who checks datavita.co.uk
- AI is probabilistic. Infrastructure mapping must be deterministic.
- By keeping this in Python, we guarantee the right answer every time,
  regardless of how Gemini is feeling on any given API call

How it works:
1. The Brief Builder classifies the organisation's workload type from their answers
2. This module maps that classification to the correct DataVita facility
3. The mapping result is INJECTED into Gemini's prompt as a constraint
4. Gemini writes the narrative AROUND the predetermined infrastructure choice
"""

from dataclasses import dataclass


@dataclass
class InfraRecommendation:
    """A deterministic infrastructure recommendation for an AI opportunity."""
    facility: str
    facility_short: str
    reason: str
    key_specs: str


# ── Workload Classification Keywords ──
# Used to detect the type of workload from the organisation's answers

GPU_KEYWORDS = [
    "training", "train", "model", "machine learning", "deep learning",
    "neural", "computer vision", "image recognition", "nlp",
    "natural language", "generative", "llm", "large language",
    "inference", "gpu", "hpc", "supercomput", "research computing",
]

PUBLIC_SECTOR_KEYWORDS = [
    "council", "nhs", "hospital", "government", "public sector",
    "health board", "education", "university", "school", "police",
    "fire", "ambulance", "social work", "housing", "planning",
    "sovereign", "citizen", "patient", "pupil", "resident",
]

CITY_FACING_KEYWORDS = [
    "real-time", "realtime", "real time", "low latency", "edge",
    "city", "urban", "iot", "sensor", "live", "streaming",
    "financial", "fintech", "trading", "media", "broadcast",
    "content delivery", "hybrid cloud",
]


def classify_workload(text: str) -> str:
    """
    Classify the organisation's workload type from their discovery answers.
    Returns one of: 'gpu_intensive', 'public_sector', 'city_facing', 'general'

    The classification is intentionally simple — keyword matching, not AI.
    This is a feature, not a limitation. Deterministic > clever.
    """
    lower = text.lower()

    # Check for GPU/HPC workloads first (highest infrastructure tier)
    gpu_score = sum(1 for kw in GPU_KEYWORDS if kw in lower)
    public_score = sum(1 for kw in PUBLIC_SECTOR_KEYWORDS if kw in lower)
    city_score = sum(1 for kw in CITY_FACING_KEYWORDS if kw in lower)

    # If strong GPU signal, map to CoreWeave + DV1
    if gpu_score >= 2:
        return "gpu_intensive"

    # Public sector organisations get sovereign hosting at DV1
    if public_score >= 2:
        return "public_sector"

    # City-facing, low-latency workloads go to DV2 Glasgow
    if city_score >= 2:
        return "city_facing"

    # Single keyword matches — use the strongest signal
    if gpu_score > 0:
        return "gpu_intensive"
    if public_score > 0:
        return "public_sector"
    if city_score > 0:
        return "city_facing"

    # Default: DV1 is the safest recommendation for general workloads
    return "general"


def map_infrastructure(workload_type: str) -> InfraRecommendation:
    """
    Map a workload classification to a specific DataVita facility.

    No AI. No ambiguity. Always the same answer for the same input.

    This is called once per opportunity in the brief. The result is injected
    into the Gemini prompt so it writes the narrative around the correct facility.
    """
    mapping = {
        "gpu_intensive": InfraRecommendation(
            facility="DV1 Lanarkshire + CoreWeave GPU",
            facility_short="DV1 + CoreWeave",
            reason=(
                "GPU workloads require Nvidia infrastructure — deployed at DV1 Lanarkshire. "
                "CoreWeave provides scalable GPU compute for AI training and inference. "
                "DV1 offers up to 200kW/rack with liquid cooling for high-density GPU deployments."
            ),
            key_specs="24MW power, Tier III certified, PUE 1.18, 100% renewable, liquid cooling to 200kW/rack",
        ),
        "public_sector": InfraRecommendation(
            facility="DV1 Lanarkshire",
            facility_short="DV1",
            reason=(
                "Public sector data requires sovereign Scottish hosting with the highest "
                "certification standards. DV1 is Uptime Institute Tier III certified for "
                "both design and construction — the only such facility in Scotland. "
                "ISO 27001 and ISO 42001 certified. 100% renewable energy."
            ),
            key_specs="Tier III certified, ISO 27001, ISO 42001, 100% renewable, sovereign Scottish hosting",
        ),
        "city_facing": InfraRecommendation(
            facility="DV2 Glasgow (177 Bothwell Street)",
            facility_short="DV2",
            reason=(
                "Low-latency, city-facing workloads benefit from DV2's Glasgow city centre "
                "location — the best-connected facility in central Scotland. Ideal for "
                "hybrid cloud, financial services, and applications that need proximity "
                "to users and partners in Glasgow."
            ),
            key_specs="1MW, 130 racks, Glasgow city centre, best connectivity in central Scotland",
        ),
        "general": InfraRecommendation(
            facility="DV1 Lanarkshire",
            facility_short="DV1",
            reason=(
                "DV1 Lanarkshire provides the most versatile infrastructure in Scotland — "
                "suitable for everything from document processing to AI-powered analytics. "
                "Tier III certified, 100% renewable, with room to scale from pilot to production."
            ),
            key_specs="24MW (expandable to 40MW), Tier III, PUE 1.18, 100% renewable",
        ),
    }

    return mapping.get(workload_type, mapping["general"])


def get_infrastructure_for_brief(
    organisation_text: str,
    data_text: str,
) -> tuple[str, InfraRecommendation]:
    """
    Full pipeline: takes the organisation's answers, classifies the workload,
    and returns the infrastructure recommendation.

    Returns (workload_type, recommendation) so the Brief Builder can include
    both the classification reasoning and the facility details in the prompt.
    """
    # Combine relevant text for classification
    combined = f"{organisation_text} {data_text}"
    workload_type = classify_workload(combined)
    recommendation = map_infrastructure(workload_type)
    return workload_type, recommendation
