# Stakeholder Rationale — Vision, Mission, and Why Sub-Centre Mind Exists

**Audience:** Hackathon judges, government health officials, funders, or anyone who asks *"so what?"*

**Companion:** [README](../README.md) (product overview, quick start, technical detail)

---

## Brand (adopted)

| Element | Text |
|---------|------|
| **Product name** | **Sub-Centre Mind** — keep; already in repo, URL, and ADR; globally readable. |
| **Tagline** | *Offline closed-loop co-pilot for India's last-mile maternal health — recall, track, report, refuse.* |
| **Punchline** (video, deck, hero caption) | *When the cloud disconnects, care still connects.* |

---

## Vision

Every frontline health worker in India — ANM, and in a fuller rollout [ASHA](https://en.wikipedia.org/wiki/Accredited_Social_Health_Activist), AWW — should have an **offline AI co-pilot** on the phone she already owns: grounded in official protocols, accountable through closed-loop follow-through, and **provably** refusing to overstep its role.

**Today:** the implementation centres on the **Sub-Centre ANM**. In the real care chain, the [ASHA](https://en.wikipedia.org/wiki/Accredited_Social_Health_Activist) brings pregnant women to the ANM, couples for family planning counselling, and children to immunisation sessions — she is the **village bridge** to the facility. A natural **Tier 2** extension is for the ANM to assign nudge follow-up to the ASHA’s phone (field confirmation), while Tier 1 remains protocol + escalation authority at the sub-centre. **Patient-facing** access (Tier 3) needs a **separate** prompt, safety, and literacy layer — roadmap only, not claimed today.

---

## Mission

To put a **verifiable, voice-first, offline clinical co-pilot** in the hands of India's ~170,000 Sub-Centre ANMs — answering protocol questions, tracking patient follow-ups, drafting supervisor reports, and **structurally refusing** to diagnose — **without** a single byte of patient-identifiable data leaving her device.

---

## One-paragraph pitch

**Sub-Centre Mind** is an offline, voice-first clinical co-pilot for India's [Auxiliary Nurse Midwives](https://en.wikipedia.org/wiki/Auxiliary_nurse_midwife) — the trained nurse–midwives who staff each of the country's ~170,000 [Sub-Centres](https://en.wikipedia.org/wiki/Public_health_system_in_India#Sub_Centres), serving about 3,000–5,000 people with no doctor on site and often no reliable internet. Built on **Gemma 4 E4B** running entirely on-device (Gate 1: **Ollama**), it answers protocol questions in seconds (Hindi, Marathi, English) grounded in **11** indexed MoHFW/WHO guideline PDFs, tracks follow-ups via a **closed-loop nudge** state machine, drafts supervisor reports from a **local audit trail**, and structurally refuses to diagnose — enforced by a **versioned, machine-readable** safety contract ([`boundary_card.json`](../boundary_card.json)) verifiable in minutes via `scripts/g1_checks.sh`. It is what a frontline worker needs when the cloud disconnects: **protocol recall, follow-through, and proof.**

---

## The differentiator (integration, not one file)

The moat is **not** any single artifact — it is the **integration**:

- an LLM **small enough** to run locally (**Gemma 4 E4B**),
- **grounded** in the right corpus (MoHFW/WHO),
- **gated** by retrieval confidence before generation,
- **bounded** by a verifiable refusal contract + native **function calling**,
- **closed-looped** through a nudge engine and **audited** end-to-end,

**all offline.** Cloud chatbots are more capable; government digitisation tools handle reporting. Neither replaces what an ANM needs **during a patient contact with no signal**.

---

## Three things, offline

1. **Recalls** — protocol Q&A (RAG + confidence gate), voice-first, multilingual.  
2. **Tracks** — closed-loop nudges (IFA, ANC, immunization); state machine is local; **SMS/WhatsApp transport is roadmap**, not claimed as shipped.  
3. **Refuses** — tool-calling path fires `refuse_and_escalate` for diagnostic/prescriptive queries; every refusal names escalation target and urgency.

---

## Tech stack: today vs roadmap

| Today (Gate 1, verified) | Roadmap (see [ADR-0001](adr/0001-runtime-architecture-edge-deployment.md)) |
|--------------------------|----------------------------------------------------------------------------|
| Gemma 4 E4B via **Ollama** | **Cactus** on phone (HTTP bridge + native companion) |
| Hybrid **FAISS + BM25** retrieval | **LiteRT** as alternative edge runtime |
| **faster-whisper** ASR | **Unsloth** fine-tuning on protocol + refusal behaviour |
| **Streamlit** demo UI | ANM-first mobile shell; optional ASHA delivery UI |

**Accuracy:** Query routing and orchestration today are **Python** (`query_router.py`, RAG, gate). Cactus is **not** the production router until the companion ships.

---

## Decision matrix: why not just…?

| Dimension | Cloud LLM (Gemini / ChatGPT) | Govt digitisation (RCH / HMIS) | Sub-Centre Mind (local) |
|-----------|------------------------------|--------------------------------|-------------------------|
| Works **without** internet | No | Often no at point of care | **Yes** |
| MoHFW-grounded protocol answers | Generic / web mix | Not a Q&A product | **11 PDFs**, retrieval + gate |
| Patient follow-up accountability | Not built in | Registers, not behavioural loop | **Nudge state machine** |
| Supervisor report drafts | No | Manual tally → portal | **Audit JSONL → template** |
| Verifiable safety boundary | Best-effort | N/A | **boundary_card + g1_checks** |
| PHI leaves device | Yes (even “sovereign” cloud) | Submission path | **No egress path** (local design) |

---

## Devil's advocate FAQ (short)

**"It's just JSON."** — The JSON is the *spec*; the proof is **behaviour**: Gemma 4 reliably routes protocol vs clinical-overreach queries with tools + tests.

**"ANM already knows to refuse."** — The refusal is for the **AI**, not to teach the ANM; it blocks the model from becoming liability under pressure.

**"Why not Google?"** — Wrong corpus, online, slow, not auditable to MoHFW line.

**"Why not subsidised Gemini + sovereign cloud?"** — Connectivity + procurement latency + recurring OPEX; still not a nudge + audit workflow product.

**"Will her phone run E4B?"** — Not all phones today; tiered deployment (lighter model, Pi companion) in ADR.

---

## Honest limitations

- Boundary set is **demo-scale** (v0.1); expandable.  
- **No** adversarial test battery yet.  
- Model can still err **inside** answerable zone; gate reduces but does not eliminate risk.  
- Nudge **transport** (SMS/WhatsApp) not wired — state machine only.  
- **Field pilots** post-hackathon for usability proof.

---

## Reading order

1. [README](../README.md)  
2. This document  
3. [`boundary_card.json`](../boundary_card.json)  
4. `bash scripts/g1_checks.sh`  
5. [ADR-0001](adr/0001-runtime-architecture-edge-deployment.md)  
6. Live demo: `bash scripts/warmup.sh && bash scripts/run_app.sh`
