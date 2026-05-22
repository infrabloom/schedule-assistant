# Reference Template Library -- What the Bundled P6 Templates Teach

`assets/p6-templates/` holds three **sanitized** hyperscale data center
construction schedules, kept as **structural / domain reference** for Phase 1.
This file records what they are and what to learn from them -- a deliberate
second data point alongside the CB4 experience the rest of this skill is built
on, not "forgotten" attachments.

## The three templates

| File | Profile | Size / density |
|---|---|---|
| `VA-DC-Template.xer`  | Mid-size build, ~7 phases | 1,115 tasks, 2,194 ties -- schedule Level 3 |
| `VA2-DC-Template.xer` | Clean phase-replicated build, ~10 phases | 2,044 tasks, 3,972 ties -- schedule Level 3 |
| `IN-DC-Template.xer`  | Large, commissioning-heavy, ~12 phases | 7,112 tasks, 13,841 ties -- schedule Level 4 |

They were sanitized with `scripts/sanitize_xer.py`: client / contractor / site
names and project numbers scrubbed, actuals reset, export-user genericized, all
GUIDs regenerated. They are safe to keep bundled. Use them for **structure
only** -- they still carry orphans and dead-end chains from their source
schedules and **do not pass `validate_xer.py` / `cohesion_audit.py`**. Never
import one as a baseline.

## Per-template profile

**VA-DC** -- ~7 phases. WBS: Milestones / Schedule Issues / Procurement /
Permits & Design / Construction (largest branch) / Final Inspections /
Commissioning / Deleted Activities. Activity-level durations cluster ~6 days.
Density approx. schedule **Level 3**. Notable: rolls commissioning up thin;
carries a very large "Schedule Issues" branch.

**VA2-DC** -- ~10 phases, the cleanest **phase-replication exemplar**: each
Phase-N Construction branch is ~150 activities. WBS: Milestones / Issues /
Procurement / Construction. Durations cluster ~4 days. Density approx. **Level 3**.

**IN-DC** -- two projects in one file (one is an empty "COPY HERE" shell, one is
the real ~7,000-task schedule). ~12 phases. WBS: Milestones / Preconstruction /
QA-QC Mockups / Procurements & Deliveries / Construction / Startup-Commissioning
/ Fuel Piping. Durations cluster ~2 days. Density approx. **Level 4 (execution)**
-- commissioning/startup is roughly half the schedule. Has a dedicated "Liquid
Cooling Fabrication" procurement branch (AI-era cooling scope).

## What the templates teach (portable patterns)

1. **Hyperscale DC schedules are organized by a repeating unit.** TeraWulf calls
   it a Data Hall (x4); these templates call it a Phase / Unit (x7-12 per
   building). The skill's "build the first unit, replicate the rest" logic
   generalizes -- only the unit's name and count are project-specific.
2. **WBS top level is consistent:** Milestones / (Schedule) Issues / Procurement
   / Construction / Commissioning(Startup), plus Preconstruction, Final
   Inspections, Closeout. Matches the WBS pattern in `02-schedule-patterns.md`.
3. **Owner milestone vocabulary differs -- same shape, different names.** CB4 /
   TeraWulf: SWD -> EFA -> FA -> FR -> RFS. A second common hyperscale-owner
   pattern (seen across all three templates): Build Start -> Long-Lead-Equipment
   / OFCI On-Site Dates -> FEA -> NEA -> H2C -> PFHO -> PCO. Both run
   early-access -> handover -> completion. Map the new owner's vocabulary
   explicitly in Phase 1.
4. **The "Schedule Issues" WBS branch** -- delay / issue events tracked as
   activities under a dedicated branch. A useful transparency pattern for
   surfacing schedule impacts.
5. **Calendars:** 8 h/day is universal; the working DAYS per week vary
   (5-, 6-, 7-day variants). Some owners keep special single-weekday calendars so
   handover milestones land on fixed days.
6. **Logic profile:** finish-to-start dominant (65-83% of ties); FF and SS each
   a substantial 15-20% (real DC schedules use them heavily, not just FS);
   `PR_SF` rare but present -- which confirms treating PR_SF as a WARN, not a
   FAIL; lags used sparingly (<5% of ties carry a non-zero lag).
7. **Density scales with unit count x granularity:** ~1,100 tasks (Level 3) ->
   ~2,000 (Level 3) -> ~7,000 (Level 4). At Level 4, commissioning explodes.

## Planned vs actual durations

Each completed activity's planned calendar span was compared to its actual span:

- The **as-built** templates (VA2-DC, IN-DC) show almost no variance (median
  ratio 1.0; ~23% ran long). That is an artifact -- at closeout a scheduler
  trues up the planned dates to the actuals. An as-built therefore understates
  plan variance, but its durations ARE realized durations, which makes it a
  **trustworthy source of real activity durations**.
- The still-**live** template (VA-DC) shows the real picture: of multi-day
  completed activities, **~46% ran longer than planned**, and the upper quartile
  took **~2x** the planned span (p75 ratio 2.05; median planned span 10 d ->
  median actual 12 d).

Takeaway: trust as-built durations as benchmarks, but **plan duration
contingency** -- on a live schedule the overrun tail is heavy and one-sided.

## Logic patterns

Logic was reviewed at two levels. The **tie-type mix** is consistent and
portable (FS-dominant; FF and SS each 15-20%; PR_SF rare; lags <5% -- above).
The **per-equipment start-up micro-chain** (Construction Complete -> QC -> IEM
-> FOD/Energization -> Start-up Complete -> Start-up Report) is the templates'
most repeated fragnet, captured in `references/13-activity-catalog.md`. Full
per-phase predecessor networks are project-specific -- read them directly from
the closest template in Phase 1 rather than copying them.

## Cross-check against this skill -- result: aligned

- **WBS top-level pattern** -- matches `02-schedule-patterns.md`. OK.
- **Repeating-unit replication** -- matches the skill's DH-replication logic;
  generalizes cleanly (Data Hall <-> Phase / Unit). OK.
- **8 h/day calendar basis** -- consistent with the skill and lesson #20. OK.
- **PR_SF** -- the templates contain PR_SF ties, confirming the merged
  `validate_xer.py` is right to flag PR_SF as a WARN, not a FAIL. OK.
- **Templates fail `validate_xer.py` / `cohesion_audit.py`** -- expected; the
  orphans are partly the "DELETED ACTIVITIES" / "COPY HERE" branches the source
  owners keep. Consistent with `assets/p6-templates/README.md`.
- **Schedule size** -- the templates calibrate `09-schedule-levels.md`:
  size = repeating-unit count x density level.
- The skill is written in TeraWulf / CB4 / "Data Hall" terms; the templates show
  a second owner-model (Phase/Unit, an FEA/NEA/H2C/PFHO milestone set, an Issues
  branch). No contradiction -- the methodology holds; the templates broaden it.

## How to use these templates in Phase 1

1. Pick the closest template by size and density (small / Level 3 -> VA-DC;
   clean phase replication -> VA2-DC; large / Level 4 -> IN-DC).
2. Read its WBS and activity catalog to seed the new project's structure.
3. Map its milestone vocabulary onto the new owner's milestones.
4. **Do not import a template as a baseline** -- reference structure only, and it
   will not pass validation.
