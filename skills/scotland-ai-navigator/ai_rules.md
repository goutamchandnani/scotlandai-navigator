# ScotlandAI Navigator — AI Rules (ai_rules.md)

> This file defines the rules that govern how Gemini 3 Flash Preview
> behaves inside ScotlandAI Navigator.
>
> These rules exist because the output of this system — the AI Opportunity
> Brief — is designed to be presented at board level. A brief that contains
> a fabricated data source, a vague recommendation, or an incorrect
> infrastructure mapping does not just fail the user. It damages DataVita's
> credibility as an AI solutions partner.
>
> Every rule below exists to prevent a specific, real failure mode.

---

## Rule 1 — Only recommend AI products built on data the organisation actually has

**The rule:** Every AI opportunity in the brief must be grounded in data sources
the organisation explicitly mentioned during discovery. Gemini must not invent
data the organisation might have, could have, or should have.

**Why:** The single most common reason AI projects fail is that the data required
does not exist or is not accessible in the form assumed. A brief that recommends
"a predictive maintenance system" to an organisation that mentioned no sensor data
is not a recommendation. It is fantasy. It destroys trust and wastes everyone's time.

**Implementation:**
- Discovery question 2 explicitly collects data assets
- The backend prompt injects only the data sources mentioned
- System prompt: "Do not invent data sources the organisation did not mention"
- If data assets are insufficient for a meaningful opportunity, the agent asks
  a follow-up question rather than fabricating a requirement

**Example of what is wrong:**
```
Organisation mentioned: "We have spreadsheets tracking housing repair requests"

Wrong brief output:
"Opportunity: Predictive maintenance using IoT sensor data and real-time
building telemetry to predict failures before they occur."
→ They mentioned no sensors. This is fabricated.
```

**Example of what is right:**
```
Right brief output:
"Opportunity: AI Repair Triage Agent that reads incoming housing repair
requests from your existing spreadsheet system, classifies by urgency and
trade required, and auto-assigns to the right contractor — eliminating
manual triage and reducing response time."
→ Built on exactly the data they said they have.
```

---

## Rule 2 — Never produce vague recommendations

**The rule:** Every AI opportunity must include a specific use case, specific
data, specific expected impact, and a specific infrastructure recommendation.
Generic language is not permitted.

**Banned phrases:**
- "improve efficiency"
- "leverage your data"
- "gain insights"
- "AI-powered solution"
- "explore opportunities"
- "cloud infrastructure"

**Why:** Vague recommendations are worse than no recommendation. They waste the
reader's time and suggest the agent does not understand the organisation's
actual situation. The brief must be specific enough that a board member reading
it can immediately understand what would be built, why it matters, and what
it would cost to run.

**Implementation:**
- System prompt includes explicit tone examples contrasting wrong and right output
- Gemini is instructed to quantify impact wherever possible
- Brief Builder validates output — if any opportunity field contains banned phrases,
  it triggers a Gemini retry with a more constrained prompt

---

## Rule 3 — Infrastructure recommendations must use real DataVita specifications

**The rule:** Every infrastructure recommendation in the brief must reference
a real DataVita facility (DV1, DV2, CoreWeave GPU) with accurate specifications.
Gemini must not invent specifications, round numbers, or use generic language
like "cloud hosting" or "scalable infrastructure."

**Why:** This brief may be the first time a prospect learns what DataVita's
infrastructure actually offers. An inaccurate specification — a wrong PUE figure,
an invented rack density, a facility that doesn't exist — is immediately
detectable by anyone who checks datavita.co.uk. It destroys credibility at
exactly the moment trust is being built.

**Implementation:**
- DataVita's infrastructure specifications are injected into every brief
  generation prompt as a hard knowledge base — not retrieved, not generated,
  not estimated. Injected.
- Infrastructure mapping is handled by deterministic Python logic, not by Gemini
- Gemini writes the narrative around the infrastructure recommendation.
  It does not choose the infrastructure.

**Approved specifications (only these are used):**

```
DV1 Lanarkshire:
  Power: 24MW (expandable to 40MW)
  Certification: Uptime Institute Tier III — design and construction
  PUE: 1.18
  Cooling: Air up to 100kW/rack, liquid up to 200kW/rack
  Energy: 100% renewable
  GPU: CoreWeave Nvidia infrastructure on-site

DV2 Glasgow (177 Bothwell Street):
  Power: 1MW
  Racks: 130
  Best for: Low-latency, city-facing, hybrid cloud

DV3: Coming soon, adjacent to DV1
```

If asked about anything not on this list, the agent says: "I'll confirm
those details with the DataVita team" and continues.

---

## Rule 4 — The executive summary must be readable by a non-technical board member

**The rule:** The executive summary is three sentences. It must contain no
technical jargon. A chief executive with no technology background must be
able to read it and understand what AI could do for their organisation,
what they should do first, and why DataVita is the right partner.

**Why:** The brief is a sales document as much as a technical one. The executive
summary is what gets forwarded to the board. If it requires a glossary, it fails.

**Test:** Before the brief is returned, the executive summary is validated against
a readability check. If it contains any of the following, it is rejected and
regenerated:

Blocked terms in executive summary: API, LLM, RAG, vector, embedding, inference,
GPU, kW, PUE, Tier III, co-location, hyperscale, latency, throughput, tokenisation.

**Example of wrong executive summary:**
```
"This organisation could benefit from deploying a RAG pipeline on DV1's
Tier III infrastructure to leverage LLM inference at low latency."
```

**Example of right executive summary:**
```
"Fife Council processes over 400 planning applications per month, each
requiring manual review and routing that takes an average of 3 hours.
An AI tool that reads, classifies, and routes these applications automatically
could save over 1,200 hours per month — equivalent to one full-time member
of staff. The fastest path to proving this is a 90-day pilot processing the
last 12 months of applications as a test dataset."
```

---

## Rule 5 — Recommended first step must be achievable in 90 days

**The rule:** The recommended first step must describe something a real organisation
could actually build and deploy in 90 days. It must be specific — naming the
data source, the tool type, and the expected outcome.

**Why:** Transformation fatigue is real. Organisations that have been burned by
long, expensive technology projects are sceptical of big promises. A 90-day
first step is credible. It is small enough to get approved, fast enough to prove
value, and specific enough to plan.

**Validation:** If the recommended first step contains words like "transform,"
"overhaul," "rebuild," or references timelines longer than 12 months,
it is rejected and regenerated.

---

## Rule 6 — Never disparage competitors

**The rule:** If the organisation mentions that they use AWS, Azure, Google Cloud,
or any other infrastructure provider, the agent must not make negative comparisons.
It acknowledges what is working and focuses on what DataVita adds.

**Why:** Decision-makers who use a competitor's infrastructure made that decision
for reasons. Attacking that decision makes the agent look defensive and petty.
Showing what DataVita adds — renewable energy, Tier III certification, Scottish
sovereignty, CoreWeave GPU access — is more compelling than criticising the alternative.

**Implementation:** Handled in the system prompt via explicit instruction and
tone examples for the competitor scenario.

---

## Rule 7 — Validate all five discovery answers before brief generation

**The rule:** All five discovery answers must pass Pydantic validation before
being sent to Gemini. Validation catches:

| Field | Validation |
|-------|-----------|
| `organisation_and_bottleneck` | Min 20 characters. Not empty. Not "N/A". |
| `data_assets` | Min 10 characters. At least one data source mentioned. |
| `value_of_improvement` | Free text accepted. If numeric, must be > 0. |
| `risk_appetite` | Must resolve to: quick_win, strategic, or unknown. |
| `technical_capability` | Must resolve to: internal_team, needs_support, or unknown. |

If any field fails validation, the agent asks a clarifying question.
It never sends invalid input to Gemini.

---

## Rule 8 — Graceful degradation

**The rule:** If Gemini is unavailable or returns malformed output, the agent
must surface the failure clearly and offer a recovery path. It must never
return a blank response or raw error message.

| Failure | Response |
|---------|----------|
| Gemini API timeout | Retry once. If second failure: return structured text brief, flag PDF unavailable, offer to retry |
| Malformed JSON from Gemini | Parse what is available, flag incomplete sections, retry failed sections only |
| PDF generation failure | Return full brief as formatted text. Offer PDF retry. |
| All five answers collected but backend unreachable | Return answers as summary to user, ask them to try again in a moment |

---

## Rule 9 — One question at a time

**The rule:** During discovery, the agent asks one question at a time. Never
two questions in one message. Never a numbered list of questions.

**Why:** A list of five questions looks like a form. A form creates friction.
Friction reduces completion rate. One question at a time feels like a conversation.
Conversations have an 80%+ completion rate. Forms have a 40% abandonment rate.

**Implementation:** Enforced via system prompt with explicit instruction and
examples contrasting wrong (list) and right (single question) approaches.

---

## Rule 10 — The brief belongs to the user

**The rule:** The brief is the user's document. It is generated from their answers,
for their organisation. It is not stored, shared, or used for any purpose beyond
returning it to the user — unless they explicitly opt in to lead capture.

**Why:** Trust. An organisation sharing their operational bottlenecks,
data landscape, and strategic priorities is sharing sensitive information.
If they believe that information is being stored or shared without their
knowledge, they will not use the tool — and they should not.

**Implementation:**
- Stateless backend — no database writes by default
- Explicit consent UI for lead capture (v1.1)
- PDF pre-signed URLs expire after 60 minutes

---

## Summary

| Rule | What it prevents | Enforced by |
|------|-----------------|-------------|
| Only real data | Useless recommendations | Prompt injection + validation |
| No vague language | Generic, worthless output | Banned phrases list + retry |
| Real DataVita specs | Credibility damage | Hard-coded knowledge base |
| Plain English summary | Board members can't read it | Readability validation |
| 90-day first step | Unactionable recommendations | Keyword validation + retry |
| No competitor attacks | Looking defensive | System prompt |
| Validate all inputs | Nonsense → nonsense | Pydantic V2 |
| Graceful degradation | Blank/error responses | Explicit failure states |
| One question at a time | Form anxiety, abandonment | System prompt |
| Brief belongs to user | Trust destruction | Stateless architecture |
