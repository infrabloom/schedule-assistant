# [Project] Schedule v[N] — PM Briefing

**Data Date:** [YYYY-MM-DD]
**Schedule version:** v[N.x]
**Author:** [Name]

---

## 1. Executive Summary

[1-2 paragraphs: where the schedule lands vs. contractual milestones, top 3 risks, top 3 mitigations]

**Headline dates:**

| Milestone | Contractual | v[N] Forecast | Variance | Status |
|---|---|---|---|---|
| DH4 EFA | [date] | [date] | [+/-N days] | 🟩/🟧/🟥 |
| DH4 FA | [date] | [date] | [+/-N days] | 🟩/🟧/🟥 |
| DH3 EFA | [date] | [date] | [+/-N days] | 🟩/🟧/🟥 |
| ... | | | | |
| PCO | [date] | [date] | [+/-N days] | 🟩/🟧/🟥 |

🟩 On / ahead of contract | 🟧 At risk (within 14 days) | 🟥 Forecasted past contract

---

## 2. Schedule Stats

- **Total activities:** [count]
- **Total ties:** [count]
- **Orphans:** [should be 0]
- **Duplicates:** [should be 0]
- **Activities with actuals:** [count of TK_Active + TK_Complete]
- **OPC import status:** [✅ Passes / ⚠️ Issues]

---

## 3. Source Documents

| Source | Date | Status | Notes |
|---|---|---|---|
| Build Sequence PDF | [date] | Authoritative | [version / rev] |
| Client high-level schedule | [date] | Reference | [version] |
| Mech contractor schedule | [date] | Ingested | [version] |
| Mech commissioning schedule | [date] | Ingested | [version] |
| Electrical contractor schedule | [date] | Ingested | [version] |
| MEL spreadsheet | [date] | Ingested | [version] |
| Prior GC schedule | [date] | Actuals only (logic NOT trusted) | [version] |

---

## 4. Logic Principles Applied

[Describe the major logic decisions that shape the schedule. Examples:]

- **L3 commissioning on test power** (Interpretation B) — L3-CDU and L3-CHW can run before L3-LV-EN
- **Procurement → install FF tie** for long-lead equipment, FS for commodity
- **3-week-per-area stagger** per Build Sequence PDF
- **EFA gated by:** L3-CDU + L3-CHW + Containment Verify + FOD Walks + DH Electrical QA/QC
- **FA gated by:** EFA + Rack Install (160h = 4 weeks per FluidStack)
- **PCO gated by:** FA + L5 Load Bank IST + B-Feed live

---

## 5. Critical Path Summary

**Per-DH critical path drivers:**

| DH | Critical path | Driver activity |
|---|---|---|
| DH4 EFA | [trace] | [activity + reason] |
| DH4 FA | [trace] | [activity + reason] |
| DH3 EFA | [trace] | [activity + reason] |
| ... | | |

---

## 6. Top Risks

🟥 **R1** — [Risk description]. Impact: [days / scope]. Mitigation: [action]. Owner: [name].
🟥 **R2** — ...
🟧 **R3** — ...

---

## 7. Open Items (top 5)

See `Open-Items-By-Discipline.md` for full list.

1. **[Item]** — Owner: [name]. Needed by: [date]. Blocks: [activity].
2. ...

---

## 8. Assumptions (top 5)

See `Assumptions-Register.md` for full list.

1. **A1** — [Assumption]. Source: [trade verbal / template default]. Impact if wrong: [days].
2. ...

---

## 9. Deviations from Prior Version (v[N-1] → v[N])

| Change | Reason | Impact |
|---|---|---|
| [Logic change] | [why] | [days, milestones affected] |
| [Duration change] | [why] | [days, milestones affected] |
| ... | | |

---

## 10. Recommended Next Steps

1. [Action] — Owner: [name]. Date: [target].
2. ...

---

## 11. Talking Points for Stakeholders

- **Owner:** [key message]
- **GC PM:** [key message]
- **Mech Trade:** [key message]
- **Electrical Trade:** [key message]
- **CxA:** [key message]
- **FluidStack / IT vendor:** [key message]

---

## Appendix A — Activity Count by WBS

| L1 WBS | Activity count |
|---|---|
| 01 Milestones | [n] |
| 02 Procurement | [n] |
| 03 Site & Shell | [n] |
| 04 Construction | [n] |
| 05 Final Inspections | [n] |
| 06 Commissioning | [n] |
| 07 Closeout | [n] |

## Appendix B — Trade Responsibility (high-level)

[Brief recap of who owns what — see the Trade Responsibility Map for the full map]
