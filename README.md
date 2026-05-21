# 🏴󠁧󠁢󠁳󠁣󠁴󠁿 ScotlandAI Navigator

**Turn any Scottish organisation's AI ambition into a concrete, board-ready opportunity brief — in under 10 minutes.**

---

## The Problem

Danny Quinn, Managing Director of DataVita, wrote:

> *"Many of the people making decisions about AI infrastructure in Scotland simply don't understand what's at stake. The path we collectively choose today will define our country for decades."*

DataVita's AI Solutions team closes the AI understanding gap manually today — discovery meetings, senior people, weeks of elapsed time before a recommendation exists. That process does not scale against DataVita's ambitions: a £44.9M Glasgow City Council contract, UCL's £19.5M supercomputer, CoreWeave GPU infrastructure, and plans for 500MW of capacity.

**ScotlandAI Navigator closes this gap in minutes. Automatically. At scale.**

---

## What It Does

ScotlandAI Navigator is an AI agent that any Scottish organisation can talk to — from Telegram, Slack, WhatsApp, or any OpenClaw-connected channel.

It asks **five intelligent questions** — one at a time, like a conversation, not a form — then produces a structured **AI Opportunity Brief** containing:

- **3 specific AI products** the organisation could realistically build
- Each mapped to the **right DataVita infrastructure tier** (DV1, DV2, or CoreWeave GPU)
- A **recommended 90-day first step** — specific enough to act on immediately
- An **executive summary** a non-technical board member can read and understand
- A **downloadable PDF** formatted for professional presentation

Every output is a warm, qualified lead for DataVita's AI Solutions team.

---

## How It Works

```
User messages:  "What could AI do for our council?"
        │
        ▼
   5-question discovery conversation
   (adaptive, one question at a time)
        │
        ▼
   FastAPI backend validates answers
   Python maps infrastructure (deterministic — not AI)
   Gemini generates the brief content
   ReportLab renders a professional PDF
        │
        ▼
   Board-ready AI Opportunity Brief
   + downloadable PDF (60-min link)
```

---

## Project Structure

```
├── skills/scotland-ai-navigator/   # OpenClaw agent skill
│   ├── SKILL.md                     # Skill manifest
│   ├── antigravity_prompt.md        # Agent system prompt
│   └── ai_rules.md                  # 10 rules governing AI behaviour
│
├── backend/                         # FastAPI backend
│   ├── main.py                      # App entry point
│   ├── core/config.py               # Environment-based configuration
│   ├── schemas/                     # Pydantic validation models
│   ├── services/                    # Brief builder, infra mapping, PDF gen
│   └── knowledge/                   # Hard-coded DataVita specifications
│
├── docs/                            # Design documentation
│   ├── architecture.md              # Every technical decision explained
│   └── prd.md                       # Product requirements
│
├── render.yaml                      # One-click Render deployment
└── openclaw.json                    # OpenClaw agent configuration
```

---

## Tech Stack & Why

| Technology | What it does | Why this, not something else |
|-----------|-------------|------------------------------|
| **Gemini 3 Flash Preview** | Generates brief content | Fast, cheap (<£0.01/brief), structured JSON output |
| **FastAPI** | Backend API | Async, auto-validates with Pydantic, auto-generates docs |
| **Pydantic V2** | Input validation | Catches nonsense answers before they reach the AI |
| **ReportLab** | PDF generation | Pure Python, no external service, professional output |
| **itsdangerous** | Download links | 60-min expiry tokens without needing a database |
| **Render** | Deployment | Auto-deploy from GitHub, free tier, zero config |

---

## Quick Start

```bash
# Clone
git clone https://github.com/Goutamchandnani/ScotlandAI-Navigator.git
cd ScotlandAI-Navigator/backend

# Install dependencies
pip install -r requirements.txt

# Set your Gemini API key
export GEMINI_API_KEY=your_key_from_aistudio_google_com

# Run
uvicorn main:app --reload
```

---

## Built for the DataVita OpenClaw Challenge — May 2026

This skill was built because it directly addresses the problem Danny Quinn has been writing about: the gap between Scotland's AI ambitions and the organisations that stand to benefit most from them.

ScotlandAI Navigator is not merely clever. It matters.

**Built by Goutam Chandnani** · [goutamchandnani.netlify.app](https://goutamchandnani.netlify.app)
