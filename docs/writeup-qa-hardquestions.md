# Sub-Centre Mind — Hard Questions & Writeup Answers

These are the adversarial questions a judge, reviewer, or domain expert will ask.
Each entry has: the question, a short honest answer, and suggested writeup language.

**Abbreviations:** See **Appendix G — Glossary** at the end of this file.

---

## 1) “Isn’t this just a local RAG chatbot?”

**Honest answer:** At the infrastructure layer, yes — retrieval + generation + function routing + a follow‑up scheduler. The differentiator is whether this combination removes real risk and workload better than the alternative.

The alternative for an ANM at 9pm is: call the MO (often unreachable), guess from memory, or tell the patient to wait until morning. Sub‑Centre Mind adds a fourth option: grounded, refusing, source‑cited response with automatic escalation when the query crosses into diagnostic/prescriptive territory.

**Writeup language:**

> “Sub‑Centre Mind is not a novel architecture. It is a deliberate application of proven components — local inference, grounded retrieval, and structured refusal routing — to a setting where the absence of decision support creates avoidable risk and administrative burden.”

---

## 2) “Wouldn’t the ANM already know the answers from experience?”

**Honest answer:** For routine cases — yes. An experienced ANM knows IFA dosing and common danger signs. The system is not for routine cases. It’s for:

- Edge cases she genuinely wants to confirm (interactions, borderline readings, protocol nuance)
- Patient/family messages that arrive after hours via WhatsApp/SMS
- Confirming a protocol before acting on something she hasn’t done recently
- Having a citable source if a decision is questioned later

Analogy: checklists are not used because experts don’t know steps; they’re used because cognitive load and interruptions cause errors even in experts.

**Writeup language:**

> “Sub‑Centre Mind is not designed for what ANMs already know. It is designed for the edge cases, the after‑hours patient query, and the protocol confirmation before acting — the small number of moments per clinic that matter most and have no reliable support today.”

---

## 3) “How is this different from any other RAG solution in healthcare?”

**Three concrete differences:**

1. **Published refusal contract (Decision Boundary Card):** A machine‑readable, versioned spec of what the system answers, what it refuses, and who it escalates to — testable and auditable.
2. **Closed‑loop accountability:** The system doesn’t stop at the response; it follows up until confirmation (“ली”) or escalation. Most RAG chatbots stop at one answer.
3. **Native function calling as the refusal mechanism:** Refusal/escalation is a typed tool call (`refuse_and_escalate(...)`) with traceable arguments, not a “prompt suggestion.”

---

## 4) “You still need a ~$200 machine at every sub‑centre. Who pays? Who maintains it?”

**Honest answer:** This is one of the hardest questions and we don’t fully solve it in a hackathon.

What we can say honestly:

- Deployment unit is the **sub‑centre**, not “every village.”
- A mini‑PC is comparable to other clinic equipment procurement cycles.
- Maintenance would follow the same model as other clinic devices (district IT / vendor support).

What we do **not** claim to solve: procurement approval cycles, last‑mile maintenance capacity, and training. Those are real barriers.

**Writeup language:**

> “We do not solve procurement or maintenance. We solve the technical product question: given a low‑cost compute node at a sub‑centre, what becomes possible with local inference and a published refusal contract?”

---

## 5) “How many devices are needed — per village? per panchayat?”

**Honest answer:** The unit is the **sub‑centre** (often ~3,000–5,000 population). One node serves one ANM’s coverage area; it is not per household.

**Writeup language:**

> “The deployment unit is the sub‑centre, not the village. One compute node serves one ANM’s coverage population of ~3,000–5,000.”

---

## 6) “Will local government actually invest in this? Who is the buyer?”

**Honest answer:** Not from a hackathon demo alone. Government adoption needs evidence from pilots. A realistic early path is NGO/foundation pilots or a state NHM pilot, then evidence → scale.

**Writeup language:**

> “Government adoption of clinical decision support requires evidence from field pilots. The immediate path is through pilot partners; the system’s open architecture and refusal contract are designed to make pilots evaluable and reproducible.”

---

## 7) “What if the model gives wrong advice? Who is liable?”

**Honest answer:** This is why the refusal contract exists.

- Sub‑Centre Mind does not diagnose or prescribe.
- Every protocol answer includes a citation.
- The ANM remains the decision-maker; the system is a grounded second opinion.

**Writeup language:**

> “Sub‑Centre Mind reduces risk by providing a citable, grounded reference — not by replacing clinical judgment. The Decision Boundary Card makes explicit what the system will not decide.”

---

## 8) “Why Gemma 4 specifically? Couldn’t this be any 4B model?”

**Answer:** Three reasons to justify Gemma 4 in the submission:

1. **Native function calling** for auditable refusal/escalation routing.
2. **Multilingual performance** (Hindi/Marathi/Telugu) for grounded retrieval without translation layers.
3. **Open weights + local inference** to support data sovereignty (no third‑party LLM API sees PHI).

---

## 9) “Is this AI for the sake of AI? Rural maternal health is about transport, facilities, norms.”

**Honest answer:** Valid critique. We explicitly do not claim to fix transport, facility capacity, pay/incentives, or household decision dynamics.

We target a narrower, solvable slice:

- After‑hours patient messages
- Edge-case protocol confirmations
- Admin/report drafting burden

**Writeup language:**

> “Sub‑Centre Mind does not fix structural drivers. It addresses one solvable slice: protocol support, refusal‑and‑escalation, and administrative relief at the point of care.”

---

## 10) “This is a hackathon demo. Is it real?”

**Honest claim boundary:**

- Inference path is real: Gemma 4 E4B via Ollama, local, tool calling verified.
- Corpus is real: official MoHFW/WHO PDFs, indexed locally.
- Decision Boundary Card is real and versioned.
- Nudge loop is real and retargeted from AgriNexus’s closed-loop engine.
- HMIS draft is **demo-grade** unless proven otherwise.
- No field deployment claim; this is a proof-of-concept.

**Writeup language:**

> “This is a proof‑of‑concept with production‑grade architecture choices. We state clearly what is functional today and what remains demo‑grade.”

---

## Appendix A — Market alternatives, incumbent tools, and “why build new?”

These questions are meant for reviewers who’ve seen the broader landscape (government portals, CHW apps, commercial vendors).

### A1) “Doesn’t HMIS / DHIS2 / NHM portals already solve reporting?”

**Honest answer:** They solve **capture**, not **derivation**. Reporting portals record outputs once numbers exist; they don’t reduce the cognitive work to produce those numbers from scattered patient interactions, follow-ups, and field messages.

**Writeup language:**

> “National reporting systems are the destination, not the assistant. Sub‑Centre Mind is about turning week-long field reality into a reviewable draft the ANM can sign — not replacing the portal.”

### A2) “What about eSanjeevani / telemedicine / state health apps?”

**Honest answer:** Those systems optimize **remote clinician consults**. Sub‑Centre Mind targets **protocol grounding + refusal + local sovereignty + asynchronous messaging workflows** when a clinician is not available — different constraint.

### A3) “What about ASHA-facing apps (including Maatr)? Aren’t we duplicate?”

**Honest answer:** Many deployments optimize **frontline data capture** or **counseling**. Sub‑Centre Mind’s wedge is **auditably refusal-first routing**, plus **closed-loop follow-through**, anchored at the **sub-centre desk workflow**. Same ecosystem; different artifact.

### A4) “What about generic WhatsApp chatbots (Saheli-style)?”

**Honest answer:** Many are informational-only and lack a published refusal boundary + traceable escalations + grounding citations tied to official PDFs at retrieval time.

### A5) “Could CHWs just use ChatGPT / Gemini on the web?”

**Honest answer:** That violates typical PHI constraints, creates vendor lock-in, and yields non-auditable outputs. Local-first Gemma + citations + tool traces is the governance story.

---

## Appendix B — Architecture & feasibility challenges

### B1) “WhatsApp needs internet — so ‘local sovereignty’ is fake.”

**Honest answer:** Transport can be internet-mediated while **reasoning + PHI storage** remain on-prem. The claim is “**data sovereignty for the intelligence surface**,” not “no network exists.”

### B2) “RAG on PDFs is wrong if PDF text extraction is garbage.”

**Honest answer:** Real risk. Mitigation is OCR fallback / chunk QA / citation checks / refusing when retrieval confidence is low.

### B3) “Function calling won’t work reliably under pressure prompts.”

**Honest answer:** Also real; mitigate with strict tool routing prompts + evaluation harness + fallback refusal policy.

### B4) “Does this increase digital burden for ASHAs/ANMs?”

**Honest answer:** It can if designed poorly. The intent is **reduce** burden by automating drafts from existing messages and avoiding new manual logging — must be demonstrated, not asserted.

---

## Appendix C — Equity, gender, power dynamics

### C1) “Household decision-makers (mother-in-law/husband) matter more than ANM counseling.”

**Honest answer:** True at population level. Sub‑Centre Mind doesn’t fix intra-household power dynamics; it targets timely escalation + safer messaging when contact happens.

### C2) “Will patients trust AI?”

**Honest answer:** Patients trust **human escalation paths** and clear safety behavior. The demo should emphasize refusal + MO escalation, not “AI knows best.”

---

## Appendix D — Differentiation vs “just another RAG”

### D1) “What’s your moat if OpenAI ships better RAG tomorrow?”

**Honest answer:** The moat is not embeddings; it’s **the operational loop + refusal contract + deployment constraints** that make outcomes measurable.

### D2) “Why not fine-tune?”

**Honest answer:** Fine-tuning is high-risk under time constraints; tool routing + grounded retrieval + eval is faster and more auditable for a hackathon.

---

## Appendix E — ABDM, longitudinal CHW platforms, district IT, clinical governance

These are “production realism” questions: integration burden, ops, and accountability beyond the demo.

### E1) “Ayushman Bharat Digital Mission / ABHA — aren’t you supposed to plug into that?”

**Honest answer:** ABDM defines **identity, consent, and interoperable exchange** for longitudinal care records. Sub‑Centre Mind in POC form does **not** claim full ABDM integration. A honest path is: **optional** linkage behind explicit consent, with district-approved workflows — not automatic scraping of sensitive narratives into national pipes.

**Writeup language:**

> “We separate **assistant behavior at the sub-centre** from **national record-linkage policy**. A pilot would define consent, data minimization, and what gets summarized vs what stays local.”

### E2) “Patient messaging contains PHI — how is consent and minimization handled?”

**Honest answer:** Real deployments need **purpose limitation** (e.g., operational triage vs longitudinal research), **retention limits**, and **access controls** at facility level. The hackathon should state **what is designed-in** (local processing, refusal traces) vs **what still requires policy sign-off**.

### E3) “OpenSRP / CommCare already do longitudinal CHW workflows — why not extend them?”

**Honest answer:** Those platforms excel at **structured forms, schedules, and program fidelity**. Sub‑Centre Mind’s wedge is **unstructured inbound messages + grounded protocol answers + refusal-as-tool + closed-loop nudges** without forcing every interaction into a form first. In a mature stack, the assistant could **sit beside** a longitudinal platform (draft → structured fields), not replace it.

### E4) “Who patches the box, runs antivirus, and restores backups when ransomware hits?”

**Honest answer:** **District IT** (or a contracted MSP) must own **OS patching, disk encryption, offline backups, and restore drills**. The project should admit this explicitly; “local model” does not remove **endpoint hygiene**.

**Writeup language:**

> “Local inference shifts **where prompts are processed**; it does not eliminate **device security and backup discipline**. A rollout bundles the assistant with standard facility IT runbooks.”

### E5) “Where is the MO review queue — who clears escalations after hours?”

**Honest answer:** Escalation design must match **real staffing**: MO on-call rosters, PHC backup, or explicit “defer to morning” policies. A demo can show **queue + SLA placeholders**; production needs **ownership and escalation paths** written down.

### E6) “What audit trail exists if something goes wrong?”

**Honest answer:** Production needs **append-only event logs** (who/when/tool calls/citations), **config versioning** (Decision Boundary Card + corpus), and **incident response**: isolate device, preserve logs, notify supervisor. The hackathon can commit to **traceability principles** and stub retention policies.

### E7) “Is this a medical device / clinical decision support under regulation?”

**Honest answer:** Jurisdiction-specific. The honest stance: position as **information + workflow assist** with refusal boundaries and human-in-the-loop; **legal review** before claims of diagnostic support. Do not bluff regulatory clearance.

---

## Appendix F — Supplement (incl. external review): WhatsApp+API, NHM apps, benchmarks, TCO, competitors

Many of these overlap earlier sections — noted inline so you don’t repeat yourself in the writeup.

### F1) “Why not WhatsApp + ChatGPT / Claude API? Simpler.”

**Overlap:** Partially covered by **§A5** (consumer LLMs). Worth adding explicitly: **cloud API + PHI**, **recurring cost at scale**, **offline/fragile connectivity**, **audit ownership**.

**Honest answer:** Cloud APIs can be stronger models, but they move prompts/responses into vendor-controlled infrastructure unless you build heavy redaction — still risky for identifiable narratives. Local inference trades peak capability for **sovereignty + offline availability + predictable unit economics** after hardware purchase. API spend scales with query volume; a sub-centre node amortizes.

### F2) “Practo / mfine / Tata 1mg already exist. Why reinvent?”

**Overlap:** **§A2** (telemedicine framing). Add the **B2C marketplace** angle.

**Honest answer:** Those products optimize **patient-initiated consults** and consumer journeys. Sub‑Centre Mind targets **public-sector ANM workflow**, protocol grounding, refusal routing, and closed-loop follow-up — not booking a doctor appointment.

### F3) “NHM already has ANMOL, RCH, HMIS. Why another system?”

**Overlap:** **§A1** (HMIS/reporting). Naming ANMOL/RCH makes the critique concrete.

**Honest answer:** ANMOL/RCH/HMIS excel at **registration, schedules, and reporting capture**. They generally do not provide **after-hours, conversational protocol assistance with citations + auditable refusal** for edge-case messages. Position as **complement**: drafts/answers feed work that still lands in official systems.

### F4) “RAG doesn’t eliminate hallucinations.”

**Overlap:** **§B2** (bad PDF text). This adds **generation** risk.

**Honest answer:** Correct — retrieval reduces but does not eliminate hallucination. Mitigations: **citations required**, **refusal when retrieval is weak**, **tool-first escalation** for diagnostic territory, and **human verification** against the cited passage. Project docs use a **>0.7 similarity target** for multilingual retrieval QA — treat as an **evaluation goal**, not a safety certificate until measured on your corpus.

### F5) “Hindi/Marathi — tested with real ANMs? Dialects?”

**Honest answer:** Not claimed for the hackathon POC. Standard-register embeddings/models handle **mainstream** Hindi/Marathi; **dialect, code-mixing, and low-literacy phrasing** need field pilots and possibly curated examples. Gate‑style checks ≠ production linguistic validation.

### F6) “What if someone jailbreaks the model?”

**Overlap:** **§B3**, **§E6**. Add explicit **adversarial** framing.

**Honest answer:** Prompt tricks are a real class of failures. Defenses are layered: **tool routing + server-side policy**, **logging**, **no unsupervised prescribing/diagnosis**, **supervisory escalation**, and **district endpoint controls**. “Offline limits remote exploitation” helps narrow attack surface but is not sufficient alone.

### F7) “Gemma 4 E4B feels experimental — why not Gemma 2 / Llama?”

**Overlap:** **§8**, **§10**. Worth stating explicitly.

**Honest answer:** Submission/context may require Gemma 4; **architecture is model-swappable** (same refusal contract + RAG shell). E4B “thinking” can be disabled for latency; stability concerns are valid and answered by **evaluation harness + conservative boundary**, not by trusting the model brand.

### F8) “What’s the accuracy? Where are benchmark numbers?”

**Honest answer:** Report **what you measure**: e.g. Gate‑1 refusal behaviour on a fixed diagnostic prompt set; retrieval scores on a small multilingual query list. A **full accuracy claim** needs labeled datasets + blind review — not implied by a demo.

### F9) “ANMs are overworked — won’t this add burden?”

**Overlap:** **§B4**. Sharpen with **after-hours** and **familiar channel** points.

**Honest answer:** Adoption risk is real. The design intent is **fewer round-trips** (draft HMIS text, structured refusal instead of long chats) and **meeting users where they already are** (e.g. WhatsApp). Only a pilot measures time-on-task honestly.

### F10) “Guidelines change — how do you version the corpus and the boundary card?”

**Honest answer:** Operational answer is **re-ingest PDFs**, bump **corpus version**, keep **Decision Boundary Card semver/changelog** aligned with what the model is allowed to assert. Easier than full model retraining — still requires **district approval** for what counts as authoritative text.

### F11) “Why not train ANMs better instead of AI?”

**Overlap:** **§2** (expertise). Add the **not either/or** frame.

**Honest answer:** Training is necessary but not sufficient under **interruptions, fatigue, and uneven refresher access**. Decision support is complementary — like aviation checklists — not a substitute for competency programs.

### F12) “Incumbents: Wadhwani AI, ARMMAN, Noora Health, others?”

**Honest answer:** The maternal-health NGO ecosystem mixes **analytics, patient outreach (e.g. voice/IVR), and facility training**. Exact product boundaries shift over time — **verify current offerings** before naming them narrowly in a finalist deck. Honest differentiation remains: **ANM-facing desk assistant**, **local inference option**, **published refusal contract**, **closed-loop accountability artifact**.

### F13) “Total cost of ownership?”

**Overlap:** **§4**. Expand TCO honestly.

**Honest answer:** Hardware purchase is **one line item**. True TCO includes **power**, **spares**, **district IT time**, **training**, **connectivity**, **corpus maintenance**, and **incident response**. Compare TCO to **avoidable referrals, repeat visits, and supervisor time** only with pilot data — otherwise stay qualitative.

### F14) “Medico-legal liability — developers, district, ANM?”

**Overlap:** **§7**. Adds deployer angle.

**Honest answer:** Liability regimes vary. Practical stance for a writeup: system is **advisory**; authoritative sources are **cited guidelines**; human retains authority; deployers need **policies + audits**. Developers should avoid marketing language that implies **standalone diagnosis**.

### F15) “Why should judges favour this submission?”

**Overlap:** **§3**, **§D**, **§10**. One consolidated pitch.

**Honest answer:** Lead with **evaluable artefacts**: Decision Boundary Card + tool traces + (where working) citations + closed-loop lineage borrowed from AgriNexus. Pair with **explicit non-claims** (procurement, structural barriers, pilot-less accuracy). Judges can **test refusal behaviour** more easily than “vibes.”

---

## Appendix G — Glossary

Short definitions for acronyms and programme names used above. India-specific items are marked *(India)*.

| Term | Meaning |
|------|--------|
| **ABDM** | **Ayushman Bharat Digital Mission** *(India)* — national digital health ecosystem (identity, consent, health records exchange). |
| **ABHA** | **Ayushman Bharat Health Account** *(India)* — unique health ID within ABDM (formerly “health ID”). |
| **ANM** | **Auxiliary Nurse Midwife** *(India)* — nurse–midwife cadre often stationed at a sub-centre. |
| **ANMOL** | **ANM Online** *(India)* — NHM-linked mobile/app workflow for ANMs (name/programme scope may evolve). |
| **API** | **Application Programming Interface** — machine-accessible way for software to call a model or service (e.g. chat/completions API). |
| **ASHA** | **Accredited Social Health Activist** *(India)* — community-level health worker; often interfaces between households and the system. |
| **B2B / B2C** | **Business-to-business** vs **business-to-consumer** — here: clinic/workflow tools vs patient marketplace apps. |
| **CHW** | **Community health worker** — generic term; ASHA is one cadre in India. |
| **CDS** | **Clinical decision support** — systems that assist clinicians/staff with decisions (regulated differently by jurisdiction). |
| **CHIS** | **Community health information system** — digital workflows + records for CHWs (e.g. OpenSRP, CommCare-class tools). |
| **DHIS2** | **District Health Information Software 2** — open-source health information platform used in many countries for aggregation/reporting. |
| **E4B** | **~4 billion-parameter** Gemma 4–family build used in this project (vendor naming; often treated as **experimental/beta**). Optional “thinking” / extended reasoning paths, if present, are typically turned off for latency in demos. |
| **Gate‑1** | Project **acceptance check** for tool calling + refusal behaviour on fixed prompts (not a regulatory gate). |
| **HMIS** | **Health Management Information System** — routine reporting/indicators pipeline *(exact branding varies by state/NHM implementation)*. |
| **IFA** | **Iron and folic acid** — supplementation per national maternal health protocols. |
| **IVR** | **Interactive voice response** — phone menu/voice outreach (often low-literacy friendly). |
| **LLM** | **Large language model** — text (and sometimes tool) model powering answers. |
| **MO** | **Medical officer** — physician supervisor at PHC/block level in typical Indian public-health staffing. |
| **MoHFW** | **Ministry of Health and Family Welfare** *(India)* — publishes many national guidelines. |
| **MSP** | **Managed service provider** — vendor that operates IT for a district/state under contract. |
| **NHM** | **National Health Mission** *(India)* — umbrella for many public primary-health programmes and funding streams. |
| **NGO** | **Non-governmental organization** — common pilot partner for innovations before government scale. |
| **OCR** | **Optical character recognition** — turns scanned pages into text for indexing. |
| **PDF** | **Portable Document Format** — guideline documents ingested by the RAG pipeline. |
| **PHC** | **Primary health centre** — facility level above sub-centre in the Indian public-health tier. |
| **PHI** | **Protected health information** — identifiable health data (US HIPAA term; used here informally for “sensitive patient narratives”). |
| **POC** | **Proof of concept** — demonstration, not certified deployment. |
| **RAG** | **Retrieval-augmented generation** — fetch relevant document chunks, then generate an answer grounded on them. |
| **RCH** | **Reproductive and Child Health** *(India)* — programme/portal family tied to maternal–child tracking and reporting. |
| **SLA** | **Service level agreement** — agreed response time / ownership for escalations (placeholder in demos). |
| **SMS** | **Short message service** — text messaging channel alongside WhatsApp in places. |
| **semver** | **Semantic versioning** — version numbers like `1.2.3` with meaning for API/compatibility (used for config/corpus/boundary card discipline). |
| **TCO** | **Total cost of ownership** — hardware + power + ops + training + maintenance over time. |
| **WHO** | **World Health Organization** — international guidance PDFs used in the corpus. |

**Product / tech names (not acronyms but often unfamiliar):**

| Name | Notes |
|------|--------|
| **CommCare / Dimagi** | Mobile data collection and CHW workflow platform (structured forms, schedules). |
| **Gemma** | Google open-weight LLM family used locally in this project. |
| **Ollama** | Local runtime used to serve Gemma with an HTTP API for development/demo. |
| **OpenSRP** | Open-source CHIS-style platform for community health workflows. |
| **Sub-centre** | *(India)* smallest static facility in many states; ANM-led outreach to ~3k–5k population (order-of-magnitude). |

---

*Last updated: May 2026. Add new questions as they surface during the build and testing.*

