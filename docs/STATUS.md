# Sub-Centre Mind — Status Report

**Date**: May 2, 2026  
**Hours logged**: 1.5 hrs  
**Gate 1 status**: ⚠️ BLOCKED

---

## Completed ✅

### Scaffold Files
- [x] README.md — project overview, architecture, engineering lineage
- [x] LICENSE — MIT
- [x] docs/NEXT.md — 25-task build checklist across 4 phases
- [x] docs/HANDOFF-CLI.md — Claude Code bootstrap prompt
- [x] boundary_card.json v0.1 — 16 answerable + 16 refusal entries
- [x] requirements.txt — dependencies for RAG pipeline

### Verification
- [x] Ollama service running (PID 43219)
- [x] Gemma 4 model listed in `ollama list` (9.6 GB)

---

## Blocked 🚫

### Critical Blocker: Ollama Version Mismatch

**Issue**: Gemma 4 model requires newer Ollama version than currently installed

**Details**:
- Current Ollama version: `0.18.3`
- Error when running `ollama run gemma4:latest`: `500 Internal Server Error: unable to load model`
- Error when pulling: `412: The model you are attempting to pull requires a newer version of Ollama`

**Impact**: Cannot run smoke test or any Gemma 4 queries → Gate 1 at risk

**Mitigation**:
1. **Immediate**: Update Ollama to latest version from https://ollama.com/download
2. **Verify**: Run `ollama --version` to confirm update
3. **Re-pull**: `ollama pull gemma4:latest` to get compatible model
4. **Test**: `ollama run gemma4:latest "IFA tablet dose for pregnant women per MoHFW?"`

**Owner**: Prasad  
**Deadline**: May 3, 09:00 CET (before RAG pipeline work)

---

## Next Steps

### After Ollama Update
1. Run smoke test: `ollama run gemma4:latest "IFA tablet dose..."`
2. Test function calling with `refuse_and_escalate` tool schema
3. Begin RAG pipeline: download MoHFW PDFs to `data/health-corpus/`
4. Write `src/rag/ingest.py` — PDF → chunks → FAISS index

### Immediate Actions (Tonight)
- [ ] Update Ollama to latest version
- [ ] Verify Gemma 4 model loads correctly
- [ ] Run smoke test and document response
- [ ] Update STATUS.md with results

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Ollama update breaks existing models | Low | Medium | Test with qwen3:8b first |
| Gemma 4 still incompatible after update | Low | Critical | **Kill switch**: withdraw from hackathon |
| Smoke test latency >12s | Medium | High | Optimize prompt, reduce chunk size |
| Function calling not supported | Low | Critical | Fallback to regex-based refusal |

---

## Time Budget

| Phase | Estimated | Actual | Remaining |
|-------|-----------|--------|-----------|
| Phase 1: Foundation | 8 hrs | 1.5 hrs | 6.5 hrs |
| Phase 2: RAG Pipeline | 12 hrs | 0 hrs | 12 hrs |
| Phase 3: Refusal + Function Calling | 10 hrs | 0 hrs | 10 hrs |
| Phase 4: Gate 1 Validation | 6 hrs | 0 hrs | 6 hrs |
| **Total** | **36 hrs** | **1.5 hrs** | **34.5 hrs** |

**Buffer**: 14-44 hrs (depending on 20-50 hr total availability)

---

## Gate 1 Criteria (May 5, 18:00 CET)

1. ❌ Function calling returns valid JSON with `refuse_and_escalate` tool call — **BLOCKED** (Ollama version)
2. ❌ 5/5 refusals trigger correctly — **BLOCKED** (Ollama version)
3. ❌ Multilingual RAG: Hindi + Marathi queries return relevant chunks (>0.7 similarity) — **NOT STARTED**
4. ❌ Latency ≤12s per query — **NOT STARTED**

**Status**: 0/4 criteria met, 1 critical blocker

---

## Notes

- Boundary card v0.1 complete with 16 answerable (protocol) + 16 refusal (diagnostic/prescriptive) entries
- All scaffold files follow hackathon requirements
- Engineering lineage from AgriNexus AI documented in README
- No coding past 22:00 CET rule in effect

---

**Next update**: May 3, 09:00 CET (after Ollama update)
