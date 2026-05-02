# Build Checklist — Sub-Centre Mind

**Target**: Gate 1 (May 5, 18:00 CET) → Submission (May 18)  
**Available hours**: 20-50 total  
**Kill switch**: Gate 1 failure = withdraw, no heroics

---

## Phase 1: Foundation (May 2-3, ~8 hrs)

### Scaffold ✅
- [x] README.md
- [x] LICENSE (MIT)
- [x] NEXT.md (this file)
- [x] HANDOFF-CLI.md
- [x] boundary_card.json v0.1
- [x] requirements.txt

### Smoke Tests
- [ ] Ollama connectivity: `ollama list | grep gemma4`
- [ ] Basic query: "IFA tablet dose for pregnant women per MoHFW?"
- [ ] Function calling: verify JSON schema with `refuse_and_escalate` tool

### Decision Boundary Card v0.1
- [ ] 15+ answerable queries (IFA, ANC, immunization, nutrition)
- [ ] 15+ refusal triggers (BP, insulin, bleeding, prescriptions, diagnoses)
- [ ] JSON schema validation

---

## Phase 2: RAG Pipeline (May 3-4, ~12 hrs)

### Data Ingestion
- [ ] Download MoHFW PDFs (ANC guidelines, IFA protocols, immunization schedule)
- [ ] Download WHO safe motherhood guidelines
- [ ] Place in `data/health-corpus/`
- [ ] Write `src/rag/ingest.py` — PDF → chunks → FAISS index
- [ ] Verify index size and chunk count

### Retrieval
- [ ] Write `src/rag/query.py` — query → retrieve top-k chunks
- [ ] Implement multilingual query handling (Hindi, Marathi, English)
- [ ] Test similarity threshold (target: >0.7 for relevant chunks)
- [ ] Measure retrieval latency (target: <3s)

### RAG Integration
- [ ] Write `src/rag/generate.py` — chunks + query → Gemma 4 prompt
- [ ] Implement prompt template with MoHFW context injection
- [ ] Test end-to-end: query → retrieve → generate → response
- [ ] Verify citations/sources in response

---

## Phase 3: Refusal + Function Calling (May 4-5, ~10 hrs)

### Function Schema
- [ ] Define `refuse_and_escalate` tool schema (reason, escalation_target, urgency)
- [ ] Define `answer_protocol_question` tool schema (answer, source, confidence)
- [ ] Write `src/refusal/tools.py` — tool definitions for Ollama

### Refusal Logic
- [ ] Write `src/refusal/classifier.py` — query → answer/refuse decision
- [ ] Implement boundary card lookup
- [ ] Test 5 core refusals:
  - [ ] BP interpretation ("Is 140/90 high BP?")
  - [ ] Insulin dosing ("How much insulin for gestational diabetes?")
  - [ ] Bleeding assessment ("Is heavy bleeding normal?")
  - [ ] Metformin prescription ("Should I give metformin?")
  - [ ] TB diagnosis ("Does cough mean TB?")

### Escalation
- [ ] Write `src/refusal/escalate.py` — format escalation message
- [ ] Include query, reason, urgency level
- [ ] Mock Medical Officer notification (console log for v1)

---

## Phase 4: Gate 1 Validation (May 5, ~6 hrs)

### Test Suite
- [ ] Write `tests/test_function_calling.py` — verify JSON schema
- [ ] Write `tests/test_refusal.py` — 5/5 refusals pass
- [ ] Write `tests/test_rag_multilingual.py` — Hindi + Marathi queries
- [ ] Write `tests/test_latency.py` — <12s per query

### Gate 1 Checklist
- [ ] ✅ Function calling returns valid JSON with `refuse_and_escalate`
- [ ] ✅ 5/5 refusals trigger correctly
- [ ] ✅ Multilingual RAG: >0.7 similarity for Hindi/Marathi
- [ ] ✅ Latency ≤12s per query

### Documentation
- [ ] Record Gate 1 results in `docs/GATE1-RESULTS.md`
- [ ] Update README with test results
- [ ] Commit and tag: `git tag v0.1-gate1`

---

## Phase 5: Nudge Engine (May 6-10, ~10 hrs)

### State Machine (from AgriNexus AI)
- [ ] Port `src/nudges/state_machine.py` from AgriNexus
- [ ] Adapt states: `pending_ifa`, `pending_anc`, `confirmed`, `overdue`
- [ ] Write `src/nudges/scheduler.py` — IFA daily, ANC visit reminders

### WhatsApp Integration
- [ ] Mock WhatsApp client (console log for v1)
- [ ] Write `src/nudges/send.py` — format message, send
- [ ] Write `src/nudges/receive.py` — parse "ली" confirmation
- [ ] Test state transitions: send → confirm → next state

### Closed Loop
- [ ] Write `tests/test_nudge_loop.py` — E2E nudge cycle
- [ ] Verify state persistence (SQLite for v1)
- [ ] Test overdue escalation (3 missed IFA → alert ANM)

---

## Phase 6: Integration + Polish (May 11-15, ~8 hrs)

### End-to-End
- [ ] Write `src/main.py` — CLI entry point
- [ ] Integrate RAG + refusal + nudge
- [ ] Test full workflow: query → answer/refuse → nudge → confirm
- [ ] Measure total latency (target: <15s for answer + nudge)

### Error Handling
- [ ] Ollama connection failures → graceful fallback
- [ ] FAISS index missing → clear error message
- [ ] Malformed queries → prompt clarification

### Documentation
- [ ] Write `docs/ARCHITECTURE.md` — system design
- [ ] Write `docs/EVALUATION.md` — Gate 1 results, metrics
- [ ] Record demo video (3-5 min, Hindi/English)

---

## Phase 7: Submission (May 16-18, ~6 hrs)

### Hackathon Deliverables
- [ ] Update README with final results
- [ ] Ensure boundary_card.json is complete (v1.0)
- [ ] Clean up code: remove debug prints, add docstrings
- [ ] Run full test suite: `pytest tests/ -v`
- [ ] Push to GitHub: `git push origin main --tags`

### Kaggle Submission
- [ ] Prepare submission notebook (if required)
- [ ] Include demo video link
- [ ] Submit before May 18, 23:59 CET

### Post-Submission
- [ ] Write `docs/RETROSPECTIVE.md` — what worked, what didn't
- [ ] Plan v2 features (HMIS integration, voice input)

---

## Risk Register

| Risk | Mitigation | Owner |
|------|-----------|-------|
| Gate 1 failure | Kill switch: withdraw if any criterion fails | Prasad |
| Gemma 4 latency >12s | Reduce chunk size, optimize prompt | Prasad |
| Hindi/Marathi RAG <0.7 | Add transliteration, test more queries | Prasad |
| Function calling broken | Fallback to regex-based refusal | Prasad |
| Ollama crashes | Add retry logic, monitor memory | Prasad |

---

## Time Budget

| Phase | Estimated | Actual | Notes |
|-------|-----------|--------|-------|
| Phase 1: Foundation | 8 hrs | — | Scaffold + smoke tests |
| Phase 2: RAG Pipeline | 12 hrs | — | Ingest + retrieval + integration |
| Phase 3: Refusal + Function Calling | 10 hrs | — | Tools + classifier + escalation |
| Phase 4: Gate 1 Validation | 6 hrs | — | Test suite + documentation |
| Phase 5: Nudge Engine | 10 hrs | — | State machine + WhatsApp mock |
| Phase 6: Integration + Polish | 8 hrs | — | E2E + error handling + docs |
| Phase 7: Submission | 6 hrs | — | Final cleanup + Kaggle submit |
| **Total** | **60 hrs** | — | Buffer: 10-40 hrs depending on issues |

---

## Daily Standup Format

**Date**: YYYY-MM-DD  
**Hours logged**: X hrs  
**Completed**:
- Task 1
- Task 2

**In progress**:
- Task 3

**Blocked**:
- Issue 1 (mitigation: ...)

**Next**:
- Task 4
- Task 5

**Gate 1 status**: ON TRACK / AT RISK / BLOCKED
