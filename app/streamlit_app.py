"""Sub-Centre Mind — local-first demo UI (Streamlit).

Three tabs drive the existing modules end-to-end:
    1. Ask     — protocol Q&A with retrieval + confidence gate + optional tools
    2. Nudges  — closed-loop follow-up state machine, persisted to JSON
    3. Report  — audit JSONL → aggregate stats → draft supervisor summary

Everything runs against the local Ollama (`gemma4:latest` by default).
No PHI leaves the device; use synthetic / pseudonymous identifiers in demos.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

_REPO = Path(__file__).resolve().parent.parent
_SRC = _REPO / "src"
for p in (_SRC, _REPO):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)

import streamlit as st

from audit.report import aggregate, llm_narrative, template_summary
from audit.schema import append_event, iter_events, new_event
from nudges import (
    Nudge,
    NudgeOutcome,
    NudgeState,
    advance,
    load_nudges,
    new_nudge,
    save_nudges,
    upsert,
)
from vision import (
    VisionResult,
    describe_medicine_packet,
    read_printed_text,
    read_register_row,
)


# --- paths / defaults --------------------------------------------------------
DEFAULT_INDEX_DIR = Path(os.environ.get("SCM_INDEX_DIR", "data/index"))
DEFAULT_AUDIT_LOG = Path(os.environ.get("SCM_AUDIT_LOG", "data/logs/dev_events.jsonl"))
DEFAULT_NUDGE_STORE = Path(os.environ.get("SCM_NUDGE_STORE", "data/nudges/store.json"))
DEFAULT_MIN_SIM = float(os.environ.get("SCM_RETRIEVAL_MIN_SIM", "0.7"))
DEFAULT_NUM_PREDICT = int(os.environ.get("SCM_NUM_PREDICT", "220"))
DEFAULT_MODEL = os.environ.get("SCM_MODEL", "gemma4:latest")


# --- styling helpers ---------------------------------------------------------
STATE_COLORS = {
    NudgeState.SCHEDULED: ("⏳", "Scheduled"),
    NudgeState.SENT: ("📤", "Sent"),
    NudgeState.CONFIRMED: ("✅", "Confirmed"),
    NudgeState.NO_RESPONSE: ("⚠️", "No response"),
    NudgeState.ESCALATED: ("🚑", "Escalated"),
}


def _state_badge(s: NudgeState) -> str:
    icon, label = STATE_COLORS[s]
    return f"{icon} **{label}**"


# --- page ---------------------------------------------------------------------
st.set_page_config(
    page_title="Sub-Centre Mind",
    page_icon="🩺",
    layout="wide",
)

st.title("Sub-Centre Mind")
st.caption(
    "Local clinical decision support for ANMs · Gemma 4 E4B · "
    "grounded retrieval · structured refusal · closed-loop follow-up"
)

# --- sidebar -----------------------------------------------------------------
with st.sidebar:
    st.subheader("Settings")
    index_dir = Path(st.text_input("Index directory", value=str(DEFAULT_INDEX_DIR)))
    audit_log = Path(st.text_input("Audit log (JSONL)", value=str(DEFAULT_AUDIT_LOG)))
    nudge_store = Path(st.text_input("Nudge store (JSON)", value=str(DEFAULT_NUDGE_STORE)))
    model = st.text_input("Ollama model tag", value=DEFAULT_MODEL)

    st.divider()
    st.subheader("Retrieval / Gate")
    min_sim = st.slider(
        "Confidence threshold (top semantic similarity)",
        min_value=0.30,
        max_value=0.95,
        value=DEFAULT_MIN_SIM,
        step=0.01,
        help="If top retrieved chunk scores below this, the LLM is not called.",
    )
    gate_on = st.checkbox("Enable confidence gate", value=True)
    top_k = st.slider("Top-K chunks", min_value=3, max_value=10, value=5)
    num_predict = st.slider(
        "num_predict (response length)",
        min_value=80,
        max_value=512,
        value=DEFAULT_NUM_PREDICT,
        step=20,
    )

    st.divider()
    st.caption(
        "All processing local. PHI must be pseudonymized before recording demos. "
        "WhatsApp transport is intentionally not wired in v1."
    )


# --- propagate to env so existing modules pick up ----------------------------
os.environ["SCM_INDEX_DIR"] = str(index_dir)
os.environ["SCM_RETRIEVAL_MIN_SIM"] = str(min_sim)
os.environ["SCM_CONFIDENCE_GATE"] = "1" if gate_on else "0"
os.environ["SCM_MODEL"] = model
os.environ["SCM_NUM_PREDICT"] = str(num_predict)


# --- imports that need env / heavy deps to be in place -----------------------
def _generate_lazy():
    """Import generate lazily so the UI loads even if torch/faiss are slow."""
    from rag.generate import generate_answer

    return generate_answer


def _orchestrator_lazy():
    from query_router import OrchestratorResult, orchestrate_query

    return orchestrate_query, OrchestratorResult


# --- tabs --------------------------------------------------------------------
tab_ask, tab_photo, tab_nudges, tab_report = st.tabs(
    ["💬 Ask", "📷 Photo", "🔔 Nudges", "📋 Report"]
)


# =============================================================================
# Tab 1 — Ask
# =============================================================================
with tab_ask:
    st.subheader("Protocol Q&A — grounded, with citations")

    # --- voice input (optional, faster-whisper local) ---
    with st.expander("🎙️ Voice input (Hindi / Marathi / English)", expanded=False):
        st.caption(
            "Local Whisper (faster-whisper, CPU). First use downloads the model. "
            "Transcript becomes the question below."
        )

        _LANG_OPTIONS = {
            "Hindi (हिन्दी)": "hi",
            "Marathi (मराठी)": "mr",
            "English": "en",
            "Auto-detect": None,
        }
        selected_lang_label = st.selectbox(
            "Spoken language",
            options=list(_LANG_OPTIONS.keys()),
            index=0,
            help=(
                "Choose the language you are speaking. "
                "Selecting Hindi or Marathi prevents Whisper from mis-transcribing "
                "to Urdu/Arabic script."
            ),
        )
        selected_lang_code = _LANG_OPTIONS[selected_lang_label]

        try:
            audio = st.audio_input("Record a short query")
        except AttributeError:
            audio = None
            st.info("Streamlit ≥ 1.31 is required for in-browser recording.")

        if audio is not None and st.button("Transcribe and use as question"):
            with st.spinner("Transcribing locally..."):
                try:
                    from rag.lang import contains_arabic_script
                    from voice import ASRUnavailable, transcribe_with_hindi_fallback
                    raw = audio.read() if hasattr(audio, "read") else audio.getvalue()
                    if selected_lang_code is not None:
                        from voice import transcribe as _transcribe
                        res = _transcribe(raw, language=selected_lang_code)
                    else:
                        res = transcribe_with_hindi_fallback(raw)
                    if contains_arabic_script(res.text):
                        st.warning(
                            f"Whisper returned Urdu/Arabic script "
                            f"(detected: {res.language} · {res.language_probability:.2f}). "
                            "Switch the language selector to **Hindi** and record again."
                        )
                    else:
                        st.session_state["ask_query"] = res.text
                        st.session_state["ask_query_lang"] = res.language
                        st.session_state["ask_query_lang_source"] = "asr"
                        st.success(
                            f"Transcribed ({res.language} · {res.language_probability:.2f}): "
                            f"{res.text}"
                        )
                except ASRUnavailable as e:
                    st.warning(str(e))
                except Exception as e:
                    st.error(f"ASR failed: {e}")

    col_q, col_btn = st.columns([4, 1])
    with col_q:
        query = st.text_input(
            "Question (English / Hindi / Marathi)",
            placeholder="iron and folic acid supplementation in antenatal period",
            key="ask_query",
        )
    with col_btn:
        st.write("")
        st.write("")
        submit = st.button("Ask", type="primary", use_container_width=True)

    use_tools = st.checkbox(
        "Also run tool-calling (refuse_and_escalate / answer_protocol_question)",
        value=False,
        help="Adds a second pass via /api/chat with the Gate 1 tool contract.",
    )

    if submit and query.strip():
        with st.spinner("Retrieving + reasoning locally..."):
            try:
                generate_answer = _generate_lazy()
                out = generate_answer(
                    query.strip(),
                    index_dir=index_dir,
                    model=model,
                    top_k=top_k,
                    num_predict=num_predict,
                )
            except Exception as e:
                st.error(f"Generation failed: {e}")
                out = None

        if out is not None:
            top_sim = out.retrieved[0].semantic_score if out.retrieved else 0.0

            mcols = st.columns(4)
            mcols[0].metric("Top similarity", f"{top_sim:.3f}")
            mcols[1].metric("Threshold", f"{min_sim:.2f}")
            mcols[2].metric(
                "Gate", "BLOCKED" if out.confidence_blocked else "PASSED",
            )
            mcols[3].metric("Chunks", len(out.retrieved))

            if out.confidence_blocked:
                st.warning(
                    "Confidence gate blocked: top retrieval similarity is below threshold. "
                    "The local model was **not** called. Escalate or rephrase."
                )

            st.markdown("### Answer")
            st.write(out.answer)

            if out.retrieved:
                st.markdown("### Citations")
                rows = [
                    {
                        "#": i + 1,
                        "source": c.source_file,
                        "page": c.page,
                        "rank (rerank)": round(c.score, 3),
                        "sim (cosine)": round(c.semantic_score, 3),
                    }
                    for i, c in enumerate(out.retrieved)
                ]
                st.dataframe(rows, hide_index=True, use_container_width=True)

            try:
                from rag.lang import detect_language

                asr_lang = st.session_state.get("ask_query_lang")
                lang_source = st.session_state.get("ask_query_lang_source")
                if asr_lang and lang_source == "asr":
                    query_lang = asr_lang
                else:
                    query_lang = detect_language(query)
                append_event(
                    audit_log,
                    new_event(
                        "confidence_gate_blocked"
                        if out.confidence_blocked
                        else "rag_answer",
                        top_sim=float(top_sim),
                        confidence_blocked=bool(out.confidence_blocked),
                        query_preview=query.strip()[:160],
                        query_lang=query_lang,
                    ),
                )
                # Reset ASR-source flag so the next typed query is detected
                # by heuristic, not stamped with the previous Whisper code.
                st.session_state["ask_query_lang_source"] = None
            except Exception as e:
                st.info(f"(audit append skipped: {e})")

            if use_tools:
                st.markdown("---")
                st.markdown("### Tool call (Gate 1 contract)")
                with st.spinner("Calling /api/chat with tools..."):
                    try:
                        orchestrate_query, _ = _orchestrator_lazy()
                        r = orchestrate_query(
                            query.strip(),
                            index_dir=index_dir,
                            model=model,
                            top_k=top_k,
                        )
                    except Exception as e:
                        st.error(f"Tool call failed: {e}")
                        r = None
                if r is not None:
                    st.write(f"**Tool name:** `{r.tool_name or '(none)'}`")
                    if r.tool_arguments:
                        st.json(r.tool_arguments)
                    if r.tool_name == "refuse_and_escalate":
                        try:
                            append_event(
                                audit_log,
                                new_event(
                                    "tool_refusal",
                                    urgency=r.tool_arguments.get("urgency"),
                                    reason=r.tool_arguments.get("reason", "")[:160],
                                ),
                            )
                        except Exception:
                            pass
                    elif r.tool_name == "answer_protocol_question":
                        try:
                            append_event(
                                audit_log,
                                new_event(
                                    "tool_protocol",
                                    confidence=r.tool_arguments.get("confidence"),
                                ),
                            )
                        except Exception:
                            pass


# =============================================================================
# Tab 2 — Photo (Gemma 4 vision, bounded use cases)
# =============================================================================
with tab_photo:
    st.subheader("Vision — bounded use cases")
    st.caption(
        "Gemma 4 reads a photo and returns text. We **never** interpret medical "
        "images here (no rashes, ECGs, ultrasounds). Vision is for routing, "
        "OCR, and draft fields only."
    )

    use_case = st.radio(
        "Use case",
        options=[
            ("printed_text", "Printed protocol / poster — read text"),
            ("medicine_packet", "Medicine packet — read brand & dose, escalate"),
            ("register_row", "Register row — extract fields for ANM to confirm"),
        ],
        format_func=lambda x: x[1],
        horizontal=False,
        key="vision_use_case",
    )
    uploaded = st.file_uploader(
        "Upload a JPG / PNG (or take a photo on a phone and upload)",
        type=["png", "jpg", "jpeg"],
    )

    if uploaded is not None:
        st.image(uploaded, caption=uploaded.name, use_container_width=True)

    feed_to_rag = st.checkbox(
        "After OCR, retrieve grounded protocol citations using the extracted text",
        value=False,
    )

    if uploaded is not None and st.button("Analyze image", type="primary"):
        with st.spinner("Calling Gemma 4 vision locally..."):
            image_bytes = uploaded.getvalue()
            try:
                if use_case[0] == "printed_text":
                    res = read_printed_text(image_bytes, num_predict=num_predict)
                elif use_case[0] == "medicine_packet":
                    res = describe_medicine_packet(image_bytes, num_predict=num_predict)
                else:
                    res = read_register_row(image_bytes, num_predict=num_predict)
            except Exception as e:
                st.error(f"Vision failed: {e}")
                res = None

        if res is not None:
            st.markdown("### Extracted text")
            st.code(res.text or "(empty)")
            st.info(f"Boundary: {res.boundary_note}")

            try:
                append_event(
                    audit_log,
                    new_event(
                        "tool_protocol" if use_case[0] != "medicine_packet" else "tool_refusal",
                        kind_detail="vision",
                        use_case=res.use_case,
                        chars=len(res.text or ""),
                    ),
                )
            except Exception:
                pass

            if feed_to_rag and (res.text or "").strip():
                with st.spinner("Retrieving citations from indexed PDFs..."):
                    try:
                        generate_answer = _generate_lazy()
                        out = generate_answer(
                            res.text.strip(),
                            index_dir=index_dir,
                            model=model,
                            top_k=top_k,
                            num_predict=num_predict,
                        )
                    except Exception as e:
                        st.error(f"RAG follow-up failed: {e}")
                        out = None

                if out is not None:
                    st.markdown("### Grounded answer + citations")
                    st.write(out.answer)
                    if out.retrieved:
                        rows = [
                            {
                                "#": i + 1,
                                "source": c.source_file,
                                "page": c.page,
                                "rank": round(c.score, 3),
                                "sim": round(c.semantic_score, 3),
                            }
                            for i, c in enumerate(out.retrieved)
                        ]
                        st.dataframe(rows, hide_index=True, use_container_width=True)


# =============================================================================
# Tab 3 — Nudges
# =============================================================================
with tab_nudges:
    st.subheader("Closed-loop follow-up — state machine view")
    st.caption(
        f"Persisted to `{nudge_store}`. Demo only — no real WhatsApp / SMS transport in v1."
    )

    nudges: list[Nudge] = load_nudges(nudge_store)

    with st.expander("➕ New nudge", expanded=not nudges):
        with st.form("new_nudge_form", clear_on_submit=True):
            nf_recipient = st.text_input(
                "Recipient pseudonym",
                value="P-001-pseudo",
                help="Use a synthetic ID. Never a real patient name in demos.",
            )
            nf_template = st.selectbox(
                "Template",
                options=[
                    "ifa_followup_d1",
                    "ifa_followup_d3",
                    "anc_visit_d3",
                    "immunization_d7",
                ],
                index=0,
            )
            nf_when = st.date_input(
                "Schedule date",
                value=(datetime.now(timezone.utc) + timedelta(days=1)).date(),
            )
            nf_max_retries = st.number_input(
                "Max retries", min_value=0, max_value=5, value=1, step=1
            )
            submitted = st.form_submit_button("Create nudge")
            if submitted:
                scheduled_dt = datetime.combine(
                    nf_when, datetime.min.time(), tzinfo=timezone.utc
                )
                n = new_nudge(
                    recipient_ref=nf_recipient.strip() or "P-anon",
                    template_id=nf_template,
                    scheduled_at=scheduled_dt,
                    max_retries=int(nf_max_retries),
                )
                nudges = upsert(nudges, n)
                save_nudges(nudge_store, nudges)
                st.success(f"Created {n.id[:8]}")
                st.rerun()

    if not nudges:
        st.info("No nudges yet. Create one above.")
    else:
        for n in nudges:
            with st.container(border=True):
                head = st.columns([3, 2, 2, 1])
                head[0].markdown(f"**{n.recipient_ref}** · `{n.template_id}`")
                head[1].markdown(_state_badge(n.state))
                head[2].markdown(
                    f"retries: `{n.retries}/{n.max_retries}` · "
                    f"sched: `{n.scheduled_at.strftime('%Y-%m-%d')}`"
                )
                head[3].caption(f"id: `{n.id[:8]}`")

                if n.history:
                    with st.expander("History", expanded=False):
                        for ts, ev in n.history:
                            st.write(f"`{ts}` — {ev}")

                actions = st.columns(4)
                if actions[0].button("Mark sent", key=f"sent-{n.id}"):
                    updated = advance(n, NudgeOutcome.DISPATCH_OK)
                    nudges = upsert(nudges, updated)
                    save_nudges(nudge_store, nudges)
                    st.rerun()
                if actions[1].button("Confirmed", key=f"conf-{n.id}"):
                    updated = advance(n, NudgeOutcome.REPLY_CONFIRMED)
                    nudges = upsert(nudges, updated)
                    save_nudges(nudge_store, nudges)
                    st.rerun()
                if actions[2].button("No reply", key=f"none-{n.id}"):
                    updated = advance(n, NudgeOutcome.NO_REPLY_TIMEOUT)
                    nudges = upsert(nudges, updated)
                    save_nudges(nudge_store, nudges)
                    st.rerun()
                if actions[3].button("Dispatch failed", key=f"fail-{n.id}"):
                    updated = advance(n, NudgeOutcome.DISPATCH_FAILED)
                    nudges = upsert(nudges, updated)
                    save_nudges(nudge_store, nudges)
                    st.rerun()


# =============================================================================
# Tab 4 — Report
# =============================================================================
with tab_report:
    st.subheader("Draft supervisor report (not an HMIS submission)")
    st.caption(f"Source: `{audit_log}`")

    if not audit_log.is_file():
        st.info(
            "No audit log yet. Ask a question on the **Ask** tab to start the JSONL trail."
        )
    else:
        stats = aggregate(audit_log)

        cols = st.columns(4)
        cols[0].metric("Events", stats["total_events"])
        cols[1].metric("Gate-blocked", stats["confidence_gate_blocked_count"])
        cols[2].metric(
            "Avg top sim",
            f"{stats['top_sim_avg']:.3f}" if stats.get("top_sim_avg") is not None else "—",
        )
        cols[3].metric("Languages logged", len(stats.get("queries_by_language") or {}))

        st.markdown("### By type")
        st.json(stats.get("by_kind") or {})

        st.markdown("### Event timeline")
        rows = [
            {
                "ts": ev.ts_iso,
                "kind": ev.kind,
                "detail": ev.detail,
            }
            for ev in iter_events(audit_log)
        ]
        st.dataframe(rows, hide_index=True, use_container_width=True)

        st.markdown("### Draft summary (template)")
        draft = template_summary(stats)
        st.code(draft, language="markdown")
        st.download_button(
            "Download draft (.md)",
            data=draft,
            file_name="sub-centre-draft.md",
            mime="text/markdown",
        )

        with st.expander("➕ Add Gemma narrative (optional, calls Ollama)"):
            if st.button("Generate narrative"):
                with st.spinner("Asking Gemma to summarize the stats..."):
                    try:
                        text = llm_narrative(stats, model=model)
                        st.markdown(text)
                    except Exception as e:
                        st.error(f"LLM narrative failed: {e}")
