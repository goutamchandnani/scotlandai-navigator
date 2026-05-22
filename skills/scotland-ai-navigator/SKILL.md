---
name: scotland-ai-navigator
description: >
  Helps any Scottish organisation discover what AI could do for them.
  Runs a five-question conversational discovery, then produces a structured,
  board-ready AI Opportunity Brief with three specific AI products mapped to
  DataVita's real infrastructure — DV1, DV2, and CoreWeave GPU. Turns a cold
  inquiry into a warm lead for DataVita's AI Solutions team in under 10 minutes.
version: 1.1.0
metadata:
  openclaw:
    requires:
      env:
        - GEMINI_API_KEY
        - NAVIGATOR_API_URL
      bins:
        - curl
        - python3
    primaryEnv: GEMINI_API_KEY
    envVars:
      - name: GEMINI_API_KEY
        required: true
        description: >
          Google Gemini API key. Used to power the discovery conversation
          and AI Opportunity Brief generation via Gemini 3 Flash Preview.
          Get one free at aistudio.google.com.
      - name: NAVIGATOR_API_URL
        required: true
        description: >
          Base URL of the deployed ScotlandAI Navigator FastAPI backend.
          Example: https://scotland-ai-navigator.onrender.com
          Must be internet-accessible. Set after deploying to Render.
      - name: LEAD_CAPTURE_WEBHOOK
        required: false
        description: >
          Webhook URL (Airtable, Make, Zapier, or any HTTP endpoint) to
          receive opted-in lead data when a user says yes to DataVita
          follow-up after their brief. Payload includes name, email,
          organisation, brief executive summary, and infrastructure
          recommendation. If not set, the opt-in prompt is still shown
          but contact data is logged server-side only. Enable by setting
          this variable — no code change required.
      - name: PDF_EXPIRY_MINUTES
        required: false
        description: >
          How long generated PDF brief links remain valid, in minutes.
          Defaults to 60. Increase for demos where judges may revisit links.
    emoji: "🏴󠁧󠁢󠁳󠁣󠁴󠁿"
    user-invocable: true
    slash-command: navigator
    homepage: https://github.com/Goutamchandnani/scotland-ai-navigator
---

# ScotlandAI Navigator 🏴󠁧󠁢󠁳󠁣󠁴󠁿

Turn any Scottish organisation's AI ambition into a concrete, board-ready
opportunity brief — in under 10 minutes, from any messaging app.

---

## What this skill does

ScotlandAI Navigator runs a short, conversational discovery with any organisation
that wants to understand what AI could do for them. It asks five intelligent
questions — one at a time, adapting based on answers — then calls the Navigator
backend to produce a structured AI Opportunity Brief.

The brief contains three specific AI products the organisation could realistically
build, each mapped to the right tier of DataVita's infrastructure (DV1 Lanarkshire,
DV2 Glasgow, or CoreWeave GPU), with a recommended 90-day first step and an
executive summary ready to take to a board.

Every output is a warm, qualified lead for DataVita's AI Solutions team.

---

## Why this skill exists

Danny Quinn, Managing Director of DataVita, wrote:

> "Many of the people making decisions about AI infrastructure in Scotland
> simply don't understand what's at stake. The path we collectively choose
> today will define our country for decades."

DataVita's AI Solutions team closes this understanding gap manually today —
discovery meetings, senior people, weeks of elapsed time before a recommendation
exists. That process does not scale against DataVita's ambitions: a £44.9M
Glasgow City Council contract, UCL's £19.5M supercomputer, CoreWeave GPU
infrastructure, and plans for 500MW of capacity.

ScotlandAI Navigator closes the gap in minutes. Automatically. At scale.
On any channel.

---

## Trigger phrases

The agent responds to any of these:

- `what could ai do for us`
- `we want to explore ai`
- `ai opportunity`
- `scotland ai navigator`
- `/navigator`
- `help us get started with ai`
- `what ai should we build`

---

## Conversation flow

```
User: What could AI do for our council?

Agent: Great timing — AI is transforming what councils can deliver,
       and Scotland has some of the best infrastructure in Europe to
       run it on.

       Let me ask you five quick questions and I'll put together a
       specific brief you can take to your leadership team.

       First: what does your council actually struggle with most
       operationally right now? The thing that eats the most time
       or causes the most friction?

User: Planning applications. We get 400 a month and each one takes
      3 hours to review and route manually.

Agent: That's a significant workload — and exactly the kind of
       structured, repetitive process where AI creates real, fast ROI.

       Second question: what data do you already have digitally?
       Things like document systems, databases, spreadsheets,
       case management tools?

User: We have all applications as PDFs going back 10 years,
      a SQL database tracking decisions, and an Excel tracker
      for officer assignments.

Agent: Perfect — that's a strong data foundation. Three more questions.

       What would a 20% reduction in that planning application workload
       be worth to your council — roughly, in staff time or budget?

User: Probably 2 full-time officers. Around £80,000 a year.

Agent: Understood. Two more:

       Are you looking to prove something works quickly — say a 90-day
       pilot — or are you thinking about a longer strategic transformation?

User: Quick win first. We need to show results before we can get
      more budget.

Agent: Makes sense. Last question:

       Do you have an internal IT or data team who could support
       a build, or would you need full delivery support from a partner?

User: We have two developers but they've never worked with AI before.

Agent: Got everything I need. Building your brief now...

       ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
       🏴󠁧󠁢󠁳󠁣󠁴󠁿 SCOTLAND AI OPPORTUNITY BRIEF
       Organisation: [Council Name]
       Generated: 21 May 2026
       ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

       EXECUTIVE SUMMARY
       Your council processes 400 planning applications per month through
       a manual review process costing approximately 1,200 staff hours.
       AI can automate the classification and routing of these applications,
       saving an estimated £80,000 per year from day one of deployment.
       The fastest path to proving this is a 90-day pilot using your
       existing 10 years of PDF applications as a training dataset.

       OPPORTUNITY 1 — Planning Application Triage Agent
       What it does: Reads incoming PDF applications, classifies by type
         and complexity, extracts key criteria, routes to the right officer
       Data required: Your existing PDF archive + SQL decisions database
       Expected impact: ~2 hours saved per application × 400/month = £80k/yr
       Infrastructure: DV1 Lanarkshire — document processing at scale,
         sovereign Scottish hosting for sensitive planning data
       Build complexity: Medium
       Time to first value: 90 days

       OPPORTUNITY 2 — [second opportunity]
       ...

       OPPORTUNITY 3 — [third opportunity]
       ...

       RECOMMENDED FIRST STEP
       Run a 90-day pilot: take the last 500 planning applications from
       your archive, build a classifier that routes them correctly, and
       measure accuracy against your officers' actual decisions. If it
       hits 85%+ accuracy — which is typical for this type of document —
       you have the internal case for full deployment.

        📎 Full PDF brief: [download — valid 60 min]

        To explore any of these on DataVita's infrastructure:
        datavita.co.uk/contact | AI Solutions team

        ─────────────────────────────────────────────
        Would you like DataVita's AI Solutions team to reach
        out and talk through any of these with you? If yes,
        just share your name and email.

User:   Yes — Jane Smith, jane.smith@fife.gov.uk

Agent:  Done. The team will be in touch at jane.smith@fife.gov.uk.
        The PDF brief has everything they need to get started.
```

---

## Discovery questions (reference)

The agent asks these one at a time, adapting based on answers:

1. **Bottleneck:** What does your organisation do and what is your single
   biggest operational pain point right now?

2. **Data:** What data do you already have digitally?
   (Documents, databases, spreadsheets, sensor feeds, transaction logs)

3. **Value:** What would a meaningful improvement in that bottleneck be worth?
   (Time, money, or outcomes — any measure is useful)

4. **Risk appetite:** Are you looking for a quick win in 90 days,
   or a longer strategic transformation?

5. **Technical capability:** Do you have an internal technical team,
   or would you need full delivery support?

---

## Output — AI Opportunity Brief

The brief always contains:

- **Executive summary** — 3 sentences, board-ready, zero jargon
- **3 AI opportunities** — each with: use case, problem solved, data required,
  expected impact (quantified), DataVita infrastructure mapping,
  build complexity, time to first value
- **Recommended first step** — specific, achievable in 90 days
- **DataVita contact** — AI Solutions team link
- **Downloadable PDF** — formatted for professional presentation (60-min link)

---

## Infrastructure mapping (how the brief chooses the right DataVita tier)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/generate-brief` | Generate an AI Opportunity Brief from 5 discovery answers |
| `POST` | `/capture-lead` | Forward opted-in lead data to the LEAD_CAPTURE_WEBHOOK (v1.1) |
| `GET` | `/download/{token}` | Download a generated PDF brief (60-min link) |
| `GET` | `/health` | Service health check (also reports lead_capture: enabled/disabled) |

| Workload type | DataVita recommendation |
|---------------|------------------------|
| AI model training, GPU inference, HPC | DV1 Lanarkshire + CoreWeave GPU |
| Public sector, sovereign data, NHS, councils | DV1 Lanarkshire |
| Research computing, university HPC | DV1 Lanarkshire |
| Low-latency, city-facing, hybrid cloud | DV2 Glasgow (177 Bothwell St) |
| Scaling from pilot to production | DV1 or DV3 (coming soon) |

Infrastructure mapping is deterministic Python — not delegated to the AI.
Gemini writes the narrative. Python decides the infrastructure. Always.

---

## DataVita infrastructure facts used in briefs

All specifications are sourced directly from datavita.co.uk.
The skill never invents or estimates these figures.

**DV1 — Lanarkshire (Chapelhall):**
- 24MW power (expandable to 40MW)
- Uptime Institute Tier III certified — design AND construction
  (only such facility in Scotland)
- PUE: 1.18 — among the best in the UK
- Cooling: air up to 100kW/rack, liquid up to 200kW/rack
- 100% renewable energy
- CoreWeave Nvidia GPU infrastructure deployed on-site
- ISO 14001, ISO 27001, ISO 42001 certified

**DV2 — Glasgow city centre (177 Bothwell Street):**
- 1MW power, 130 racks
- Best connectivity in central Scotland
- City centre location

**DV3 — Coming soon:**
- Adjacent to DV1 in Chapelhall
- Planning approved January 2026

---

## Environment setup

```bash
# Required
export GEMINI_API_KEY=your_key_from_aistudio_google_com
export NAVIGATOR_API_URL=https://your-app.onrender.com

# Optional
export LEAD_CAPTURE_WEBHOOK=https://your-webhook-url
export PDF_EXPIRY_MINUTES=60
```

---

## Backend deployment

The FastAPI backend must be deployed and internet-accessible before this skill
will function. The skill calls `POST /generate-brief` on the backend URL.

```bash
git clone https://github.com/Goutamchandnani/scotland-ai-navigator
cd scotland-ai-navigator/backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Recommended: Deploy to Render**
1. Push repo to GitHub
2. New Web Service on Render → connect repo
3. Set `GEMINI_API_KEY` in environment variables
4. Copy the `.onrender.com` URL → set as `NAVIGATOR_API_URL`

---

## OpenClaw agent configuration

Add to `~/.openclaw/openclaw.json`:

```json
{
  "agents": {
    "scotland-ai-navigator": {
      "systemPrompt": "path:./skills/scotland-ai-navigator/antigravity_prompt.md",
      "model": "gemini-3-flash-preview",
      "skills": ["scotland-ai-navigator"],
      "thinking": {
        "budget": 8000
      }
    }
  },
  "env": {
    "GEMINI_API_KEY": "your_key",
    "NAVIGATOR_API_URL": "https://your-app.onrender.com"
  }
}
```

---

## Install from ClawHub

```bash
openclaw skills install scotland-ai-navigator

# Or from local directory:
openclaw skills install ./skills/scotland-ai-navigator
```

---

## Security notes

- No user data is stored without explicit consent
- All API keys stored in environment — never logged or transmitted to client
- Discovery answers processed transiently — no database writes by default
- PDF brief links expire after 60 minutes (configurable)
- Lead capture only activates if `LEAD_CAPTURE_WEBHOOK` is set AND user opts in
- Backend validates all inputs with Pydantic before they reach Gemini
- Gemini processes data transiently — no training on submitted answers

For ClawScan: this skill makes outbound HTTP calls to:
- `$NAVIGATOR_API_URL/generate-brief` (POST — your own backend)
- `$LEAD_CAPTURE_WEBHOOK` (POST — only if set and user consents)
No other outbound connections. No shell commands. No file system access.

---

## Built for the DataVita OpenClaw Challenge — May 2026

This skill was built as a submission for DataVita's OpenClaw Challenge.
The challenge asked entrants to build something that matters — not something
that is merely clever.

ScotlandAI Navigator matters because it directly addresses the problem
Danny Quinn has been writing about for months: the gap between Scotland's
AI ambitions and the organisations that stand to benefit most from them.

Built by Goutam Chandnani · goutamchandnani.netlify.app
