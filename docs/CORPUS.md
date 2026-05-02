# RAG corpus — source traceability

This file lists every PDF in `data/health-corpus/`: **local filename**, **canonical download URL** (or hub page where the file is selected), **purpose** in Sub‑Centre Mind, and **date checked** (URL reachable / file present).

**Date checked column:** `2026-05-02` means we verified the link or file that day. Programme sites move files—re-verify before a release demo.

---

## Core clinical & programme (original set)

| Local filename | Canonical URL / source hub | Purpose | Date checked |
|----------------|------------------------------|---------|----------------|
| `WHO-IFA-pregnant-women-2012.pdf` | [WHO IRIS — Daily iron and folic acid supplementation in pregnant women](https://iris.who.int/handle/10665/77712) (PDF linked from record) | IFA policy text; refusal/escalation anchors for supplementation vs prescribing | 2026-05-02 |
| `WHO-Calcium-Supplementation.pdf` | [WHO IRIS — Calcium supplementation in pregnant women](https://apps.who.int/iris/) (search title; programme publishes multiple years) | Calcium vs IFA disambiguation; nutrition pillar | 2026-05-02 |
| `MCP-Guide-Book-2018.pdf` | [NHM — Manuals / registers](https://nhm.gov.in/index1.php?lang=1&level=2&lid=648&sublinkid=1498) / MCP programme documents on NHM | Integrated MCP operational content (ANC, counselling, reporting cross-refs) | 2026-05-02 |
| `HBNC-Operational-Guidelines.pdf` | NHM / Child Health programme publications (search **HBNC** on [nhm.gov.in](https://nhm.gov.in)) | Newborn & postnatal home-visit protocols | 2026-05-02 |
| `AMB-Operational-Guidelines.pdf` | MoHFW / NHM safe abortion & allied operational guidance (search **AMB** / Medical Boards on [mohfw.gov.in](https://www.mohfw.gov.in)) | High-risk pregnancy / abortion-board pathway context | 2026-05-02 |
| `PMSMA-Extended-HRP-Guidance.pdf` | NHM **PMSMA** programme materials ([programme index](https://pmsma.nhp.gov.in/) or NHM maternal-health listings) | High-risk pregnancy extended guidance | 2026-05-02 |

> **Note:** For rows marked with a hub rather than a direct PDF, the exact landing PDF may change; keep the filename in git and update this table if you replace the file.

---

## Added for “accountable infrastructure” (admin + referral + immunization)

| Local filename | Canonical URL | Purpose | Date checked |
|----------------|-----------------|----------|----------------|
| `NHM-National-Immunization-Schedule.pdf` | `https://nhm.gov.in/New_Updates_2018/NHM_Components/Immunization/report/National_%20Immunization_Schedule.pdf` | National Immunization Schedule (UIP)—immunization sessions, vaccine follow-up / nudge lineage | 2026-05-02 |
| `NHSRC-Skills-Lab-RMNCH-A-Training-Manual-2013.pdf` | `https://nhsrcindia.org/sites/default/files/2021-06/4.Skills%20Lab%20Training%20Manual%20Nov%202013.pdf` | Skills Lab — procedures + referral-style escalation language for Decision Boundary Card testing | 2026-05-02 |
| `RCH-Portal-Data-Entry-Manual-2018.pdf` | `https://nhmmizoram.org/upload/RCH%20Portal%20Data%20Entry%20Manual.pdf` | **State-hosted mirror** of RCH portal data-entry walkthrough (screens/fields). Use until you pin an NIC/MoHFW PDF for your state/release. See also [RCH portal — About](https://rch.mohfw.gov.in/RCH/about-rch.aspx) for annexures. | 2026-05-02 |
| `NHM-SBA-Guidelines-ANC-Skilled-Attendance-ANM-2010.pdf` | `https://nhm.gov.in/images/pdf/programmes/maternal-health/guidelines/sba_guidelines_for_skilled_attendance_at_birth.pdf` | MoHFW-line **SBA** guidelines for ANM/LHV/SN—ANC, complications, **referral / escalation** language (pairs with Skills Lab; overlaps MCP/HBNC but citation-grade for judges) | 2026-05-02 |
| `WHO-India-CMYP-2013-2017.pdf` | `https://extranet.who.int/countryplanningcycles/sites/default/files/planning_cycle_repository/india/india_cmyp_2013-17.pdf` | India **Comprehensive Multi-Year Plan (CMYP) 2013–17** via WHO country planning cycles—national immunization **strategy / programme narrative** (2013–17 period). **Not** the same as MoHFW `Universal.pdf`; complements `NHM-National-Immunization-Schedule.pdf` (schedule) with planning-level language. | 2026-05-02 |

---

## MoHFW `Universal.pdf` (UIP compendium) — not in corpus

| Canonical URL | Status | Mitigation in repo |
|-----------------|--------|----------------------|
| `https://www.mohfw.gov.in/sites/default/files/Universal.pdf` | **HTTP 404** (verified `www` and non-`www`, 2026-05-02). Older citations still point here; file appears withdrawn or relocated. | Use `NHM-National-Immunization-Schedule.pdf` for schedule tables; use [MoHFW — UIP programme page](https://www.mohfw.gov.in/?q=en%2FMajor-Programmes%2Funiversal-immunization-programme-uip) (“Detailed PDF” link when MoHFW restores it). Manually add `MoHFW-UIP-Universal-Immunization-Programme.pdf` under `data/health-corpus/` when you obtain a current PDF from the Immunization division. **`WHO-India-CMYP-2013-2017.pdf`** is a **different** official artefact (WHO CMYP), not a drop-in replacement for `Universal.pdf`. |

---

## Rebuild index after any PDF change

From repo root (with venv active):

```bash
python src/rag/ingest.py
```

---

## Corpus size note

The corpus is now **11 PDFs** (including CMYP). Keeping **~8–12 high-impact PDFs** balances retrieval quality and local **embedding + Gemma** latency; larger corpora increase embedding time. The **SBA** PDF is large (~15 MB on disk); after additions, re-measure `ingest` batch count and Gate‑1 latency on target hardware.
