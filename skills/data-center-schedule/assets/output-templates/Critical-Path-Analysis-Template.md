# [Project] Critical Path Analysis — v[N]

**Data Date:** [YYYY-MM-DD]
**Schedule version:** v[N]

---

## How to read this

For each contractual milestone, trace backward through the longest chain of activities. Each activity in the chain is "critical" (zero / near-zero total float). Look for:
- **Long-duration activities** — candidates for compression
- **Long lags** between activities — candidates for sequencing review
- **Activities tied to procurement** — candidates for expedited delivery
- **Activities with assumption flags** — candidates for clarification

---

## DH4 EFA — Forecast [date]

**Total chain duration:** [N working days from data date]

| Step | Activity | Duration | Float | Trade | Notes |
|---|---|---|---|---|---|
| 1 | [activity code + name] | [Nh] | 0d | [trade] | [why critical] |
| 2 | [activity code + name] | [Nh] | 0d | [trade] | |
| ... | | | | | |
| N | MS-EFA-DH4 | TT_FinMile | 0d | — | Contract: [date] |

**Top compression candidates:**
1. [Activity] — [hours saveable, how]
2. ...

**Top risks on this chain:**
1. [Activity] — [risk and impact]
2. ...

---

## DH4 FA — Forecast [date]

[same format]

---

## DH3 EFA — Forecast [date]

[same format]

---

## DH3 FA — Forecast [date]

[same format]

---

## DH2 EFA — Forecast [date]

[same format]

---

## DH2 FA — Forecast [date]

[same format]

---

## DH1 EFA — Forecast [date]

[same format]

---

## DH1 FA — Forecast [date]

[same format]

---

## PCO — Forecast [date]

[same format]

---

## Critical Path Across All DHs — Common Drivers

Activities that appear on 2+ DH critical paths (these are the highest-leverage compression targets):

| Activity | DHs affected | Total impact |
|---|---|---|
| [activity] | [DH4, DH3, DH2, DH1] | [days saveable across all] |
| ... | | |

---

## Float Distribution

| Float bucket | Activity count |
|---|---|
| 0 days (critical) | [n] |
| 1-5 days | [n] |
| 6-20 days | [n] |
| 21-60 days | [n] |
| > 60 days | [n] |

---

## Compression Options (if at-risk)

For each at-risk milestone:

### Option A — Trade compression
- Activity / scope: [what gets compressed]
- Hours saved: [N]
- Cost: [labor uplift / overtime estimate]
- Risk: [quality / safety / staffing concerns]

### Option B — Sequencing change
- Logic change: [what tie changes]
- Days saved: [N]
- Risk: [what breaks if this doesn't hold]

### Option C — Scope change
- Scope removed / deferred: [what]
- Days saved: [N]
- Owner approval needed: [yes/no]

### Option D — Procurement expedite
- Equipment: [what]
- Lead time savings: [weeks]
- Cost: [premium]

---

## How to use this on a new project

1. **Phase 4-5:** Generate per-DH critical path after each major build version.
2. **Phase 6:** Validate critical path against trade expectations (do they agree these are the drivers?)
3. **Phase 7:** Deliver final critical path analysis as part of PM briefing.
4. **Mid-project:** Re-run after each schedule update; track movement of critical path activities.
