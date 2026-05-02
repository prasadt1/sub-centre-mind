# Sub-Centre Mind — Architecture Documentation

**Version**: 0.1  
**Date**: May 2, 2026  
**Target**: Gemma 4 Good Hackathon (Health & Sciences Track)

---

## Table of Contents

1. [System Overview](#system-overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Component Details](#component-details)
4. [Data Flow Diagrams](#data-flow-diagrams)
5. [Decision Boundary System](#decision-boundary-system)
6. [Deployment Architecture](#deployment-architecture)
7. [Technology Stack](#technology-stack)
8. [Security & Privacy](#security--privacy)

---

## System Overview

**Sub-Centre Mind** is a local-first clinical decision support system for India's Auxiliary Nurse Midwives (ANMs). It provides protocol-grounded answers, refuses diagnostic/prescriptive queries, and automates follow-up nudges—all running offline on edge hardware.

### Core Capabilities

- **Protocol Q&A**: Answers questions about IFA dosing, ANC schedules, immunization protocols using RAG over MoHFW/WHO PDFs
- **Safe Refusal**: Refuses diagnostic queries (BP interpretation, insulin dosing) and escalates to Medical Officers
- **Closed-Loop Nudges**: WhatsApp reminders for IFA compliance and ANC visits with confirmation tracking
- **Multilingual**: Hindi, Marathi, English support

### Design Principles

1. **Local-First**: All processing on-device, PHI never leaves the sub-centre
2. **Refusal-First**: Explicit boundaries prevent diagnostic overreach
3. **Auditable**: Every decision traceable via Decision Boundary Card
4. **Edge-Compatible**: Runs on ₹15K mini-PC with 8GB RAM

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         ANM (User)                              │
│                    WhatsApp / CLI Interface                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │   Query Router       │
                  │  (boundary_card.json)│
                  └──────────┬───────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
    ┌─────────────────┐          ┌──────────────────┐
    │  RAG Pipeline   │          │ Refusal Handler  │
    │                 │          │  + Escalation    │
    │ • Intent Detect │          │                  │
    │ • FAISS Retriev │          │ • Tool Calling   │
    │ • Reranking     │          │ • MO Notification│
    └────────┬────────┘          └──────────────────┘
             │
             ▼
    ┌─────────────────────┐
    │   Gemma 4 E4B       │
    │   (Ollama Local)    │
    │   think: false      │
    └────────┬────────────┘
             │
             ▼
    ┌─────────────────────┐
    │  Nudge Engine       │
    │  (WhatsApp Loop)    │
    │                     │
    │ • State Machine     │
    │ • Scheduler         │
    │ • Confirmation Track│
    └─────────────────────┘
```

---

## Component Details

### 1. Query Router

**Purpose**: Classify incoming queries as answerable (protocol) or refusal (diagnostic/prescriptive)

**Implementation**: `boundary_card.json` + function calling

**Logic**:
```
IF query matches diagnostic/prescriptive pattern:
    → Call refuse_and_escalate(reason, target, urgency)
ELSE IF query matches protocol pattern:
    → Route to RAG Pipeline
ELSE:
    → Default to refusal (safe fallback)
```

**Key Files**:
- `boundary_card.json`: Machine-readable refusal contract (16 answerable + 16 refusal entries)
- `scripts/g1_checks.sh`: Validation script for tool calling

---

### 2. RAG Pipeline

**Purpose**: Retrieve relevant chunks from MoHFW/WHO PDFs and generate grounded answers

**Architecture**:

```
Query (Hindi/Marathi/English)
    ↓
Intent Detection (IFA vs Calcium vs Generic)
    ↓
Multilingual Embedding (paraphrase-multilingual-MiniLM-L12-v2)
    ↓
FAISS Retrieval (top-48 candidates, cosine similarity)
    ↓
Intent Reranking (boost IFA chunks for IFA queries, etc.)
    ↓
Top-5 Chunks (score >0.7 threshold)
    ↓
Prompt Construction (chunks + safety rules)
    ↓
Gemma 4 Generation (think: false, num_predict: 220)
    ↓
Answer + Citations (source file + page number)
```

**Key Features**:

- **Intent Reranking**: Solves IFA vs Calcium confusion using multilingual keywords
  - English: "IFA", "iron", "ferrous", "anemia"
  - Hindi: "आयरन", "लौह", "अनेमिया"
  - Marathi: "आयरनचे", "आयर्नचे"
  
- **Hybrid Scoring**: `final_score = semantic_score × intent_boost`
  - Strong intent match: 1.35× boost
  - Weak intent match: 1.15× boost
  - No match: 1.0× (semantic only)

- **Citation Traceability**: Every answer includes `[1] filename.pdf p.42 (score=0.85)`

**Key Files**:
- `src/rag/ingest.py`: PDF → chunks → FAISS index
- `src/rag/query.py`: Retrieval + intent reranking
- `src/rag/intent.py`: Multilingual intent detection
- `src/rag/generate.py`: Answer generation with citations
- `data/index/`: FAISS index (1790 chunks from 11 PDFs)

---

### 3. Refusal Handler

**Purpose**: Refuse diagnostic/prescriptive queries and escalate to Medical Officer

**Function Schema**:

```json
{
  "name": "refuse_and_escalate",
  "parameters": {
    "reason": "BP interpretation requires Medical Officer assessment",
    "escalation_target": "Medical Officer",
    "urgency": "high",
    "case_summary": "ANM query: BP reading 140/90 requires clinical interpretation"
  }
}
```

**Escalation Urgency Levels**:
- **Critical**: Bleeding, seizures, severe complications (immediate MO contact)
- **High**: BP readings, insulin dosing, lab interpretation (same-day MO contact)
- **Medium**: Suspected TB, rash diagnosis, medication queries (24-hour MO contact)
- **Low**: General health questions (routine follow-up)

**Key Files**:
- `boundary_card.json`: Refusal triggers (16 entries)
- `scripts/g1_checks.sh`: Validates 5 core refusals

---

### 4. Gemma 4 E4B (Local Inference)

**Model**: `gemma4:latest` (9.6 GB, E4B variant)

**Configuration**:
```json
{
  "model": "gemma4:latest",
  "think": false,           // Critical: Disables thinking mode (20s → 2s latency)
  "stream": false,
  "options": {
    "num_predict": 220,     // Limit response length
    "temperature": 0.1      // Low temperature for factual responses
  }
}
```

**Performance**:
- First load: 8.6s (model loading)
- Subsequent queries: 2.1s average
- Gate 1 target: <12s ✅

**Why Gemma 4**:
1. Native function calling (for refusal routing)
2. Multilingual performance (Hindi/Marathi)
3. Open weights + local inference (data sovereignty)

---

### 5. Nudge Engine

**Purpose**: Automated WhatsApp reminders for IFA compliance and ANC visits

**State Machine** (adapted from AgriNexus AI):

```
pending_ifa → ifa_sent → ifa_confirmed → next_cycle
     ↓            ↓            ↓
  overdue_1   overdue_2   overdue_3 → escalate_to_anm
```

**Confirmation Tracking**:
- Patient replies "ली" (Marathi: "taken") → state transitions to `confirmed`
- No reply after 3 days → state transitions to `overdue_1`
- 3 missed confirmations → escalate to ANM for follow-up

**Key Files** (Phase 5, not yet implemented):
- `src/nudges/state_machine.py`: State transitions
- `src/nudges/scheduler.py`: Daily IFA, ANC visit reminders
- `src/nudges/send.py`: WhatsApp message formatting
- `src/nudges/receive.py`: Parse "ली" confirmation

---

## Data Flow Diagrams

### Flow 1: Protocol Query (Answerable)

```
ANM: "IFA tablet dose for pregnant women per MoHFW?"
    ↓
Query Router: Matches protocol pattern
    ↓
Intent Detection: Detects IFA intent
    ↓
FAISS Retrieval: Finds WHO-IFA-pregnant-women-2012.pdf chunks
    ↓
Intent Reranking: Boosts IFA-specific chunks (1.35× score)
    ↓
Top-5 Chunks: [WHO p.12 (0.92), MCP p.45 (0.88), ...]
    ↓
Gemma 4 Generation: "180 tablets (1 daily for 180 days post-conception)"
    ↓
Response: Answer + Citations
    [1] WHO-IFA-pregnant-women-2012.pdf p.12 (score=0.92)
    [2] MCP-Guide-Book-2018.pdf p.45 (score=0.88)
```

**Latency**: 2.1s (retrieval: 0.3s, generation: 1.8s)

---

### Flow 2: Diagnostic Query (Refusal)

```
ANM: "Is 140/90 high BP?"
    ↓
Query Router: Matches diagnostic pattern
    ↓
Gemma 4 Tool Calling: refuse_and_escalate(
    reason="BP interpretation requires Medical Officer",
    escalation_target="Medical Officer",
    urgency="high",
    case_summary="ANM query: BP 140/90 interpretation"
)
    ↓
Escalation Handler: Format message for MO
    ↓
Response: "This query requires Medical Officer assessment. 
           Escalated to Dr. Sharma (urgency: high)."
    ↓
Log: Query + tool call + timestamp → data/logs/queries.jsonl
```

**Latency**: 1.8s (no retrieval, direct tool call)

---

### Flow 3: Multilingual Query (Hindi)

```
ANM: "गर्भवती महिलाओं के लिए IFA टैबलेट की खुराक क्या है?"
    ↓
Intent Detection: Detects "आयरन" → IFA intent
    ↓
Multilingual Embedding: Encodes Hindi query
    ↓
FAISS Retrieval: Finds relevant chunks (language-agnostic)
    ↓
Intent Reranking: Boosts IFA chunks
    ↓
Gemma 4 Generation: Responds in Hindi
    "गर्भवती महिलाओं के लिए 180 IFA टैबलेट (प्रतिदिन 1, 180 दिन)"
    ↓
Response: Hindi answer + English citations
```

**Latency**: 2.3s (same as English)

---

### Flow 4: Closed-Loop Nudge (IFA Reminder)

```
Day 1: System sends WhatsApp
    "नमस्ते! आज का IFA टैबलेट लिया? हाँ के लिए 'ली' भेजें।"
    ↓
State: pending_ifa → ifa_sent
    ↓
Day 1 (evening): Patient replies "ली"
    ↓
State: ifa_sent → ifa_confirmed
    ↓
Day 2: Next cycle begins
    ↓
[If no reply after 3 days]
    ↓
State: ifa_sent → overdue_1
    ↓
System: Send reminder + escalate to ANM after 3 missed
```

---

## Decision Boundary System

### Decision Boundary Card (`boundary_card.json`)

**Purpose**: Machine-readable specification of what the system answers, refuses, and escalates

**Schema**:

```json
{
  "version": "0.1",
  "answerable": [
    {
      "query": "IFA tablet dose for pregnant women",
      "category": "protocol",
      "source": "MoHFW ANC guidelines",
      "expected_answer": "180 tablets (1 daily for 180 days)"
    }
  ],
  "refusals": [
    {
      "query": "Is 140/90 high BP?",
      "category": "diagnostic",
      "reason": "BP interpretation requires Medical Officer",
      "urgency": "high",
      "escalation_target": "Medical Officer"
    }
  ]
}
```

**Current Coverage**:
- 16 answerable queries (IFA, ANC, immunization, nutrition)
- 16 refusal triggers (BP, insulin, bleeding, prescriptions, diagnoses)

**Validation**:
- `scripts/g1_checks.sh`: Automated test suite
- 5 core refusals tested (BP, insulin, bleeding, metformin, TB)
- 100% refusal accuracy required for Gate 1

---

## Deployment Architecture

### Edge Hardware Requirements

**Minimum Specs**:
- CPU: 4 cores (ARM64 or x86_64)
- RAM: 8GB
- Storage: 32GB (16GB for model + index, 16GB for logs/data)
- Power: <50W (solar-compatible)

**Recommended Hardware**:
- Raspberry Pi 5 (8GB): ₹8,000
- Intel N100 Mini-PC (8GB): ₹15,000
- Orange Pi 5 Plus (16GB): ₹12,000

### Software Stack

```
┌─────────────────────────────────────┐
│  Application Layer                  │
│  • Python 3.10+                     │
│  • Sub-Centre Mind (src/)           │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│  Inference Layer                    │
│  • Ollama 0.22.1+                   │
│  • Gemma 4 E4B (9.6 GB)             │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│  Data Layer                         │
│  • FAISS (vector store)             │
│  • SQLite (logs, state)             │
│  • JSON (config, boundary card)     │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│  OS Layer                           │
│  • Ubuntu 22.04 / Raspberry Pi OS   │
│  • systemd (service management)     │
└─────────────────────────────────────┘
```

### Network Architecture

```
┌──────────────────────────────────────────────┐
│  Sub-Centre (Offline-First)                 │
│                                              │
│  ┌────────────┐      ┌─────────────┐       │
│  │  Mini-PC   │──────│  Router     │       │
│  │  (Gemma 4) │      │  (Optional) │       │
│  └────────────┘      └──────┬──────┘       │
│         │                    │               │
│         │                    │               │
│  ┌──────▼──────┐      ┌─────▼──────┐       │
│  │  ANM Phone  │      │ 4G Modem   │       │
│  │  (WhatsApp) │      │ (Nudges)   │       │
│  └─────────────┘      └────────────┘       │
│                                              │
└──────────────────────────────────────────────┘
         │ (Optional: HMIS sync)
         ▼
┌──────────────────────────────────────────────┐
│  District Health Office                      │
│  • HMIS Portal                               │
│  • Medical Officer Dashboard                 │
└──────────────────────────────────────────────┘
```

**Connectivity**:
- **Primary Mode**: Offline (all inference local)
- **Optional**: 4G for WhatsApp nudges (low bandwidth)
- **Sync**: Daily HMIS upload when connectivity available

---

## Technology Stack

### Core Dependencies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| LLM Runtime | Ollama | 0.22.1+ | Local Gemma 4 inference |
| Model | Gemma 4 E4B | 9.6 GB | Question answering + tool calling |
| Vector Store | FAISS | 1.7.4 | Semantic search (CPU-only) |
| Embeddings | sentence-transformers | 2.2.2 | Multilingual embeddings |
| Embedding Model | paraphrase-multilingual-MiniLM-L12-v2 | 384-dim | Hindi/Marathi/English |
| PDF Processing | PyPDF2 | 3.0.1 | Extract text from MoHFW PDFs |
| Testing | pytest | 7.4.0 | Test suite |
| Language | Python | 3.10+ | Application code |

### Full Stack

```
Application:     Python 3.10+
Framework:       None (lightweight scripts)
LLM:             Gemma 4 E4B via Ollama
Vector DB:       FAISS (IndexFlatIP)
Embeddings:      sentence-transformers
State:           SQLite (logs, nudge state)
Config:          JSON (boundary card, meta)
Interface:       WhatsApp API (future) / CLI (current)
Deployment:      systemd service
Monitoring:      Local logs (queries.jsonl, nudges.jsonl)
```

---

## Security & Privacy

### Data Sovereignty

**Principle**: PHI (Protected Health Information) never leaves the sub-centre

**Implementation**:
- All inference local (no cloud API calls)
- All data stored locally (no remote database)
- Optional sync to district HMIS (encrypted, government network)

### Audit Trail

**Every query logged**:
```json
{
  "timestamp": "2026-05-02T18:30:45Z",
  "query": "IFA dose for pregnant women?",
  "intent": "iron_ifa",
  "retrieved_chunks": 5,
  "top_score": 0.92,
  "tool_call": null,
  "response_length": 156,
  "latency_ms": 2100
}
```

**Every refusal logged**:
```json
{
  "timestamp": "2026-05-02T18:35:12Z",
  "query": "Is 140/90 high BP?",
  "tool_call": "refuse_and_escalate",
  "reason": "BP interpretation requires Medical Officer",
  "urgency": "high",
  "escalation_target": "Medical Officer"
}
```

### Access Control

**Current** (Phase 1):
- Single-user system (ANM at sub-centre)
- No authentication (physical access control)

**Future** (Production):
- ANM login (PIN-based)
- Role-based access (ANM vs MO vs Admin)
- Session timeout (auto-lock after 15 min)

### Model Safety

**Refusal Contract**:
- Explicit boundaries (no diagnosis, no prescribing)
- Function calling enforces refusal (not just prompt)
- Every answer cites source (verifiable by ANM)

**Failure Modes**:
- Low retrieval score (<0.7) → refuse with "insufficient source confidence"
- Empty retrieval → refuse with "no relevant source found"
- Ambiguous query → ask for clarification

---

## Appendix: Diagram Prompts for Nano Banan

### Prompt 1: System Architecture Diagram

```
Create a clean, modern system architecture diagram for "Sub-Centre Mind" with these components:

Top layer: "ANM (User)" with WhatsApp icon
↓
Second layer: "Query Router" (decision diamond shape) with "boundary_card.json" label
↓ splits into two paths:
Left path: "RAG Pipeline" box containing:
  - Intent Detection
  - FAISS Retrieval
  - Reranking
Right path: "Refusal Handler" box containing:
  - Tool Calling
  - MO Notification
↓ both paths merge to:
"Gemma 4 E4B (Ollama)" box with "think: false" label
↓
Bottom layer: "Nudge Engine" box with WhatsApp icon

Use colors:
- Blue for data flow
- Red for refusal path
- Green for answer path
- Orange for nudge loop

Style: Clean, professional, healthcare-appropriate colors
```

### Prompt 2: RAG Pipeline Flow

```
Create a vertical flowchart showing the RAG pipeline with these steps:

1. "Query (Hindi/Marathi/English)" - rounded rectangle
2. "Intent Detection" - hexagon with "IFA vs Calcium" label
3. "Multilingual Embedding" - rectangle with model name
4. "FAISS Retrieval" - cylinder shape with "top-48 candidates"
5. "Intent Reranking" - diamond with "1.35× boost" label
6. "Top-5 Chunks" - rectangle with "score >0.7"
7. "Gemma 4 Generation" - rounded rectangle
8. "Answer + Citations" - rounded rectangle with document icon

Add timing annotations:
- Retrieval: 0.3s
- Generation: 1.8s
- Total: 2.1s

Style: Technical flowchart, use gradient colors (blue to green)
```

### Prompt 3: Decision Boundary Visualization

```
Create a 2x2 matrix diagram showing the Decision Boundary Card:

X-axis: "Complexity" (Low to High)
Y-axis: "Risk" (Low to High)

Quadrants:
1. Bottom-left (Low Risk, Low Complexity): "Protocol Questions"
   - Examples: IFA dose, ANC schedule, immunization
   - Color: Green
   - Action: "Answer with RAG"

2. Top-left (High Risk, Low Complexity): "Danger Signs"
   - Examples: Bleeding, seizures, severe pain
   - Color: Red
   - Action: "Refuse + Escalate (Critical)"

3. Bottom-right (Low Risk, High Complexity): "Edge Cases"
   - Examples: Rare protocols, unclear guidelines
   - Color: Yellow
   - Action: "Refuse + Escalate (Medium)"

4. Top-right (High Risk, High Complexity): "Diagnostic/Prescriptive"
   - Examples: BP interpretation, insulin dosing, lab results
   - Color: Dark Red
   - Action: "Refuse + Escalate (High)"

Add legend showing urgency levels: Critical, High, Medium, Low

Style: Clean matrix with clear color coding
```

### Prompt 4: Deployment Architecture

```
Create a network diagram showing edge deployment:

Center: "Sub-Centre" (building icon) containing:
  - Mini-PC (server icon) labeled "Gemma 4 E4B"
  - Router (optional, dashed line)
  - ANM Phone (mobile icon) with WhatsApp
  - 4G Modem (antenna icon, dashed line)

Connections:
- Solid line: Mini-PC ↔ ANM Phone (local)
- Dashed line: 4G Modem ↔ Cloud (optional)

Bottom: "District Health Office" (building icon) containing:
  - HMIS Portal
  - Medical Officer Dashboard

Show data flow:
- Thick arrow: Local inference (always)
- Thin dashed arrow: HMIS sync (optional, daily)
- Dotted arrow: WhatsApp nudges (optional, low bandwidth)

Add labels:
- "Offline-First"
- "PHI Never Leaves Device"
- "Optional Sync"

Style: Infrastructure diagram, use icons, muted colors
```

### Prompt 5: Closed-Loop Nudge Flow

```
Create a circular state machine diagram for the nudge engine:

States (circles):
1. "pending_ifa" (gray)
2. "ifa_sent" (blue)
3. "ifa_confirmed" (green)
4. "overdue_1" (yellow)
5. "overdue_2" (orange)
6. "overdue_3" (red)
7. "escalate_to_anm" (dark red)

Transitions (arrows):
- pending_ifa → ifa_sent: "Send WhatsApp"
- ifa_sent → ifa_confirmed: "Patient replies 'ली'"
- ifa_confirmed → pending_ifa: "Next cycle (24h)"
- ifa_sent → overdue_1: "No reply (3 days)"
- overdue_1 → overdue_2: "No reply (3 days)"
- overdue_2 → overdue_3: "No reply (3 days)"
- overdue_3 → escalate_to_anm: "3 missed"

Add WhatsApp icon on "ifa_sent" state
Add checkmark icon on "ifa_confirmed" state
Add alert icon on "escalate_to_anm" state

Style: State machine diagram, color-coded by urgency
```

---

**End of Architecture Documentation**

*For implementation details, see:*
- `docs/CORPUS.md` - Source PDF documentation
- `boundary_card.json` - Decision boundary specification
- `scripts/g1_checks.sh` - Validation test suite
- `src/rag/` - RAG pipeline implementation
