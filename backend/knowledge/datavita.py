"""
ScotlandAI Navigator — DataVita Infrastructure Knowledge Base

This is the single source of truth for DataVita's infrastructure specifications.
Every number in this file is sourced from datavita.co.uk.

WHY THIS EXISTS:
- These specs are INJECTED into every Gemini prompt, not generated
- Gemini writes the narrative around the infrastructure — it does NOT choose it
- If Gemini is asked about something not in this file, the agent says
  "I'll confirm those details with the DataVita team"
- This prevents the most dangerous failure mode: a brief with fabricated
  infrastructure specifications that anyone can disprove in 30 seconds

This is not a design choice. It is a trust decision.
"""


# ── DataVita Facility Specifications ──
# Source: datavita.co.uk (verified May 2026)

DATAVITA_INFRASTRUCTURE = {
    "DV1": {
        "name": "DV1 — Lanarkshire (Chapelhall)",
        "location": "Chapelhall, Lanarkshire — central Scotland, between Glasgow and Edinburgh",
        "power": "24MW (expandable to 40MW)",
        "certification": "Uptime Institute Tier III certified — both design AND construction (only such facility in Scotland)",
        "pue": "1.18 — among the best in the UK",
        "cooling": "Air cooling up to 100kW/rack, liquid cooling up to 200kW/rack",
        "energy": "100% renewable",
        "gpu": "CoreWeave Nvidia GPU infrastructure deployed on-site",
        "certifications_list": ["ISO 14001", "ISO 27001", "ISO 42001"],
        "best_for": [
            "AI model training",
            "GPU inference at scale",
            "HPC and research computing",
            "Public sector sovereign data hosting",
            "Large language model workloads",
        ],
    },
    "DV2": {
        "name": "DV2 — Glasgow city centre (177 Bothwell Street)",
        "location": "177 Bothwell Street, Glasgow city centre",
        "power": "1MW",
        "racks": "130",
        "connectivity": "Best connectivity in central Scotland",
        "best_for": [
            "Low-latency city-facing applications",
            "Hybrid cloud deployments",
            "Financial services",
            "Media and content delivery",
            "City council proximity workloads",
        ],
    },
    "DV3": {
        "name": "DV3 — Coming soon (adjacent to DV1)",
        "location": "Adjacent to DV1 in Chapelhall",
        "status": "Planning approved January 2026",
        "best_for": [
            "Overflow capacity for DV1 customers scaling AI workloads",
        ],
    },
    "CoreWeave": {
        "name": "CoreWeave GPU Cloud on DataVita",
        "location": "Deployed at DV1 Lanarkshire",
        "hardware": "Nvidia GPU infrastructure",
        "best_for": [
            "AI model training",
            "Inference at scale",
            "Generative AI workloads",
            "RAG pipelines",
            "Computer vision",
        ],
    },
}


def get_infrastructure_context() -> str:
    """
    Returns the full DataVita infrastructure knowledge base as a string
    suitable for injection into a Gemini prompt.

    This is called on every brief generation request. The specs are
    never cached in a way that could become stale — they are read
    from this source of truth every time.
    """
    lines = [
        "DATAVITA INFRASTRUCTURE SPECIFICATIONS",
        "(Source: datavita.co.uk — verified May 2026)",
        "=" * 60,
        "",
    ]

    for key, facility in DATAVITA_INFRASTRUCTURE.items():
        lines.append(f"### {facility['name']}")
        if "location" in facility:
            lines.append(f"  Location: {facility['location']}")
        if "power" in facility:
            lines.append(f"  Power: {facility['power']}")
        if "certification" in facility:
            lines.append(f"  Certification: {facility['certification']}")
        if "pue" in facility:
            lines.append(f"  PUE: {facility['pue']}")
        if "cooling" in facility:
            lines.append(f"  Cooling: {facility['cooling']}")
        if "energy" in facility:
            lines.append(f"  Energy: {facility['energy']}")
        if "gpu" in facility:
            lines.append(f"  GPU: {facility['gpu']}")
        if "racks" in facility:
            lines.append(f"  Racks: {facility['racks']}")
        if "connectivity" in facility:
            lines.append(f"  Connectivity: {facility['connectivity']}")
        if "hardware" in facility:
            lines.append(f"  Hardware: {facility['hardware']}")
        if "status" in facility:
            lines.append(f"  Status: {facility['status']}")
        if "certifications_list" in facility:
            lines.append(f"  Certifications: {', '.join(facility['certifications_list'])}")
        lines.append(f"  Best for: {', '.join(facility['best_for'])}")
        lines.append("")

    return "\n".join(lines)
