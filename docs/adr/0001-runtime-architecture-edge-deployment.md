# ADR 0001: Runtime Architecture for Edge Deployment

**Date:** 2026-05-03
**Status:** Proposed
**Deciders:** Prasad Tilloo
**Hackathon:** Gemma 4 Good — Health & Sciences Track

## Context

Sub-Centre Mind is clinical decision support for India's ~250,000 sub-centres, each managed by a single ANM (Auxiliary Nurse Midwife) responsible for 3,000–5,000 patients. The system must run **entirely on-device** — no PHI may leave the sub-centre.

The Gate 1 prototype (verified May 3, 2026) runs on a $200 mini-PC via Ollama. This works for judging and desktop demos, but the $200 CAPEX per sub-centre + sysadmin maintenance creates a barrier to adoption that undermines the product's mission. Government procurement in rural India is slow, underfunded, and prone to leakage; asking for 250,000 dedicated devices is a non-starter.

The Gemma 4 Good Hackathon awards separate **Special Technology Track** prizes ($10K each) for Ollama, LiteRT, Cactus, llama.cpp, and Unsloth — meaning architecture choices directly affect prize eligibility.

## Problem

**Which runtime architecture minimises barrier to entry for rural sub-centres while preserving the safety guarantees (confidence gate, refusal contract, audit trail) proven in Gate 1?**

### Requirements

| # | Requirement | Priority |
|---|-------------|----------|
| R1 | All inference local — PHI never leaves device | Must |
| R2 | Refusal contract (`boundary_card.json`) enforced at every query | Must |
| R3 | Confidence gate (≥0.7 similarity) before any LLM generation | Must |
| R4 | Multilingual RAG (Hindi, Marathi, English) with retrieval quality ≥0.7 cosine | Must |
| R5 | Voice input (Hindi, with phonetic normalisation for clinical loan-words) | Must |
| R6 | Vision (bounded: OCR, medicine packet, register row) | Must |
| R7 | Warm query latency ≤12s | Must |
| R8 | Closed-loop nudge state machine with local persistence | Must |
| R9 | Audit JSONL trail for supervisor reporting | Must |
| R10 | Per-unit hardware cost ≤$100 (ideally $0 incremental) | Should |
| R11 | Deployment by non-technical staff (no SSH, no CLI) | Should |
| R12 | No separate server/device beyond what the ANM already owns | Should |
| R13 | Prize eligibility for multiple Special Technology Track awards | Nice |

## Options Considered

### Option 1: Ollama on mini-PC (current — Gate 1 verified)

The ANM uses a $200 Intel N100 mini-PC (8–16 GB RAM) running Ubuntu + Ollama. Streamlit UI served locally in a browser. All Python dependencies installed via pip.

**Stack:**
- LLM: Gemma 4 E4B via Ollama (`/api/generate`, `/api/chat`)
- Embeddings: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (PyTorch)
- Vector search: FAISS (C++ via Python bindings)
- BM25: `rank-bm25` (pure Python)
- ASR: `faster-whisper` (CTranslate2, CPU)
- Vision: Ollama `/api/chat` with `images` field
- UI: Streamlit (browser)
- Nudges/Audit: pure Python, local JSON/JSONL

### Option A: Raspberry Pi 5 + phone (split architecture)

Retrieval pipeline (FAISS + sentence-transformers + BM25) runs on a Raspberry Pi 5 (8 GB, ~$80) at the sub-centre. LLM inference runs on the ANM's phone via LiteRT. Phone talks to Pi over local WiFi.

**Stack:**
- Pi: same Python retrieval stack as Option 1
- Phone: Gemma 4 E4B via LiteRT (Google AI Edge runtime)
- Communication: local WiFi REST API (Pi → phone)
- UI: simple Android app or mobile web page
- ASR: LiteRT or faster-whisper on Pi

### Option B: Cactus on phone only (zero-hardware)

Everything runs on the ANM's Android phone (6–8 GB RAM) using the Cactus framework. No separate device. Cactus provides LLM inference, embeddings, vector search (HNSW), vision, audio, and function calling in a single SDK.

**Stack:**
- LLM: Gemma 4 E4B via Cactus (INT4, ARM-optimised, ~40 tok/s on Apple Silicon)
- Embeddings: Cactus `model.embed()` — native, no separate model
- Vector search: `CactusIndex` (HNSW, on-device)
- ASR: Gemma 4's native 300M-parameter audio encoder (0.3s for 30s clip)
- Vision: Gemma 4's native vision encoder (built-in, not bolt-on)
- Function calling: Native Cactus tool-use API
- UI: Kotlin (Android) or React Native via Cactus SDK
- Nudges/Audit: port state machine + JSONL to Kotlin/JS (~200 lines)

## Decision Matrix

Scored 1 (worst) to 5 (best) per criterion. Weights reflect rural deployment reality.

| Criterion | Weight | Option 1 (Ollama mini-PC) | Option A (Pi + phone) | Option B (Cactus phone) |
|-----------|--------|--------------------------|----------------------|------------------------|
| **R1: PHI on-device** | Critical | 5 — all local | 5 — all local | 5 — all local |
| **R2–R4: Safety moat** (gate, refusal, RAG quality) | Critical | 5 — proven, 60 tests | 4 — same retrieval, different LLM runtime | 3 — Cactus Auto-RAG simpler than FAISS+BM25+RRF; custom reranking needs porting |
| **R5: Voice input** | Must | 4 — faster-whisper, good | 3 — split across devices | 5 — native audio encoder, 0.3s, no separate model |
| **R6: Vision** | Must | 4 — Ollama multimodal | 3 — split across devices | 5 — native vision encoder, single forward pass |
| **R7: Latency ≤12s** | Must | 5 — 3.3s proven | 4 — network hop adds ~200ms | 5 — ARM-optimised, ~40 tok/s |
| **R10: Per-unit cost** | High | 2 — $200 CAPEX | 3 — $80 Pi + existing phone | 5 — $0 if phone exists; $120 budget tablet |
| **R11: Non-technical deploy** | High | 1 — requires Linux + SSH + pip | 2 — Pi needs setup; APK is easy | 5 — APK install only |
| **R12: No extra device** | High | 1 — dedicated mini-PC | 2 — dedicated Pi | 5 — ANM's own phone |
| **R13: Prize eligibility** | Nice | 3 — Ollama ($10K) | 4 — Ollama + LiteRT ($20K) | 4 — Cactus ($10K) + Ollama ($10K for existing work) |
| **Maintenance burden** | High | 2 — OS updates, Ollama updates, power/network | 3 — Pi lighter than PC but still a device | 5 — app auto-updates via Play Store |
| **Development effort to deadline** | Medium | 5 — done | 2 — split-device networking is complex | 3 — new SDK, but Cactus handles most infra |
| **Retrieval sophistication** | Medium | 5 — FAISS+BM25+RRF+intent rerank | 5 — same stack on Pi | 3 — Cactus HNSW is simpler; custom reranking needs extra work |
| **Corruption/leakage risk** | High | 2 — $200 device is stealable/sellable | 3 — $80 Pi is less attractive | 5 — no new hardware to procure |
| | | | | |
| **Weighted total** | | **45** | **43** | **58** |

## Decision

**Recommended: Option B (Cactus phone-only) as the target production architecture, with Option 1 (Ollama) preserved as the verified demo/fallback path.**

### Migration strategy

```
Phase 1 (current, Gate 1) — Option 1 LOCKED
    All 60 tests pass. g1_checks.sh verified.
    Ollama + mini-PC. Streamlit demo for judges.
    This path is NOT modified.

Phase 2 (May 4–12) — Build LLM abstraction layer
    Extract LLMBackend Protocol (generate, chat, vision).
    Implement OllamaBackend (refactor existing ~50 lines).
    Implement CactusBackend (stub → real).
    Feature flag: SCM_BACKEND=ollama | cactus (default: ollama).
    Existing tests run against OllamaBackend unchanged.

Phase 3 (May 8–15) — Cactus proof-of-concept
    Cactus SDK integration (Python first via pip install cactus-ai).
    Port embeddings: model.embed() replaces sentence-transformers.
    Port vector search: CactusIndex replaces FAISS.
    Port Auto-RAG or keep custom retrieval with CactusIndex low-level API.
    Validate retrieval quality: Hindi ≥0.7, Marathi ≥0.7.
    Validate refusal contract: 5/5 refusals still fire.
    Validate latency: ≤12s.

Phase 4 (May 12–16) — ANM-facing UI
    Simple mobile interface (Kotlin via Cactus Android SDK or React Native).
    Voice-first: big mic button, answer in Hindi, citations hidden.
    Nudge view: patient checklist, not state machine diagram.
    Monthly report download.

Phase 5 (post-hackathon) — Production hardening
    Fine-tune Gemma 4 E4B via Unsloth on protocol Q&A + refusals.
    Field testing with real ANMs.
    Play Store distribution.
```

### Fallback guarantee

At any point during Phases 2–4, if Cactus integration hits a blocker (retrieval quality drops, function calling doesn't work as expected, mobile performance is insufficient), the team reverts to Option 1 by setting `SCM_BACKEND=ollama`. The Gate 1 demo path is never modified. All submission artifacts (boundary_card.json, g1_checks.sh, test suite, Streamlit demo) remain functional.

## Consequences

### What changes

- New `src/llm/` module with `LLMBackend` Protocol and two implementations
- `SCM_BACKEND` environment variable as the single switch
- `generate.py`, `query_router.py`, `vision/client.py`, `audit/report.py` call the backend via the Protocol instead of raw `requests.post`
- New Cactus-specific integration tests (marked, skippable without Cactus installed)

### What stays the same

- `boundary_card.json` — unchanged
- `src/rag/gate.py` — pure math, no runtime coupling
- `src/rag/lang.py` — pure string ops
- `src/rag/intent.py` — pure regex/keyword
- `src/nudges/` — pure state machine + JSON store
- `src/audit/schema.py` — pure JSONL I/O
- All 60 existing tests — run against OllamaBackend by default
- `scripts/g1_checks.sh` — Gate 1 verification script unchanged
- `docs/`, `README.md`, Streamlit demo — all preserved

### Risks

| Risk | Mitigation |
|------|-----------|
| Cactus embedding quality differs from MiniLM-L12-v2 | Validate Hindi/Marathi similarity ≥0.7 before switching; fall back to Option 1 |
| Cactus function calling doesn't reliably fire `refuse_and_escalate` | Keep Ollama as verified path; test boundary_card entries on Cactus |
| Cactus Auto-RAG lacks BM25/RRF sophistication → iron vs calcium confusion returns | Use CactusIndex low-level API + port intent reranking logic |
| ANM phones have <6 GB RAM | Offer E2B fallback (2.3B params, lower RAM); accept slight quality trade |
| Development effort exceeds timeline | Feature flag ensures instant revert to Option 1; partial Cactus work still demonstrates architecture thinking |
| Cactus SDK stability (startup framework, v1.x) | Pin SDK version; isolate behind Protocol so swap cost is minimal |

### Cost at scale

| Scale | Option 1 | Option B |
|-------|----------|----------|
| 1 sub-centre | $200 (mini-PC) | $0 (ANM's phone) |
| 1,000 sub-centres | $200,000 | $0 |
| 250,000 sub-centres | $50,000,000 | $0 |
| Annual maintenance (est.) | $25/device/year × 250K = $6.25M | App update push = ~$0 |

The cost difference is not marginal. It is the difference between a fundable pilot and a logistically impossible national rollout.

### Prize eligibility

| Prize track | Option 1 only | Option 1 + Option B |
|-------------|--------------|---------------------|
| Health & Sciences (main) | Eligible | Eligible (stronger: zero-cost story) |
| Ollama ($10K) | Eligible | Eligible (Gate 1 demo uses Ollama) |
| Cactus ($10K) | Not eligible | Eligible |
| Unsloth ($10K) | With fine-tuning | With fine-tuning |
| **Max special tech prizes** | **$10K** | **$30K** |

## References

- [Cactus documentation — RAG & Embedding](https://cactuscompute.com/docs/v1.7/rag)
- [Cactus — Gemma 4 support](https://docs.cactuscompute.com/v1.14/blog/gemma4/)
- [Gemma 4 E4B system requirements](https://www.oflight.co.jp/en/columns/gemma4-hardware-requirements-local-ai-spec-2026)
- [Sentence-Embeddings-Android (ONNX MiniLM on Android)](https://github.com/shubham0204/Sentence-Embeddings-Android)
- [Gemma 4 for Edge Deployment](https://www.mindstudio.ai/blog/gemma-4-edge-deployment-e2b-e4b-models/)
- [LiteRT-LM Gemma 4 E4B](https://huggingface.co/litert-community/gemma-4-E4B-it-litert-lm)
- [Unsloth Gemma 4 fine-tuning guide](https://unsloth.ai/docs/models/gemma-4/train)

## Appendix A: Portability Audit

Audit of all 15 source modules in `src/` — coupling to Ollama runtime.

### Zero coupling (13 modules — the moat)

| Module | Lines | Dependency |
|--------|-------|-----------|
| `rag/query.py` | 283 | sentence-transformers, faiss, numpy |
| `rag/gate.py` | 29 | None (pure math) |
| `rag/lang.py` | 162 | None (pure regex) |
| `rag/intent.py` | 242 | None (pure regex) |
| `rag/ingest.py` | 151 | sentence-transformers, faiss, PyPDF2 |
| `rag/text_tokenize.py` | ~30 | None |
| `nudges/state.py` | 123 | None (pure dataclass) |
| `nudges/store.py` | ~60 | None (JSON file I/O) |
| `nudges/dispatcher.py` | 63 | None (Protocol class) |
| `audit/schema.py` | 63 | None (JSONL I/O) |
| `audit/report.py` | 65 | None (aggregate + template_summary) |
| `voice/asr.py` | 133 | faster-whisper only |
| `boundary_card.json` | 299 | Data file |

### Ollama coupling (4 call sites, ~50 lines total)

| File | Function | Ollama endpoint | Lines |
|------|----------|----------------|-------|
| `rag/generate.py` | `generate_answer()` | `POST /api/generate` | 110–124 |
| `query_router.py` | `orchestrate_query()` | `POST /api/chat` (tools) | 150–166 |
| `vision/client.py` | `_post_chat()` | `POST /api/chat` (images) | 32–49 |
| `audit/report.py` | `llm_narrative()` | `POST /api/generate` | 77–90 |

These 4 functions are the **only** code that changes when swapping runtimes.

## Appendix B: Corpus Inventory

| # | Source PDF | Size | Chunks |
|---|-----------|------|--------|
| 1 | AMB-Operational-Guidelines.pdf | 17 MB | — |
| 2 | HBNC-Operational-Guidelines.pdf | 4.1 MB | — |
| 3 | MCP-Guide-Book-2018.pdf | 5.8 MB | — |
| 4 | NHM-National-Immunization-Schedule.pdf | 160 KB | — |
| 5 | NHM-SBA-Guidelines-ANC-Skilled-Attendance-ANM-2010.pdf | 14 MB | — |
| 6 | NHSRC-Skills-Lab-RMNCH-A-Training-Manual-2013.pdf | 8.1 MB | — |
| 7 | PMSMA-Extended-HRP-Guidance.pdf | 1.2 MB | — |
| 8 | RCH-Portal-Data-Entry-Manual-2018.pdf | 11 MB | — |
| 9 | WHO-Calcium-Supplementation.pdf | 488 KB | — |
| 10 | WHO-IFA-pregnant-women-2012.pdf | 220 KB | — |
| 11 | WHO-India-CMYP-2013-2017.pdf | 2.0 MB | — |
| | **Total** | **~64 MB** | **1,790** |

Embedding model: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384-dim)
FAISS index: 2.6 MB · BM25 pickle: 1.5 MB · chunks.json: 1.5 MB
Chunking: 900 chars max, 120 chars overlap

At 1,790 chunks × 384 dimensions, brute-force cosine similarity on a phone CPU takes <10ms. A dedicated vector index (FAISS, HNSW) is a convenience, not a necessity.
