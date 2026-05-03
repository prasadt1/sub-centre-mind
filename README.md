# Sub-Centre Mind

**Local-first clinical decision support for India's ANMs, powered by Gemma 4 E4B**

[![Hackathon](https://img.shields.io/badge/Gemma%204%20Good-Health%20%26%20Sciences-blue)](https://www.kaggle.com/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Model](https://img.shields.io/badge/model-Gemma%204%20E4B-orange)](https://ollama.com/)

## Overview

Sub-Centre Mind is a clinical decision support tool designed for Auxiliary Nurse Midwives (ANMs) managing 5,000+ patients across India's rural sub-centres. It operates on a **strict Data Sovereignty model**: all reasoning, RAG, and Patient Health Information (PHI) processing happens locally on a $200 edge device using Gemma 4 E4B. The cloud (WhatsApp) is used purely as a redacted transport layer for nudge delivery. The "brain" never leaves the room.
### Core Capabilities

- **Protocol-grounded Q&A**: Answers questions about IFA dosing, ANC schedules, immunization protocols using RAG over MoHFW/WHO guidelines
- **Safe refusal boundaries**: Refuses diagnostic queries (BP interpretation, insulin dosing, bleeding assessment) and escalates to named Medical Officers
- **Closed-loop nudges**: WhatsApp reminders for IFA compliance and ANC visits, with confirmation tracking ("ली" = taken)
- **Administrative Relief (Stretch v1)**: Auto-drafts mandatory HMIS / RCH-1 monthly reports by linking numeric figures directly to verifiable source Message IDs, ensuring auditability without adding data-entry burden.
- **Multilingual**: Hindi, Marathi, English support

## Engineering Lineage

Direct fork of **AgriNexus AI** (AWS Builder 10K AIdeas Innovation Award, April 2026) — reuses the closed-loop nudge state machine, adapted from agricultural advisories to maternal health protocols.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    ANM (User)                       │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
         ┌────────────────────┐
         │   Query Router     │
         │  (boundary_card)   │
         └────────┬───────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
┌──────────────┐    ┌──────────────────┐
│  RAG Engine  │    │ Refusal Handler  │
│ (MoHFW PDFs) │    │  + Escalation    │
└──────┬───────┘    └──────────────────┘
       │
       ▼
┌──────────────────────┐
│   Gemma 4 E4B        │
│   (Ollama local)     │
└──────────────────────┘
       │
       ▼
┌──────────────────────┐
│  Nudge Engine        │
│  (WhatsApp loop)     │
└──────────────────────┘
```

## Decision Boundary Card

The **Decision Boundary Card** (`boundary_card.json`) is the machine-readable specification of what the model answers, refuses, and escalates. This is the primary artifact for hackathon evaluation.

**v0.1 Requirements**:
- ≥15 answerable queries (IFA, ANC, immunization protocols)
- ≥15 refusal triggers (diagnostic overreach, prescriptive queries)

## Gate 1 Criteria (May 5, 18:00 CET)

Must pass ALL 4:

1. ✅ Function calling returns valid JSON with `refuse_and_escalate` tool call
2. ✅ 5/5 refusals trigger correctly (BP, insulin, bleeding, metformin, TB diagnosis)
3. ✅ Multilingual RAG: Hindi + Marathi queries return relevant chunks (>0.7 similarity)
4. ✅ Latency ≤12s per query

## Prior Art & Differentiation

While previous Gemma hackathon winners (e.g., ASHA-G) successfully tackled field-worker *digitization* (OCR/Voice-to-text for ASHAs), Sub-Centre Mind pivots to **Clinical Decision Support and Administrative Relief** for the ANM at the sub-centre desk. 
* **Different Artifact:** We do not digitize forms; we publish a deterministic refusal contract (Decision Boundary Card).
* **Different UX:** We prioritize safety-first refusal over generic Q&A.
* **Different Outcome:** We reduce the clinical liability and reporting backlog of the ANM, rather than adding a new digital workflow.

## Quick Start

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/) installed
- Gemma 4 E4B model: `ollama pull gemma4:latest`

### Installation

```bash
# Clone repository
git clone <repo-url>
cd sub-centre-mind

# Install dependencies
pip install -r requirements.txt

# Verify Gemma 4 is available
ollama list | grep gemma4
```

### Smoke Test

```bash
ollama run gemma4:latest "IFA tablet dose for pregnant women per MoHFW?"
```

Expected: Response about 180 tablets (1 daily for 180 days post-conception).

### Run RAG Pipeline

```bash
python src/rag/ingest.py  # Index MoHFW PDFs
python src/rag/query.py "गर्भवती महिलांसाठी IFA डोस काय आहे?"  # Marathi query
```

### Demo UI (Streamlit, all local)

```bash
# Warm Ollama once for fast first-token
bash scripts/warmup.sh

# Launch the demo (opens http://127.0.0.1:8501)
bash scripts/run_app.sh
```

Four tabs:

- **Ask** — protocol Q&A with retrieval, confidence gate, citations, optional tool-calling round-trip; **voice input** (Hindi/Marathi/English) via local Whisper
- **Photo** — Gemma 4 vision on bounded use cases: printed protocol OCR, medicine pack (always escalates), ANC register row → draft fields
- **Nudges** — closed-loop follow-up state machine, persisted to `data/nudges/store.json` (no live WhatsApp/SMS in v1)
- **Report** — audit JSONL → aggregate stats → draft supervisor summary (optional Gemma narrative)

### Tests & audit draft report

```bash
pytest tests/ -q
python scripts/report_from_logs.py --log data/logs/sample_events.jsonl
# Optional: append JSONL audit lines when smoke-testing RAG
SCM_AUDIT_LOG=data/logs/dev_events.jsonl python scripts/rag_smoke.py "IFA schedule pregnancy"
```

## Project Structure

```
sub-centre-mind/
├── src/
│   ├── rag/              # RAG pipeline (ingest, query, retrieval, gate, generate)
│   ├── audit/            # JSONL audit schema + aggregate / draft helpers
│   ├── nudges/           # State machine + JSON store + Dispatcher Protocol
│   ├── vision/           # Gemma 4 vision client (bounded clinical-adjacent prompts)
│   ├── voice/            # Local Whisper ASR (faster-whisper, lazy)
│   └── query_router.py   # Retrieval-injected /api/chat with Gate 1 tools
├── app/
│   └── streamlit_app.py  # Local 3-tab demo UI (Ask / Nudges / Report)
├── data/
│   ├── health-corpus/    # MoHFW/WHO PDFs
│   ├── index/            # FAISS + BM25 + chunks.json
│   ├── logs/             # Audit JSONL (sample_events.jsonl tracked)
│   └── nudges/           # Persistent nudge state (gitignored)
├── tests/                # Pytest suite (gate, nudges, store, dispatcher, report, integration)
├── docs/                 # CORPUS, ARCHITECTURE, NEXT, writeup-qa-hardquestions, etc.
├── scripts/              # ask, rag_smoke, g1_checks, run_app, run_nudges, warmup, report_from_logs
├── boundary_card.json    # Decision Boundary Card
└── requirements.txt
```

## What We Refuse to Claim
To maintain intellectual honesty in a complex global health domain, this project explicitly does **not** attempt to solve: physical transport logistics, sub-centre facility capacity, ASHA compensation models, or household decision-making dynamics. We provide grounded decision support; we do not replace clinical judgment.

## Hard Constraints

- **Gemma 4 E4B via Ollama ONLY** — no Bedrock/OpenAI/Claude in inference path
- **No vision in v1** — text-only queries
- **PHI never leaves device** — all processing local
- **Health & Sciences track only**

## Roadmap

See [docs/NEXT.md](docs/NEXT.md) for the full 25-task build checklist across 4 phases.

## License

MIT License - see [LICENSE](LICENSE)

## Author

**Prasad Tilloo** ([@prasadt1](https://github.com/prasadt1))  
AWS Builder 10K AIdeas Innovation Award Winner (April 2026) — AgriNexus AI

## Acknowledgments

- **Gemma 4 Good Hackathon** — Kaggle/Google DeepMind
- **AgriNexus AI** — engineering foundation for closed-loop nudge system
- **MoHFW** — maternal health protocols and guidelines
