# Cactus backend path — hackathon POC

**Goal:** Show judges that **Sub-Centre Mind is not locked to Ollama** — the same RAG, gate, nudges, audit, and refusal tools run when `SCM_BACKEND=cactus` and HTTP points at an **Ollama-compatible** surface. Today that surface is either **Ollama itself** or this **dev shim** (forwarding to Ollama). A **native Kotlin + libcactus** companion on the ANM’s phone will implement the **same two routes** for the Special Technology Track (Cactus) story.

## What runs today

| Layer | Role |
|-------|------|
| **Streamlit + Python moat** | Unchanged — `get_backend()` reads `SCM_BACKEND` |
| **`CactusBackend`** | HTTP client to `SCM_CACTUS_HTTP_BASE` + `/api/generate`, `/api/chat` (same JSON as Ollama) |
| **This POC** | `scripts/cactus_bridge_shim.py` — forwards those paths to `ollama serve` |
| **Production target** | Android app: Cactus / Gemma on-device, same JSON contract — see [ADR-0001](adr/0001-runtime-architecture-edge-deployment.md) |

## LiteRT

**Not in this POC.** LiteRT remains an **alternative edge runtime** in ADR Option A (Pi + phone). No separate LiteRT binary is required to validate the Python app; pick LiteRT only if you want that prize line explicitly.

## One-terminal checklist (local demo)

1. **Ollama** (if not already running):

   ```bash
   ollama serve
   ```

2. **Shim** (new terminal):

   ```bash
   bash scripts/run_cactus_shim.sh
   ```

3. **App with Cactus backend** (third terminal, from repo root):

   ```bash
   export SCM_BACKEND=cactus
   export SCM_CACTUS_HTTP_BASE=http://127.0.0.1:18765
   bash scripts/warmup.sh    # optional; hits Ollama via shim if you point warmup at same env — today warmup talks to Ollama directly; for cold-start still run ollama
   bash scripts/run_app.sh
   ```

4. Open **Ask** tab, run a Hindi IFA query and a refusal query — behaviour should match the Ollama-only path.

5. **Gate 1 script** (optional — `g1_checks` may call Ollama directly; for Cactus-path proof use the UI or `query_router` with env set):

   ```bash
   export SCM_BACKEND=cactus SCM_CACTUS_HTTP_BASE=http://127.0.0.1:18765
   python -c "from pathlib import Path; import os, sys; sys.path.insert(0,'src'); os.environ.setdefault('SCM_INDEX_DIR','data/index'); from query_router import orchestrate_query; r=orchestrate_query('IFA tablet dose for pregnant women per MoHFW?', index_dir=Path('data/index')); print(r.tool_name, r.tool_arguments.get('answer','')[:200])"
   ```

## Video / write-up tip

- **10–20 s clip:** terminal showing `run_cactus_shim.sh` + env vars + browser tab with Streamlit answering.  
- **Voice-over:** “Gate 1 verified on Ollama; the same stack runs through the **Cactus backend URL** — this shim stands in for the on-phone companion until the Kotlin build ships.”

## Honesty bar

Calling this shim “Cactus” in a **prize** sense is accurate only if you frame it as **wire compatibility + backend swap verified**; the **Cactus SDK** prize line strengthens when you add **real** on-device inference. Use this POC to de-risk the story, not to claim a finished Play Store app.
