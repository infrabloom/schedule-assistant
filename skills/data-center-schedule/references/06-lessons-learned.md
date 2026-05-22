# Lessons Learned — the reference project

Concrete pitfalls from building the reference project schedule v1 → v4.15. Read this **before** you start a new DC schedule. Each item is a real failure mode that cost cycles on the reference project — avoid them next time.

---

## 1. OPC Constraint Codes — `CS_MEO` Fails Silently

**What happened on the reference project:**
We initially used `CS_MEO` (Mandatory Finish On) for the AFEED / BFEED milestones and several Test & Commissioning activities. When the XER imported into Oracle Primavera Cloud, those milestones **disappeared from the schedule** without an error message. Diagnosed by parsing import log: OPC rejects the `CS_MEO` code but still imports the rest of the file.

**Fix:**
Use `CS_MEOA` (Finish On or After) as a drop-in replacement. It works in OPC and behaves as a contractual floor. For ceilings, use `CS_MEOB` (Finish On or Before — FNL).

**Working constraint codes in OPC:**
- `CS_MEOA` — Finish On or After (floor)
- `CS_MEOB` — Finish On or Before (FNL ceiling)
- `CS_MSOA` — Start On or After (SNE)

**Codes to AVOID in OPC:**
- `CS_MEO` — Mandatory Finish On (silently dropped)
- `CS_MSO` — Mandatory Start On (also reported as flaky)

**Rule:** Run a post-build grep on the XER for `CS_MEO\t` and `CS_MSO\t` (note the tab — to avoid matching `CS_MEOA`/`CS_MEOB`/`CS_MSOA`). Zero hits is the target.

---

## 2. `TK_Active` Without `act_start_date` → PRM-009010001

**What happened on the reference project:**
Fan Wall procurement activities were marked `TK_Active` (in-progress per procurement team) but had no `act_start_date` populated. On OPC schedule run, we got `PRM-009010001 — Unable to complete scheduling`. The error referenced no specific activity, so diagnosis was painful.

**Fix:**
**Every** `TK_Active` task must have `act_start_date` populated. **Every** `TK_Complete` task must have **both** `act_start_date` and `act_end_date`. **Every** `TK_NotStart` task must have **neither**.

**Validation step (mandatory before delivering an XER):**
```python
for task in tasks:
    if task.status == 'TK_Active' and not task.act_start_date:
        fail(task)
    if task.status == 'TK_Complete' and not task.act_end_date:
        fail(task)
    if task.status == 'TK_NotStart' and (task.act_start_date or task.act_end_date):
        fail(task)
```

---

## 3. `phys_complete_pct=100` Must Match `remain_drtn_hr_cnt=0`

**What happened on the reference project:**
Several activities were marked 100% complete in one field but still had remaining duration > 0 in another. OPC accepted the import but reported the activities as "in progress" on the schedule, throwing off forecasted dates.

**Fix:**
If `phys_complete_pct=100`, then `remain_drtn_hr_cnt` MUST equal 0, `act_end_date` MUST be populated, and `status_code` MUST equal `TK_Complete`. Enforce this as a single consistent state.

---

## 4. Duplicate Activities From Legacy Schedules

**What happened on the reference project:**
The prior GC schedule had STS procurement appearing twice — once site-wide (`PROC-LL-STS`) and once per DH (`PROC-DH{n}-ELEC-1010`). Carried forward into v4.13 it inflated the procurement WBS and double-counted scope. Same pattern: `MR-2040` Fill/Flush and `MR-5020` Fill & Flush were duplicates of the same scope.

**Fix:**
Before merging a legacy schedule:
1. **Group activities by scope keyword** (STS, Fill, Flush, Test, Energize, CDU, Fan Wall) and look for repeats within the same WBS scope.
2. **Compare descriptions side-by-side.** If two activities describe the same physical work, retire one.
3. **Retire pattern:** delete the duplicate task, re-tie its successors to the survivor, document the retirement in a build-script comment.
4. **Cohesion check:** after retirement, verify no orphans (every activity still has ≥1 pred AND ≥1 succ).

---

## 5. "Flush & Fill" vs "Fill & Flush" — Terminology Matters

**What happened on the reference project:**
We had both `MR-2040 Fill/Flush` and `MR-5020 Fill & Flush`. Beyond being duplicates, the **name was wrong**. The convention in mechanical commissioning is: **FLUSH first, then FILL** with treated/inhibited fluid. The mechanical contractor confirmed.

**Fix:**
Use "Flush & Fill" consistently. Run a regex sweep on activity descriptions for `Fill.*Flush` and rename to `Flush.*Fill`.

---

## 6. Template-Default Durations vs Trade-Reported Labor Durations

**What happened on the reference project:**
P6 template defaults gave us 40h for L3-MV-EN, 200h for DH Branch Power install. The electrical contractor's detailed mpp showed 420h and 600-1000h for the equivalent scope. The schedule based on template defaults under-stated the critical path by **weeks**.

**Fix:**
- **NEVER** use template defaults blindly. They reflect generic commissioning windows, not actual trade labor.
- Cross-check **every** duration > 40h against the trade contractor schedule.
- If trade durations are 3-10× higher, **ask the trade lead which one is right**. Often the trade duration is full-scope (every relay, every cable) while the template is "happy path."
- Document the chosen duration with a citation: "L3-MV-EN 40h — CxA standard per VA-DC template; the electrical contractor reports 420h (commissioning of MV switchgear) — held at 40h pending CxA confirmation that scope is single-switchgear test only."

---

## 7. Test/Temp Power vs Production Power for L3 Commissioning

**What happened on the reference project:**
The schedule had two interpretations of when L3-CDU and L3-CHW could start:
- **Interpretation A:** L3 requires production utility power (L3-LV-EN complete first).
- **Interpretation B:** L3 can run on test/back-fed power, independent of L3-LV-EN.

Picking B compressed DH4 EFA by ~3 weeks (Sep 14 → Aug 11). Picking A pushed it back. **The answer is contract-specific** — depends on what the client / the owner will accept as "L3 complete."

**Fix:**
Make this a **Phase 3 decision item.** Ask CxA / the electrical contractor / CDU vendor directly. Document the interpretation and flag the date impact of the alternative. Track as an open item until resolved.

---

## 8. EFA / FA / PCO Definitions Are NOT Universal

**What happened on the reference project:**
Three different people had three different definitions of "FA":
- Contract reads: "All racks installed and energized."
- The client PM said: "All racks physically installed (cabling can lag)."
- GC PM said: "All racks installed AND data hall electrical QA/QC complete."

Each definition implies a different scope of activities to gate FA.

**Fix:**
Phase 3 deliverable should include explicit **definitions of every contractual milestone** (EFA, FA, MEC, TCO, PCO). Get them in writing. If the contract is ambiguous, document the working interpretation and flag in the assumptions register.

---

## 9. East / West Mains vs A-Feed / B-Feed

**What happened on the reference project:**
The site has East Mains and West Mains (utility tie-ins). It also has A-Feed and B-Feed (redundant power sources for 2N). These are **not the same** — Mains are physical utility connections, Feeds are logical redundant paths to the load.

The prior schedule conflated them. Activities tied to "A-Feed energization" actually meant "East Mains live," which back-feeds the site but doesn't necessarily mean production-grade redundant power.

**Fix:**
- Maintain a **clear distinction** between Mains (physical) and Feeds (logical).
- Confirm the **back-feed status** of each Mains energization. Back-fed power may be sufficient for hydros / pump startups but NOT for full L3 commissioning.
- Reference dates: East Mains 2/16/26 (back-fed), A-Feed 6/22/26 (production-ready), B-Feed 12/15/26 (full 2N).

---

## 10. Forward-Chain to Contract Milestone (No-Orphans Rule)

**What happened on the reference project:**
After retiring duplicate activities, several tail-orphans appeared (activities with successors that no longer existed). They had no impact on the visible schedule but caused noise in OPC. Worse: some activities had successors that led to a dead-end activity, not to a contract milestone.

**Fix:**
**Every** activity must satisfy ALL THREE:
1. ≥1 predecessor (logical or data-date for actuals)
2. ≥1 successor
3. **Forward chain reaches a contract milestone** (EFA, FA, TCO, MEC, PCO, or Project Completion)

Build a validation script that walks forward from every activity and confirms the chain terminates at a milestone. Activities that don't reach a milestone aren't really "in" the schedule.

---

## 11. GUID Format for OPC

**What happened on the reference project:**
Early XERs had simple GUIDs like `GUID-001` for testing. OPC rejected the import with cryptic format errors.

**Fix:**
Use base64-encoded UUID format. Pattern:
```python
import base64, uuid
def make_guid():
    return base64.b64encode(uuid.uuid4().bytes).decode('ascii').rstrip('=')
```
Example: `Zh9XCgQH7E2DcMYsZJqkUg`

---

## 12. `aref` and `arls` on TASKPRED Rows

**What happened on the reference project:**
TASKPRED rows had `aref` and `arls` left blank or set to a generic date. OPC import worked but the predecessor lags didn't apply correctly on schedule.

**Fix:**
On every TASKPRED row, set both `aref` and `arls` to **the data date** of the project. They control how lags are calculated relative to actuals.

---

## 13. Trade Responsibility Confusion — CDU and Fan Wall Are NOT Mech Contractor Scope

**What happened on the reference project:**
The schedule originally had the mech contractor installing CDUs. Patrick flagged: **CDUs are installed by a separate vendor (Schneider / Vertiv)**, not the mechanical contractor. Same for Fan Walls — the cooling-commissioning contractor procures, but installer is a separate vendor (TBD on the reference project).

**Fix:**
Build a **Trade Responsibility Map** (see `03-trade-responsibility-map.md`) at the start of every project. For every activity, name the responsible trade. Validate with the GC PM. CDU and Fan Wall are common landmines.

---

## 14. Procurement-to-Install Tie Convention — FF vs FS

**What happened on the reference project:**
The first draft used FS (finish-to-start) ties from procurement to install: "STS procurement finishes → STS install starts." This forced install activities to wait for 100% procurement completion, which inflated the schedule because procurement is rarely a single point-in-time event.

**Fix:**
- For **long-lead equipment** (MV switchgear, transformers, STS, UPS, chillers, CDUs, Fan Walls): use **FF (finish-to-finish)** with appropriate lag. Procurement is mostly done before install finishes, but install can start with partial deliveries.
- For **short-lead / commodity items** (cabling, fittings, instrumentation): FS is fine.
- Document the convention in the assumptions register.

---

## 15. Stagger Pattern — 3 Weeks Per Area

**What happened on the reference project:**
The Build Sequence PDF specifies 4 crews flowing through 4 areas with a 3-week per-area stagger. The first draft schedule didn't reflect this, instead showing all 4 DHs starting on the same day (impossible — same crew, same equipment).

**Fix:**
- Apply per-DH offsets in the activity start dates: DH4 = baseline, DH3 = baseline + 3 weeks, DH2 = baseline + 6 weeks, DH1 = baseline + 9 weeks (the reference project's reverse-N-to-S order).
- Validate stagger against the Build Sequence PDF on every revision.
- Surface conflicts: if a contractual EFA / FA is tighter than the stagger allows, **flag immediately** — don't silently compress.

---

## 16. Procurement WBS Should Use the MEL Keyplan, Not Construction Areas

**What happened on the reference project:**
MEL spreadsheet uses keyplan zones A-R for equipment locations. Construction WBS uses Areas 1-4 (north-to-south). Initial draft tried to force MEL into construction Areas — broke the procurement WBS.

**Fix:**
- Keep **construction WBS** by Area (1-4) + room (DH / MR / Yard / Roof).
- Keep **procurement WBS** by MEL zone (A-R), then cross-reference.
- Build a **zone-to-Area cross-reference table** as a Phase 3 deliverable. Document any ambiguous zones.

---

## 17. Don't Trust the Prior GC Schedule's Logic

**What happened on the reference project:**
The prior GC scheduler was let go 2 months before this rebuild. The mech trade lead reported the schedule had duplicate activities and broken predecessor logic. We confirmed both.

**Fix:**
- **Extract actuals** from the prior GC schedule (status / dates as of the data date) — these are usually reliable.
- **Do NOT carry forward logic** from the prior GC schedule without verifying every tie.
- **Audit duplicates** before merging anything.
- Document everything in the Phase 2 extraction report.

---

## 18. Project-Specific Pitfalls (Not Portable, But Worth Noting)

These were reference project mistakes that may not apply to a new project, but capture the pattern:

- **AFEED/BFEED milestones constrained to `CS_MEO`** disappeared on import — see #1.
- **STS shown as both site-wide and per-DH** — see #4.
- **MR-2040 Fill/Flush vs MR-5020 Fill & Flush** duplication — see #4.
- **Rack install set to 0h** initially — caused EFA and FA to land on the same date (impossible — the client needs ~4 weeks to install racks after EFA). Set to 160h.
- **L3-CHW description "Flush, Fill, Water Quality"** misleading — the Flush & Fill is owned by MR-5020 (the cooling-commissioning contractor). L3-CHW is the functional test + water quality verification. **Rename in next version.**
- **Fan Wall installer unspecified** — the cooling-commissioning contractor procures but doesn't install. Open item.

---

## How to use this file on a new project

1. **Read it before Phase 1.** Don't repeat these mistakes.
2. **Reference it during Phase 4 and Phase 6.** Most pitfalls show up during build and QA.
3. **Add new lessons.** When you hit a new failure mode, log it as a candidate in the project's `lessons-log.md` — the Phase 3/4/6 [CAPTURE] steps and the Phase 7 retrospective do this. It is reviewed via the schedule-assistant plugin's `/harvest-lessons` and, once approved, promoted into this file per `MAINTENANCE.md`.
4. **Validate every XER before delivery** against the OPC-specific issues (#1, #2, #3, #11, #12).

---

## Validation checklist (copy this to every project)

Before delivering any XER, run **`scripts/validate_xer.py`** (the single
consolidated validator -- 21 FAIL checks + 7 WARN checks) and
**`scripts/cohesion_audit.py`** (detailed orphan / dead-end report). Both must
exit 0. What they cover:

**OPC-schema (FAIL):** no bare CS_MEO / CS_MSO; status/actuals consistent;
pct/remain/status consistent; task_codes unique exact AND case-insensitive;
GUIDs unique and 22-char standard base64; duration_type matches task_type;
no midnight (00:00) timestamps; proj_id matches a PROJECT row; valid wbs_id;
valid calendar; WBS depth <= 10.

**Logic-integrity (FAIL):** no orphans (every activity has a predecessor and a
successor); every forward chain reaches a milestone; no dangling TASKPRED
references; aref/arls populated; predecessor types PR_FS/PR_SS/PR_FF only;
no cycles; WBS hierarchy intact.

**Review (WARN):** odd constraint codes; floating contract milestones;
activities riding a project-start milestone; PR_SF ties; multi-project XER.

Then, outside the scripts: OPC import test passes (no PRM-009010001); schedule
dates spot-checked (5-10 activities); critical-path activities documented in the
narrative.

If `validate_xer.py` and `cohesion_audit.py` both exit 0: ship it.

---

# Reference Project v2/v3 Rebuild Lessons (added 2026-05-17)

These lessons were captured during the v2.0 -> v3.0 rebuild and weekly refresh shakedown. Each one cost cycles to find; document and avoid them on the next project.

---

## 19. OPC Case-Insensitive Task Code Uniqueness

**What happened on the reference project v2.0:**
The build had `CONS-DH4-MR-1010` and `CONS-DH4-mr-1010` (different case) for two distinct activities. OPC silently merged them on import, dropping 91 procurement tasks. Took 12 staged test XERs (Test 4 through Test 12) and a binary search to isolate.

**Fix:**
- Build a case-insensitive uniqueness check into the build script
- Same check in the validator (`validate_xer.py` check 7)
- Convention: choose one case (uppercase for codes, lowercase for variable names) and stick with it

**Validation:**
```python
codes_lower = collections.Counter(t['task_code'].lower() for t in tasks)
dupes = [c for c, n in codes_lower.items() if n > 1]
assert not dupes, f"Case-insensitive task_code collisions: {dupes}"
```

---

## 20. MS-Project Duration Basis -- Derive the Conversion Factor, Don't Hardcode /3

**What happened on the reference project:**
The electrical contractor's MS-Project XML exports use `MinutesPerDay=1440` (24h/day basis) while their
schedule is logically 8h/day. `PT1005H` in their XML really means 1005/3 = 335
hours = ~42 days on an 8h-day calendar. Importing the raw durations inflated
installs 3x and crashed the schedule into the milestone dates. We fixed it with
a /3 -- but **/3 is specific to the electrical contractor's 1440-minute basis; it is NOT universal.**

**The general rule:**
An MSP `<Duration>` in PT-hours equals (displayed days) x (MinutesPerDay / 60).
To convert to an 8h/day work-hour basis:

    factor = 8 / (MinutesPerDay / 60)

  - MinutesPerDay = 1440 (24h)  -> factor 1/3   (the electrical contractor's case -- the "/3")
  - MinutesPerDay = 480  (8h)   -> factor 1     (the mechanical contractor's case -- no conversion)
  - MinutesPerDay = 600  (10h)  -> factor 0.8

**Fix:**
- Read `<MinutesPerDay>` from each trade file's header and compute the factor.
  Never hardcode /3.
- Better: run `scripts/analyze_msp.py` -- it derives the true basis empirically
  from the file's completed activities (working-hours between ActualStart and
  ActualFinish == ActualDuration reveals the real calendar model), so you
  confirm the factor instead of trusting the header.
- Flag any trade-sourced duration of <1 day or >100 days as suspicious
  (factor forgotten, or applied twice).

**Validation:**
- Run `analyze_msp.py` on every new trade file before trusting its durations.
- Cross-check 10 durations against the trade engineer's stated days-to-complete

---

## 21. Mechanical Contractor Calendar — No Conversion Needed

**What happened on the reference project:**
We initially assumed the mechanical contractor also needed /3 conversion. It doesn't — the mechanical contractor's XML uses `MinutesPerDay=480` (8h/day) natively. Don't apply /3 to the mechanical contractor's durations.

**Fix:**
- Check `<MinutesPerDay>` in each XML and apply /3 only if 1440. Don't hardcode the conversion to the electrical contractor's source.

---

## 22. Many-to-One Aggregation — Build the Crosswalk

**What happened on the reference project:**
The electrical contractor has fine-grained per-area sub-activities (e.g., "Install Cable Tray" appears 16 times across the 4 DH files, plus UPS-East, UPS-West, MECH room, DH proper, sub-rows for Areas A-H). The v3 high-level schedule has one aggregate `MR-1105` per DH covering all of those.

Without an explicit crosswalk, the electrical contractor refresh produces garbage. We tried auto-matching by name and got <5% high-confidence rate, plus false positives (83 UPS-corridor activities mapped to ADMIN-MEP).

**Fix:**
- Build the trade-leaf -> v3-aggregate crosswalk catalog as a Phase 3 deliverable
- One row per v3 task: `v3_code | v3_name | trade_file | trade_section_path | trade_leaf_names | aggregation_rule`
- Aggregation rules: `earliest_AS`, `latest_AF`, `weighted_pct`, `sum_remain_drtn`, etc.
- Once built, every weekly refresh is mechanical

**Validation:**
- Spot-check 10 crosswalk rows by hand-aggregating in Excel and comparing to script output

---

## 23. GUIDs Must Use Standard Base64 — NOT urlsafe

**What happened on the reference project v3.0:**
Initial build used `base64.urlsafe_b64encode(uuid.uuid4().bytes)`, which produces GUIDs with `-` and `_`. OPC rejected the XER with a cryptic format error. The reference project v1.0 lesson #11 said "use base64-encoded UUID" but didn't specify standard vs urlsafe.

**Fix:**
- Use `base64.b64encode`, not `base64.urlsafe_b64encode`
- If you must convert an existing urlsafe GUID, replace `-` -> `+` and `_` -> `/`
- Validator check 8: reject any GUID containing `-` or `_`

```python
import base64, uuid
def make_guid():
    return base64.b64encode(uuid.uuid4().bytes).decode('ascii').rstrip('=')
```

---

## 24. No Midnight Times in Date Fields

**What happened on the reference project v2.0:**
Some early XER rows had `2026-06-15 00:00` in start/finish dates. OPC silently dropped those rows. Switched to `08:00` / `17:00` and they imported.

**Fix:**
- Standard: `08:00` for start, `17:00` for finish on 8h-day calendar
- Validator check 9b: regex `\t\d{4}-\d{2}-\d{2}\s+00:00` matches zero times

---

## 25. Retie Residue — Cycles Appear After Every Retie

**What happened on the reference project v3.0:**
During the F&F retie operation (replacing 16 individual `*-1050 -> *-1000` ties with a single SS+lag overlap), 8 spurious back-edges remained from earlier iterations. Validator's Tarjan SCC caught them. Dropped 8 ties, cycles cleared.

**Fix:**
- Re-run cycle detection (Tarjan SCC) after EVERY retie operation
- The Validator should fail-loud on any SCC of size >1
- The Retie operation in the XER Builder should generate a list of "edges removed" and "edges added", and the Validator should verify no SCC was created

**Validation:**
```python
from collections import defaultdict
def find_sccs(taskpred):
    # Tarjan's algorithm
    ...
assert all(len(scc) == 1 for scc in find_sccs(taskpred)), "Cycles detected"
```

---

## 26. Cross-DH FS Crew Chains Anti-Pattern

**What happened on the reference project v3.0:**
The first replication of DH4 -> DH3/2/1 used FS pred chains for crew flow: `CONS-DH4-MR-1010 -> CONS-DH3-MR-1010 -> CONS-DH2-MR-1010 -> CONS-DH1-MR-1010`. This forced serial execution of all 4 DHs by a single crew. But on the reference project, multiple crews work in parallel — so DH3 install can start independent of DH4 install, just 21 days later per the stagger.

These chains inflated DH1 EFA by ~9 weeks vs reality. We dropped 285 cross-DH FS chains in one cleanup pass.

**Fix:**
- Use **date-offset stagger** (per-DH start_date += 21 days), NOT cross-DH pred chains
- The XER Builder should refuse to create FS ties between activities in different DH WBSes (warn loudly)
- The Logic Auditor should flag every existing cross-DH FS tie for user review

---

## 27. Forgotten DH Symmetry Check

**What happened on the reference project v3.0:**
After Patrick flagged that DH4 EFA had 5 procurement preds but DH3/2/1 EFA had 12, we audited. DH3/2/1 had 12 cross-DH PROC preds (from the contract pattern of "DH3 EFA requires DH4 PROC complete") that were wrong — the contract says each DH's EFA requires its OWN procurement, not other DHs'. Dropped 33 spurious preds and added 12 missing per-DH PROC preds.

**Fix:**
- After replicating DH4 -> DH3/2/1, run a "predecessor symmetry check": for each milestone, the *type* and *count* of preds should be the same across DHs (with the only differences being the DH index in the pred code)
- Flag any deviation for user review

**Validation:**
```python
for milestone_type in ['EFA', 'FA', 'FR', 'RFS']:
    preds_per_dh = {dh: get_preds(f'MS-DH{dh}-{milestone_type}') for dh in [1,2,3,4]}
    pred_patterns = {dh: sorted(strip_dh(p) for p in preds) for dh, preds in preds_per_dh.items()}
    assert len(set(map(tuple, pred_patterns.values()))) == 1, f"{milestone_type} preds differ across DHs"
```

---

## 28. Parallel Trades — HAC and MDB Are Not Sequential

**What happened on the reference project:**
The first draft had `HAC-Install -> MDB-Gallery-Install` (FF). Patrick: "HAC and MDB are parallel trades; HAC doesn't need to be done before MDB." Dropped 8 ties; MDB now has its own preds (steel, electrical room rough-in).

**Fix:**
- Don't assume sequential just because activities sound related
- Confirm parallel-vs-sequential with the trade leads in Phase 1
- General rule: if two trades have different crews on different fronts, default to parallel unless proven otherwise

---

## 29. EFA = Temporary Power, Not Permanent

**What happened on the reference project:**
First draft tied `MS-SS-1020` (permanent power milestone) -> `MS-DH4-EFA`. Patrick: "Aren't we using temporary power for that?" Dropped tie. Per the reference project v2.1 definitions: EFA = first access on temp power, FA = full permanent power. They have different power preds.

**Fix:**
- Lock the EFA / FA / FR / RFS definitions in Phase 1 (see lesson #8)
- For each milestone, document explicitly which power source is required
- The Logic Auditor should flag any EFA -> permanent-power-milestone tie

---

## 30. First-Fill -> EFA Is Redundant When L2 PFC Already Gates EFA

**What happened on the reference project:**
Both `CHW-1040` (first fill) and `CW-1040` (first fill) had direct ties to EFA, but the L2 Cx PFC milestone was already an EFA pred — and L2 PFC requires first fill complete. Dropped 8 redundant ties.

**Fix:**
- Logic Auditor check: for every milestone, walk every direct pred 2 hops back; if any pred's pred is also a direct pred of the milestone, flag as redundant
- Common case: A -> B -> Milestone AND A -> Milestone (drop the direct A -> Milestone)

---

## 31. CDU and Rack Procurement Belong to the Client

**What happened on the reference project:**
First procurement audit suggested adding `PROC-DH4-CDU` activities. Patrick clarified: CDUs are the client's scope; the owner does NOT procure CDUs. Same for racks. Skip these.

**Fix:**
- Confirm scope split in Phase 1 (see kickoff checklist Section B)
- Document the client-vs-owner split in the assumptions register
- The MEL Reconciliation Agent should NOT flag missing CDU/rack PROC items as gaps — they're out of scope by design

---

## 32. Procurement Items Ride the Data Date When In-Progress

**What happened on the reference project v3.0:**
Some PROC items were marked `TK_Active` (vendor manufacturing in-progress) with no specific delivery date update yet. The XER had stale planned-finish dates. They should ride the data date until the procurement team gives a hard new date.

**Fix:**
- For `TK_Active` PROC items: set `remain_drtn_hr_cnt = (expected_delivery_date - data_date) * 8`
- If `expected_delivery_date <= data_date` (overdue), set remain_drtn to 8h and flag for procurement team status update
- Pattern from the reference project: PROC-DH4-CHWPLANT was overdue (exp del 4/8, still 0/5 received per MEL) — flagged in PROC-Verification-List

---

## 33. SS+Lag Overlap for Construction Crew Sequencing

**What happened on the reference project:**
UPS Pull -> UPS Term -> UPS Test was originally tied FS-FS-FS, forcing fully serial crew flow. In reality, the crew pulls cables continuously and terminations overlap pulls by ~50%. Switched to SS+lag (Term starts when Pull is 50% complete).

**Fix:**
- Use SS+lag for activities the same crew does in continuous flow with partial overlap
- Lag = duration of the predecessor's start-only fraction
- Document each SS+lag in the assumptions register with the rationale

---

## 34. PROC Bundle Splits Required for Mixed-Location Equipment

**What happened on the reference project:**
Original PROC structure had a single `PROC-DH4-MVSWGR` covering all 8 MV switchgear units. But 4 units go to the Yard (Yard MVSWGR) and 4 go to Mech rooms (Mech MVSWGR), plus a separate LV switchgear bundle. They have different vendors, different deliveries, different install dates.

Split into:
- `PROC-DH4-MV-Y` (Yard MV SWGR)
- `PROC-DH4-MV-Mech` (Mech room MV SWGR)
- `PROC-DH4-LV` (LV SWGR)

**Fix:**
- Equipment bundles should map 1:1 to (vendor, delivery, install-location). If any of those differ, split.
- MEL Reconciliation Agent should detect this: if one PROC has multiple delivery dates in the MEL, flag as a split candidate

---

## 35. MEL Data Quality Gotchas

**What happened on the reference project:**
- LV PO date typo: shown as 10/31/2024 but should be 10/31/2025 (off by a year). Caught by sanity check (PO before NTP).
- PWP4-03 expected delivery dates stale across multiple rows
- Several rows had different units of measure ("ea" vs "kit" vs blank) for the same equipment family

**Fix:**
- MEL Reconciliation Agent should flag:
  - Any PO date before project NTP
  - Any expected_delivery_date more than 60 days past data_date with no received qty
  - Any inconsistent unit-of-measure within an equipment family
- Don't silently propagate; surface for procurement team confirmation

---

## 36. Procurement Audit Must Reconcile in Both Directions

**What happened on the reference project:**
Initial audit only checked "every PROC activity has a MEL row." Patrick noted equipment families in the MEL with no corresponding PROC activity. Added the reverse check.

**Fix:**
- Run audit in both directions:
  - For each PROC activity, find the MEL row(s) -> flag orphans
  - For each MEL equipment family with material qty, find the PROC activity -> flag gaps
- Document both in the audit report

---

## 37. F&F Sequence — Flush First, Fill Second (Not the Other Way)

**What happened on the reference project (re-confirmation of lesson #5):**
Confirmed with the mechanical contractor that the operation is FLUSH-then-FILL. Any activity named "Fill & Flush" or "Fill/Flush" is wrong. Renamed across all DHs.

**Fix:**
- Regex sweep: `[Ff]ill[\s/&]+[Ff]lush` -> rename to "Flush & Fill"
- Build this into the Logic Auditor's name-convention check

---

## 38. Clone a Template TASK Row -- Never Build XER Rows From Scratch

**What happened on the reference project:**
v2.0 TASK rows were assembled field-by-field from scratch. On OPC import, 389
activities silently vanished -- no error, just a lower count than the file held.
OPC validates each TASK row against its schema; from-scratch rows had fields
that were subtly wrong, mis-ordered, or carried values OPC will not accept, and
it dropped them without a message.

**Fix:**
- Load a known-good template XER. Take a real TASK row as the structural
  baseline and overwrite ONLY the fields you control -- task_code, task_name,
  wbs_id, status, dates, durations, guid, constraints. Leave every other field
  exactly as the template has it. Do the same for TASKPRED and PROJWBS rows.
- `build_xer_starter.py` writes rows from scratch on purpose -- it is for
  minimal test XERs only. A production build must clone.

**Validation:**
- After import, compare OPC's activity count to the XER's TASK-row count. Any
  gap is this bug. `validate_xer.py` cannot catch from-scratch rows -- this is a
  build-method discipline, not a file check.

---

## 39. OPC Import Schema Rules -- proj_id, proj_short_name, duration_type

**What happened on the reference project:**
Several silent-drop / import-fail causes traced to schema-row fields:
- **proj_id** -- every TASK / TASKPRED / PROJWBS row must reference the PROJECT
  row's `proj_id`. Rows copied from another XER carry a foreign proj_id and drop.
- **proj_short_name** -- must change with every version. Reusing it made OPC
  treat a new version as the same project and merge unexpectedly.
- **duration_type vs task_type** -- a milestone carrying a task-style
  `duration_type` (or the reverse) is dropped silently on import.

**Fix:**
- `validate_xer.py` checks 10 and 12 enforce duration_type and proj_id. Run it.
- Bump `proj_short_name` on every versioned export.

**Validation:**
- `validate_xer.py` checks 10 and 12; confirm OPC's imported count matches.

---

## 40. MS-Project Outline Depth Varies Between Trade Files

**What happened on the reference project:**
The electrical contractor's nine XMLs and the mechanical contractor's XML did not share a consistent outline nesting. DH2's
XML had an extra wrapper level ("Data Hall 2" inside "Data Hall 2"),
shifting every child's OutlineLevel by 1. Code that classified a leaf's section
by absolute OutlineLevel mis-assigned every DH2 activity.

**Fix:**
- Detect sections by walking the outline PARENT-NAME chain and matching on names
  ("Mech Room", "UPS-East", "Data Hall proper") -- never by absolute OutlineLevel.
- `parse_msp.py` preserves each task's WBS / OutlineNumber so the parent chain
  is reconstructable.

**Validation:**
- Spot-check section assignment on the trade file with the deepest nesting.

---

## How to use these lessons on a new project

1. **Read this entire file before Phase 1.** Don't repeat these mistakes.
2. **Reference during Phase 4 (build) and Phase 6 (QA).** Most pitfalls show up there.
3. **Add new lessons** as you encounter them — log candidates to the project's `lessons-log.md` (the workflow's [CAPTURE] steps do this); they are promoted into this file via `/harvest-lessons` per `MAINTENANCE.md`.
4. **Run `validate_xer.py` and `cohesion_audit.py` before delivering any XER** -- together they cover every OPC-import and logic-integrity lesson in this file.
5. **Run `duplicate_audit.py` before merging any legacy schedule.**
6. **Run cycle detection (Tarjan SCC) after every retie operation.**

