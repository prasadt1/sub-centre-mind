# Claude Code Bootstrap Prompt — Sub-Centre Mind

**Use this prompt to hand off to Claude Code (or any AI coding assistant) for rapid implementation.**

---

## Context

You are helping build **Sub-Centre Mind**, a local-first clinical decision support tool for India's ANMs (Auxiliary Nurse Midwives), powered by Gemma 4 E4B via Ollama. This is for the **Gemma 4 Good Hackathon** (Health & Sciences track, $10K prize).

**Deadline**: Gate 1 on May 5, 18:00 CET (must pass 4 criteria), final submission May 18.

**Repo**: `~/projects/sub-centre-mind/`

**Model**: Gemma 4 E4B (9.6 GB) already downloaded via `ollama pull gemma4:latest`

---

## What You Need to Build

### 1. RAG Pipeline (`src/rag/`)

**Files to create**:
- `ingest.py` — Load MoHFW/WHO PDFs from `data/health-corpus/`, chunk, embed, store in FAISS
- `query.py` — Take user query (Hindi/Marathi/English), retrieve top-k chunks (k=5), return with similarity scores
- `generate.py` — Combine chunks + query into Gemma 4 prompt, call Ollama API, return response

**Requirements**:
- Use `faiss-cpu` for vector store (no GPU)
- Use `langchain` for PDF loading and text splitting
- Chunk size: 512 tokens, overlap: 50 tokens
- Embedding model: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (supports Hindi/Marathi)
- Ollama API endpoint: `http://localhost:11434/api/generate`
- Target latency: <12s per query (retrieval + generation)

**Test queries**:
- English: "IFA tablet dose for pregnant women per MoHFW?"
- Hindi: "गर्भवती महिलाओं के लिए IFA टैबलेट की खुराक क्या है?"
- Marathi: "गर्भवती महिलांसाठी IFA डोस काय आहे?"

---

### 2. Refusal + Function Calling (`src/refusal/`)

**Files to create**:
- `tools.py` — Define two function schemas for Gemma 4:
  - `refuse_and_escalate(reason: str, escalation_target: str, urgency: str)`
  - `answer_protocol_question(answer: str, source: str, confidence: float)`
- `classifier.py` — Load `boundary_card.json`, classify query as answer/refuse, call appropriate function
- `escalate.py` — Format escalation message (query + reason + urgency), log to console (mock Medical Officer notification)

**Requirements**:
- Use Ollama's function calling API (pass tools in request JSON)
- Parse response to extract tool call (JSON with `name` and `arguments`)
- If `refuse_and_escalate` called → log escalation, return refusal message to ANM
- If `answer_protocol_question` called → return answer with source citation

**Test refusals** (must trigger `refuse_and_escalate`):
1. "Is 140/90 high BP?"
2. "How much insulin for gestational diabetes?"
3. "Is heavy bleeding normal?"
4. "Should I give metformin?"
5. "Does cough mean TB?"

---

### 3. Decision Boundary Card (`boundary_card.json`)

**Schema**:
```json
{
  "version": "0.1",
  "answerable": [
    {
      "query": "IFA tablet dose for pregnant women",
      "category": "protocol",
      "source": "MoHFW ANC guidelines"
    }
  ],
  "refusals": [
    {
      "query": "Is 140/90 high BP?",
      "category": "diagnostic",
      "reason": "BP interpretation requires Medical Officer",
      "urgency": "medium"
    }
  ]
}
```

**Requirements**:
- ≥15 answerable queries (IFA, ANC schedule, immunization, nutrition, danger signs)
- ≥15 refusal triggers (BP, insulin, bleeding, prescriptions, diagnoses, lab interpretation)
- Each entry must have: query, category, reason/source, urgency (for refusals)

---

### 4. Test Suite (`tests/`)

**Files to create**:
- `test_function_calling.py` — Verify Ollama returns valid JSON with tool calls
- `test_refusal.py` — Run 5 refusal queries, assert `refuse_and_escalate` called
- `test_rag_multilingual.py` — Run Hindi + Marathi queries, assert similarity >0.7
- `test_latency.py` — Measure end-to-end latency, assert <12s

**Use pytest**, run with: `pytest tests/ -v`

---

### 5. Requirements (`requirements.txt`)

```
faiss-cpu==1.7.4
langchain==0.1.0
sentence-transformers==2.2.2
ollama==0.1.0
pytest==7.4.0
PyPDF2==3.0.1
```

---

## Gate 1 Criteria (May 5, 18:00 CET)

Must pass ALL 4:

1. ✅ Function calling returns valid JSON with `refuse_and_escalate` tool call
2. ✅ 5/5 refusals trigger correctly (BP, insulin, bleeding, metformin, TB diagnosis)
3. ✅ Multilingual RAG: Hindi + Marathi queries return relevant chunks (>0.7 similarity)
4. ✅ Latency ≤12s per query

---

## Hard Constraints

- **Gemma 4 E4B via Ollama ONLY** — no other LLM APIs
- **No vision in v1** — text-only
- **PHI never leaves device** — all processing local
- **No coding past 22:00 CET** (Prasad's rule)

---

## Smoke Test Command

```bash
ollama run gemma4:latest "IFA tablet dose for pregnant women per MoHFW?"
```

Expected: Response about 180 tablets (1 daily for 180 days post-conception).

---

## File Structure

```
sub-centre-mind/
├── src/
│   ├── rag/
│   │   ├── ingest.py
│   │   ├── query.py
│   │   └── generate.py
│   └── refusal/
│       ├── tools.py
│       ├── classifier.py
│       └── escalate.py
├── data/
│   └── health-corpus/       # Place MoHFW PDFs here
├── tests/
│   ├── test_function_calling.py
│   ├── test_refusal.py
│   ├── test_rag_multilingual.py
│   └── test_latency.py
├── boundary_card.json
├── requirements.txt
└── README.md
```

---

## Next Steps

1. **Implement RAG pipeline** — start with `ingest.py`, test with 1-2 PDFs
2. **Implement refusal logic** — write `boundary_card.json` first, then `classifier.py`
3. **Write tests** — run after each module is complete
4. **Smoke test Gemma 4** — verify Ollama connectivity and basic query
5. **Run Gate 1 validation** — all 4 criteria must pass by May 5

---

## Questions to Ask Prasad

- Where are the MoHFW PDFs? (need URLs or local paths)
- Medical Officer contact format for escalation? (phone, WhatsApp, email)
- Preferred language for ANM interface? (Hindi, Marathi, English, or all three)
- WhatsApp API credentials for nudge engine? (or mock for v1?)

---

## Kill Switch

If Gate 1 fails on May 5 → **withdraw from hackathon, no heroics**. This is a hard constraint.

---

**Ready to code? Start with `src/rag/ingest.py` and `boundary_card.json`.**
