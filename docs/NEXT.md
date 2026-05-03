# Sub-Centre Mind — Build Roadmap

25-task checklist across 4 phases. Items marked ✅ are complete as of the Gate 1 submission (May 5, 2026).

---

## Phase 1 — Gate 1 Core (due May 5, 2026)

| # | Task | Status |
|---|------|--------|
| 1 | RAG pipeline: FAISS + BM25 hybrid retrieval over MoHFW/WHO corpus | ✅ |
| 2 | Confidence gate (≥0.7 cosine similarity threshold) | ✅ |
| 3 | Gemma 4 E4B via Ollama local inference | ✅ |
| 4 | `refuse_and_escalate` tool call via `/api/chat` function calling | ✅ |
| 5 | `answer_protocol_question` tool call | ✅ |
| 6 | Decision Boundary Card v0.1 (16 answerable + 16 refusal entries) | ✅ |
| 7 | Multilingual: Hindi + Marathi queries >0.7 similarity | ✅ |
| 8 | ASR normalisation for Whisper phonetic mis-transcriptions | ✅ |
| 9 | Hindi/Urdu Whisper mis-classification detection + auto-retry | ✅ |
| 10 | Latency ≤12s warm (achieved: ~3.3s) | ✅ |
| 11 | Streamlit demo UI: Ask / Photo / Nudges / Report tabs | ✅ |
| 12 | Closed-loop nudge state machine (SCHEDULED → SENT → CONFIRMED / ESCALATED) | ✅ |
| 13 | Audit JSONL schema + aggregate report + template draft | ✅ |
| 14 | Vision: printed text OCR, medicine packet (always escalate), register row draft | ✅ |
| 15 | Local Whisper ASR (faster-whisper, Hindi/Marathi/English) | ✅ |

---

## Phase 2 — Post-Gate 1 Hardening

| # | Task | Status |
|---|------|--------|
| 16 | Expand corpus: ingest state-level ASHA/ANM operational guidelines | ⬜ |
| 17 | Boundary Card v0.2: ≥25 answerable + ≥25 refusals, reviewed by clinical advisor | ⬜ |
| 18 | Query intent classifier (IFA / ANC / immunisation / general) to guide retrieval focus | ⬜ |
| 19 | Marathi corpus chunks — ingest MoHFW Marathi-language PDFs to reduce reliance on expansion heuristic | ⬜ |
| 20 | Rate-limiting and de-duplication for nudge dispatcher | ⬜ |

---

## Phase 3 — WhatsApp Transport Layer

| # | Task | Status |
|---|------|--------|
| 21 | WhatsApp Business API integration for nudge send/receive | ⬜ |
| 22 | Reply parser: "ली" / "हाँ" / "no response" → `NudgeOutcome` | ⬜ |
| 23 | Escalation SMS to Medical Officer (Twilio / MSG91) | ⬜ |

---

## Phase 4 — HMIS Administrative Relief

| # | Task | Status |
|---|------|--------|
| 24 | HMIS / RCH-1 monthly report auto-draft: link numeric figures to audit event_ids | ⬜ |
| 25 | Supervisor review workflow: draft → reviewed → signed-off state for reports | ⬜ |

---

## Hard Constraints (all phases)

- Gemma 4 E4B via Ollama **only** — no cloud inference in the RAG/generation path
- PHI never leaves the device — all reasoning, retrieval, and generation is local
- Vision bounded to OCR / register fields — no diagnostic image interpretation
- Refusal contract (boundary_card.json) is the primary safety artifact; changes require explicit review
