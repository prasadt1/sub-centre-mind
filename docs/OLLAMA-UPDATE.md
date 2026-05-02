# Ollama Update Guide — Sub-Centre Mind

**Critical blocker**: Gemma 4 requires newer Ollama version than 0.18.3

---

## Update Steps

### 1. Download Latest Ollama

Visit: https://ollama.com/download

**macOS**: Download the `.dmg` file and install

### 2. Verify Installation

```bash
ollama --version
```

Expected: Version > 0.18.3 (likely 0.5.x or higher)

### 3. Restart Ollama Service

```bash
# Kill existing service
pkill ollama

# Start new service (Ollama.app will auto-start)
# Or manually: open /Applications/Ollama.app
```

### 4. Verify Service Running

```bash
ps aux | grep ollama
```

Expected: Process running with new version

### 5. Re-pull Gemma 4 Model

```bash
ollama pull gemma4:latest
```

Expected: Download completes without 412 error

### 6. Run Smoke Test

```bash
ollama run gemma4:latest "IFA tablet dose for pregnant women per MoHFW?"
```

Expected: Response about 180 tablets (1 daily for 180 days post-conception)

---

## Verification Checklist

- [ ] Ollama version > 0.18.3
- [ ] Gemma 4 model pulls without error
- [ ] Smoke test returns valid response
- [ ] Latency measured (target: <12s)
- [ ] Function calling test (see below)

---

## Function Calling Test

After smoke test passes, verify function calling support:

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "gemma4:latest",
  "prompt": "Is 140/90 high BP?",
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "refuse_and_escalate",
        "description": "Refuse to answer diagnostic/prescriptive queries and escalate to Medical Officer",
        "parameters": {
          "type": "object",
          "properties": {
            "reason": {"type": "string"},
            "escalation_target": {"type": "string"},
            "urgency": {"type": "string", "enum": ["low", "medium", "high", "critical"]}
          },
          "required": ["reason", "escalation_target", "urgency"]
        }
      }
    }
  ]
}'
```

Expected: JSON response with `tool_calls` array containing `refuse_and_escalate` call

---

## Troubleshooting

### Issue: Model still fails to load

**Solution**: Remove corrupted model and re-pull

```bash
ollama rm gemma4:latest
ollama pull gemma4:latest
```

### Issue: Function calling not supported

**Fallback**: Use regex-based refusal classifier (see `src/refusal/classifier.py`)

### Issue: Latency >12s

**Optimizations**:
1. Reduce chunk size in RAG pipeline (512 → 256 tokens)
2. Reduce top-k retrieval (5 → 3 chunks)
3. Optimize prompt template (remove verbose instructions)

---

## Kill Switch Criteria

If after Ollama update:

1. Gemma 4 still fails to load → **WITHDRAW**
2. Function calling not supported AND regex fallback fails → **WITHDRAW**
3. Latency consistently >15s with all optimizations → **WITHDRAW**

**No heroics** — Gate 1 failure = withdraw from hackathon

---

## Post-Update Actions

1. Update `docs/STATUS.md` with results
2. Run full smoke test suite
3. Begin RAG pipeline implementation
4. Commit progress: `git commit -am "Fix: Update Ollama, verify Gemma 4"`

---

**Owner**: Prasad  
**Deadline**: May 3, 09:00 CET
