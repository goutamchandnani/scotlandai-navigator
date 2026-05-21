# ScotlandAI Navigator — Architecture

---

## The design principle

Every architectural decision in this system was made by asking one question:
**what is the minimum required to make the output genuinely useful?**

Not the minimum to make it work. The minimum to make it produce a brief
specific enough that a real organisation could take it into a real boardroom.

That question ruled out complexity for complexity's sake. It ruled in
Gemini 3 Flash Preview's medium thinking mode. It ruled in a stateless
backend. It ruled out a vector database. Every decision below follows
from that principle.

---

## System overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        USER CHANNELS                             │
│         Telegram · Slack · WhatsApp · WebChat                    │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                      OPENCLAW GATEWAY                            │
│                                                                  │
│  ┌──────────────────┐     ┌───────────────────────────────────┐ │
│  │  Channel Adapters │────▶│  ScotlandAI Navigator Agent       │ │
│  │  (per platform)   │     │                                   │ │
│  └──────────────────┘     │  antigravity_prompt.md            │ │
│                            │  gemini-3-flash-preview           │ │
│                            │  medium thinking (budget: 8000)   │ │
│                            └──────────────┬────────────────────┘ │
└───────────────────────────────────────────┼──────────────────────┘
                                            │
                              Runs 5-turn discovery
                              conversation natively
                                            │
                              When 5 answers collected:
                              POST /generate-brief
                                            │
                                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND (Python)                       │
│                    Deployed on Render                             │
│                                                                   │
│  ┌─────────────────┐    ┌──────────────────────────────────────┐ │
│  │ /generate-brief  │───▶│  Pydantic validator                  │ │
│  │  POST endpoint   │    │  (validates 5 discovery answers)     │ │
│  └─────────────────┘    └──────────────┬─────────────────────── ┘ │
│                                        │                          │
│                          ┌─────────────▼──────────────┐          │
│                          │  Brief Builder              │          │
│                          │                             │          │
│                          │  1. Builds structured       │          │
│                          │     prompt from answers     │          │
│                          │  2. Injects DataVita infra  │          │
│                          │     knowledge base          │          │
│                          │  3. Calls Gemini API        │          │
│                          │  4. Parses JSON response    │          │
│                          │  5. Assembles brief object  │          │
│                          └─────────────┬───────────────┘          │
│                                        │                           │
│                    ┌───────────────────┴──────────────┐           │
│                    ▼                                  ▼           │
│           ┌────────────────┐              ┌─────────────────────┐ │
│           │  Gemini 3      │              │  ReportLab          │ │
│           │  Flash Preview │              │  PDF Generator      │ │
│           │                │              │                     │ │
│           │  Generates     │              │  Renders brief      │ │
│           │  brief content │              │  as downloadable    │ │
│           │  from          │              │  PDF                │ │
│           │  structured    │              │                     │ │
│           │  data prompt   │              │                     │ │
│           └────────┬───────┘              └──────────┬──────────┘ │
│                    └──────────────────────────────────┘            │
│                                        │                           │
│                    ┌───────────────────▼──────────────┐           │
│                    │  Response assembler               │           │
│                    │  Returns: summary_text, pdf_url,  │           │
│                    │  opportunities[], next_step        │           │
│                    └───────────────────┬───────────────┘           │
└────────────────────────────────────────┼───────────────────────────┘
                                         │
                                         ▼
                          OpenClaw formats and returns
                          brief to user in conversation
```

---

## Layer-by-layer decisions

### Layer 1 — OpenClaw Gateway

**Decision: Run discovery conversation natively in OpenClaw, not in the backend**

The five-question discovery is a multi-turn conversation. OpenClaw handles
multi-turn state natively. If the discovery logic lived in the backend, we would
need to manage session state across HTTP requests — adding a Redis layer or
database that is entirely unnecessary.

By keeping discovery in OpenClaw and only calling the backend when all five
answers are collected, the backend becomes stateless. No sessions. No database.
One POST request in, one brief out.

**Decision: Named agent session scoped to ScotlandAI Navigator**

The agent runs in its own session. This means the system prompt, conversation
history, and context are scoped to the Navigator. A user's discovery answers
do not bleed into other agent sessions.

```json
{
  "agents": {
    "scotland-ai-navigator": {
      "systemPrompt": "path:./antigravity_prompt.md",
      "model": "gemini-3-flash-preview",
      "skills": ["scotland-ai-navigator"]
    }
  }
}
```

---

### Layer 2 — Gemini 3 Flash Preview (conversation layer)

**Decision: Gemini handles the discovery conversation, not a rule-based chatbot**

An early design considered hardcoding the five questions as a simple state machine.
Question 1 → wait → Question 2 → wait → etc.

This was rejected for one reason: the discovery conversation needs to be
**adaptive**. If an organisation says "we're an NHS trust running 14 hospitals,"
the agent should already know their data landscape and ask a more specific
follow-up — not ask them to describe their data from scratch.

That adaptivity requires an LLM. Gemini handles the conversational layer and
the final brief generation. One model, two tasks.

**Decision: Medium thinking level (budget: 8000 tokens)**

Gemini 3 Flash Preview supports configurable thinking. We use medium (8000 tokens)
specifically for brief generation — not for the conversational discovery phase.

Why medium and not minimal: the brief must map AI opportunities to specific
DataVita infrastructure tiers. That requires multi-step reasoning — understanding
the workload, matching it to DV1 vs DV2 vs CoreWeave, estimating infrastructure
requirements, generating specific rather than generic recommendations.

Why not high: the additional reasoning at high thinking level does not improve
structured document generation meaningfully. It adds latency without quality gain.

**Decision: Temperature 0.3 for brief generation, 0.6 for conversation**

Brief generation needs consistency and precision — low temperature.
Discovery conversation needs to feel natural and human — slightly higher.
Two separate Gemini calls with different configs handle this.

---

### Layer 3 — FastAPI Backend

**Decision: FastAPI, not Flask**

Async support enables concurrent Gemini API calls and PDF generation.
Pydantic V2 provides runtime validation of all five discovery answers before
they reach the AI layer. This prevents nonsensical inputs from producing
nonsensical briefs.

**Decision: Stateless — no database**

The backend writes nothing to a database by default. Discovery answers arrive
in the POST request body. The brief is generated and returned. Nothing persists.

This was an explicit architectural choice, not an oversight. Storing discovery
conversations creates GDPR obligations, security surface area, and operational
complexity that adds zero value to v1. The lead capture feature (v1.1) adds
opt-in storage only when the user explicitly consents.

**Decision: Render for deployment**

Free tier. Auto-deploy from GitHub on every push. Persistent URL. Zero config.
Already used for other projects in this portfolio — no new setup required.
Every minute not spent on deployment infrastructure is a minute on product.

---

### Layer 4 — Brief Builder (the most important component)

**What it does:**
Takes five validated discovery answers and builds a structured prompt that
tells Gemini exactly what to produce — including DataVita's actual infrastructure
specifications injected as context.

**Why this is not RAG:**
A vector database and retrieval step would add latency and complexity for a
knowledge base that is small, stable, and fully structured. DataVita's
infrastructure specs fit in under 500 tokens. They are injected directly into
the prompt on every call.

**Why calculations and logic happen here, not in Gemini:**
The infrastructure mapping logic (which workload goes on which DataVita tier)
is deterministic. It is implemented in Python, not delegated to the LLM.

```python
def map_infrastructure(workload_type: str, scale: str) -> InfraRecommendation:
    """
    Deterministic infrastructure mapping.
    No AI. No ambiguity. Always the same answer for the same input.
    """
    if workload_type in ["ai_training", "hpc", "gpu_inference"]:
        return InfraRecommendation(
            facility="DV1 Lanarkshire + CoreWeave GPU",
            reason="GPU workloads require Nvidia infrastructure — deployed at DV1",
            rack_density="Up to 200kW/rack with liquid cooling"
        )
    elif workload_type in ["public_sector", "sovereign_data"]:
        return InfraRecommendation(
            facility="DV1 Lanarkshire",
            reason="Tier III certified, 100% renewable, Scottish sovereign hosting",
            rack_density="Standard to high density available"
        )
    elif workload_type in ["edge", "low_latency", "city_facing"]:
        return InfraRecommendation(
            facility="DV2 Glasgow",
            reason="City centre location, best connectivity in central Scotland",
            rack_density="130 racks, 1MW"
        )
```

Gemini writes the narrative. Python decides the infrastructure. Clean separation.

---

### Layer 5 — PDF Generation (ReportLab)

**Why ReportLab:**
Pure Python. No external service. No API key. No cost. Produces professional
output. The PDF is the artefact the user takes into a boardroom — it needs to
look like it was produced by a consultancy, not a chatbot.

**What the PDF contains:**
- DataVita header and branding context
- Generation timestamp
- All five discovery answers (so the user can verify the brief reflects
  what they said)
- Full AI Opportunity Brief
- Recommended next step
- DataVita contact information

---

## Data flow — end to end

```
1.  User: "What could AI do for my council?"
2.  OpenClaw → ScotlandAI Navigator agent session
3.  Agent begins discovery conversation (5 turns)
4.  Turn 1-5: Gemini handles conversation natively in OpenClaw
5.  After Turn 5: skill fires POST /generate-brief to FastAPI
6.  Pydantic validates all five answers
7.  Brief Builder:
    a. Classifies organisation type and workload
    b. Maps infrastructure deterministically (Python)
    c. Builds structured prompt with DataVita specs injected
    d. Calls Gemini 3 Flash Preview (temp 0.3, thinking budget 8000)
    e. Parses JSON response into brief object
8.  ReportLab renders PDF from brief object
9.  PDF served via pre-signed URL (60-min expiry)
10. FastAPI returns: { summary, opportunities[], pdf_url, next_step }
11. OpenClaw formats and returns to user
```

---

## Prompt structure (Brief Builder → Gemini)

```python
SYSTEM = """
You are a senior AI solutions consultant producing a board-ready
AI Opportunity Brief for a Scottish organisation considering AI adoption
on DataVita's infrastructure.

Produce output as a valid JSON object only. No preamble. No markdown.
Exactly this structure:
{
  "executive_summary": "string (3 sentences max)",
  "opportunities": [
    {
      "name": "string",
      "what_it_does": "string (1 sentence)",
      "problem_solved": "string (1 sentence)",
      "data_required": ["list of specific data sources"],
      "expected_impact": "string (quantified where possible)",
      "infrastructure": "string (specific DataVita tier)",
      "build_complexity": "Simple | Medium | Complex",
      "time_to_value": "string (e.g. 90 days)"
    }
  ],
  "recommended_first_step": "string (specific and actionable)"
}
"""

USER = f"""
Produce an AI Opportunity Brief for this organisation.

DISCOVERY ANSWERS:
1. What they do / biggest bottleneck: {answers.bottleneck}
2. Data they have: {answers.data_assets}
3. Value of 10% improvement: {answers.value_of_improvement}
4. Risk appetite: {answers.risk_appetite}
5. Technical capability: {answers.technical_capability}

DATAVITA INFRASTRUCTURE CONTEXT:
{DATAVITA_INFRA_KNOWLEDGE_BASE}

INFRASTRUCTURE MAPPING (use exactly):
{infrastructure_recommendation}

Rules:
- Every opportunity must use specific data the organisation said they have
- Every infrastructure recommendation must match the mapping above exactly
- Executive summary must be readable by a non-technical board member
- Recommended first step must be achievable in 90 days
- Do not invent data sources the organisation did not mention
"""
```

---

## Security decisions

| Decision | Reason |
|----------|--------|
| No persistent storage by default | Discovery answers are commercially sensitive operational data |
| Pydantic validation on all inputs | Prevents injection, catches malformed answers before Gemini |
| API keys in environment only | Never logged, never transmitted to client |
| PDF pre-signed URLs, 60-min expiry | Briefs contain strategic information — not public indefinitely |
| Stateless backend | Zero data liability, zero GDPR complexity in v1 |
| Gemini processes transiently | No training on submitted data |

---

## What this architecture does not do (and why)

**No RAG / vector database**
DataVita's infrastructure knowledge base is under 500 tokens. Injected directly.
RAG adds latency and infrastructure cost for a problem that does not need it.

**No user authentication in v1**
The discovery conversation contains no sensitive personal data. The brief
belongs to the user. Authentication adds friction that reduces completion rate
without adding meaningful security for v1.

**No streaming**
The brief is assembled and returned complete. A partial brief is worse than a
15-second wait — particularly if the user intends to download the PDF.

**No database**
Stateless design eliminates GDPR obligations, operational complexity, and
infrastructure cost. Lead capture (v1.1) adds opt-in storage only.

---

## Built with Antigravity IDE

This entire codebase was architected and built using Google Antigravity 2.0 —
Google's agent-first IDE powered by Gemini 3. Multiple parallel agents planned
the architecture, wrote the backend, tested the API endpoints, and flagged edge
cases. The developer's role was architect and mission controller: reviewing agent
output, making decisions, directing the next task.

This is not a footnote. It is deliberate. ScotlandAI Navigator is a tool about
AI doing work that humans currently do manually. It was built the same way.
