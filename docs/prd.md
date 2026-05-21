# ScotlandAI Navigator — Product Requirements Document (prd.md)

---

## The problem

Danny Quinn wrote this in October 2025:

> "Many of the people making decisions about AI infrastructure in Scotland
> simply don't understand what's at stake. The path we collectively choose
> today will define our country for decades."

He was not writing about technology. He was writing about a gap — the gap between
organisations that could transform their operations with AI and the knowledge
required to take the first step.

DataVita's AI Solutions team closes that gap manually today. A prospect calls.
A discovery meeting is booked. Senior people spend hours understanding the
organisation's operations, data, and goals before they can produce a recommendation.
That process does not scale. DataVita has a £44.9M Glasgow City Council contract,
a UCL supercomputer, CoreWeave GPU infrastructure, and plans for 500MW of capacity.
The pipeline of organisations that need this conversation is enormous. The team
that can have it is small.

ScotlandAI Navigator is the tool that closes this gap at scale.

---

## What it is

ScotlandAI Navigator is an OpenClaw agent. Any Scottish organisation — a council,
an NHS trust, a logistics company, a university, a financial services firm — can
message it from Telegram, Slack, WhatsApp, or any platform OpenClaw supports.

Through a five-question conversational discovery process, the agent builds a
complete picture of the organisation's operations, data assets, and goals. It then
produces a structured AI Opportunity Brief: three specific AI products they could
build, mapped to the right DataVita infrastructure tier, with an executive summary
they can take directly to their board.

Every output is a warm lead for DataVita's AI Solutions team.

---

## Who it is for

**Primary users:**
- Operations directors, IT leads, and digital transformation managers at
  Scottish public sector organisations (councils, NHS, universities)
- CTO/CIO equivalents at Scottish SMEs and enterprise businesses
- DataVita's own sales and AI Solutions team — to pre-qualify and accelerate
  the discovery phase with inbound prospects

**Secondary users:**
- DataVita prospects at events, conferences, and trade shows — scan a QR code,
  start a conversation on the spot

---

## Goals

| Goal | Metric | Target |
|------|--------|--------|
| Close the AI understanding gap | Organisations completing full discovery | ≥ 80% completion rate from first message to brief |
| Generate pipeline for AI Solutions team | Briefs produced per week | Measurable from week 1 |
| Reduce discovery time | Time from first contact to scoped opportunity | From weeks → under 10 minutes |
| Demonstrate DataVita's expertise | Quality of brief output | Brief should be good enough to present at board level |

---

## User journey

```
Step 1 — Entry
  User messages on any OpenClaw-connected channel:
  "I want to explore AI for my organisation"
  or "What could AI do for us?"
  or any variation

Step 2 — Discovery (5 questions, conversational, one at a time)
  Q1: What does your organisation do and what is your biggest operational bottleneck?
  Q2: What data do you already have?
  Q3: What would a 10% improvement in that bottleneck be worth?
  Q4: Risk appetite — quick win or strategic transformation?
  Q5: Internal technical team or need full delivery support?

Step 3 — Brief generation
  Agent sends answers to FastAPI backend
  Backend calls Gemini 3 Flash Preview with structured prompt
  Gemini generates the AI Opportunity Brief
  Backend returns brief to OpenClaw

Step 4 — Delivery
  Agent returns formatted brief to user in conversation
  PDF version available via download link
  User receives: "To explore any of these with DataVita's AI Solutions team,
  contact datavita.co.uk/contact"

Step 5 — Lead capture (optional, with consent)
  If user opts in, brief + contact info logged for DataVita AI Solutions team
```

---

## Functional requirements

### FR1 — Conversational discovery
The agent must conduct a natural, multi-turn conversation collecting five
structured data points. It must not present these as a form. It must adapt
follow-up questions based on previous answers.

### FR2 — Brief generation
Given five discovery answers, the backend must produce a structured AI
Opportunity Brief containing:
- Executive summary (3 sentences, board-ready)
- Three specific AI opportunities with full detail
- Infrastructure mapping to DataVita's actual DV1/DV2/CoreWeave offerings
- Recommended 90-day first step

### FR3 — Infrastructure mapping
Every AI opportunity in the brief must include a specific DataVita infrastructure
recommendation based on workload type. Generic recommendations ("cloud hosting")
are not acceptable.

### FR4 — PDF export
The brief must be exportable as a downloadable PDF, formatted for professional
presentation. Links expire after 60 minutes.

### FR5 — Multi-channel support
The agent must function identically across Telegram, Slack, and WebChat via
OpenClaw's channel adapters.

### FR6 — Graceful degradation
If the Gemini API is unavailable, the agent returns a structured text version
of the brief and retries PDF generation. It never returns a blank or error
message to the user without a recovery path.

### FR7 — No persistent data storage (default)
User discovery answers are processed transiently. No database writes occur
unless the user explicitly opts into lead capture.

### FR8 — Input validation
Discovery answers are validated before being sent to Gemini. Nonsensical or
empty responses trigger a gentle clarifying question, not an error.

---

## Non-functional requirements

| Requirement | Target |
|-------------|--------|
| End-to-end response time (brief generation) | Under 15 seconds |
| Uptime | 99.5% (Render free tier is sufficient for demo) |
| Brief quality | Every opportunity must be specific enough to act on |
| Security | No user data stored without consent. API keys in env only. |
| Cost per brief | Under £0.01 at Gemini 3 Flash Preview pricing |

---

## Out of scope (v1)

- CRM integration (DataVita's sales team follows up manually from brief)
- Pricing calculator (handled by DataVita sales team)
- Multi-language support (English only, v1)
- User authentication (open access, v1)
- Analytics dashboard (v2 roadmap)

---

## Success criteria for the competition submission

The submission succeeds if a judge can:

1. Message the agent and receive a complete, specific, board-ready AI
   Opportunity Brief within 15 minutes of first contact

2. Read the README and immediately understand why this tool exists,
   who it is for, and what problem it solves for DataVita specifically

3. Look at the Git history and see clean, thoughtful commits that
   tell the story of how the product was built

4. Read the architecture.md and understand every technical decision
   and why it was made

5. Ask themselves: "Would DataVita's AI Solutions team actually use this?"
   and answer yes

---

## The product in one sentence

ScotlandAI Navigator turns a cold inquiry into a board-ready AI Opportunity Brief
in under 10 minutes — so DataVita's AI Solutions team spends their time building
products, not explaining what AI is.

---

## Roadmap (post-competition, if hired)

**v1.1 — Lead capture with consent**
Optional opt-in at end of brief: "Want DataVita's AI Solutions team to follow up?
Leave your name and email." Captured to a simple webhook or Airtable.

**v1.2 — Industry-specific discovery tracks**
Specialised question sets for NHS, local government, logistics, financial services.
Faster, more accurate briefs for known verticals.

**v1.3 — Analytics**
How many briefs generated. Which sectors. Which AI opportunities appear most
frequently. Feeds DataVita's market intelligence.

**v2.0 — Full proposal generation**
From Opportunity Brief to full project proposal with effort estimates,
risk register, and delivery timeline. The AI Solutions team reviews and sends.
