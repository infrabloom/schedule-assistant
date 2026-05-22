# 7-Phase Workflow — Data Center Schedule Build

Each phase ends with a **[CHECKPOINT]** — stop, present findings, get explicit approval before continuing.

> **Phase numbering.** These seven phases are the skill's **build method**. The
> `/build-schedule` command orchestrates a build at a higher level with its own
> `build phase` numbers, and `/update-schedule` / `/harvest-lessons` have their own
> phases — none of those numbers map to the ones here. Each section below leads with
> its name; the `method phase N` tag is just ordering within this method.

Phases 3, 4, and 6 also carry a **[CAPTURE]** step, and Phase 7 a full **build retrospective**. Together these feed the lessons pipeline: a [CAPTURE] step appends lesson candidates to the project's `lessons-log.md` so they can be reviewed later — via the schedule-assistant plugin's `/harvest-lessons` — and the good ones promoted back into this skill. Capture is non-blocking: it never gates a phase, and if there is nothing worth logging, skip it. A build is the single richest source of lessons, so do not skip the Phase 7 retrospective. See `MAINTENANCE.md` for how a captured lesson becomes a skill update.

---

## Domain Knowledge from Templates — method phase 1

**Goal:** Build domain knowledge from reference P6 templates before touching project data.

**Inputs:** P6 reference templates (XER files) in `assets/p6-templates/`.

**Tasks:**
1. Parse XER structure and WBS hierarchy from each template
2. Build activity inventory by room type (Mech Room, Data Hall, Yard, Roof, Corridor)
3. Trace construction-to-commissioning logic chain
4. Identify interdependency gates (which milestones depend on what)
5. Extract milestone vocabulary and standard durations
6. Note any calendar conventions (5-day, 6-day, 7-day, holidays?)

**Deliverable:** `Phase1-Domain-Knowledge-Memo.md`

**[CHECKPOINT]** — Verify the memo with the PM. Confirm WBS structure, activity catalog, and L1-L5 framework before Project Source Extraction.

---

## Project Source Extraction — method phase 2

**Goal:** Extract actuals + planned activity from project-specific source documents. Trust hierarchy: client schedule > trade contractor schedules > prior GC schedule.

**Tasks:**
1. Read the **Build Sequence PDF** — authoritative for crew flow + area stagger
2. Read the **MEL.xlsx** — procurement quantities, lead times, zone mapping
3. Read the **Keyplan** — cross-reference zones (A-R) to construction Areas
4. Read **client high-level schedule** — extract contractual milestones (EFA/FA/MEC/TCO/PCO)
5. Read **electrical contractor schedule** (OCE) — extract per-DH electrical detail
6. Read **mechanical contractor schedule** (MLP) — extract piping, equipment, commissioning
7. Read **prior GC schedule** — extract actuals through data date; FLAG bad logic / duplicates separately, do NOT carry forward
8. Build a **trade responsibility matrix** — who does what (see `03-trade-responsibility-map.md`)

**Deliverable:** `Phase2-Extraction-Report.md` — list discrepancies between sources, gaps, open questions.

**[CHECKPOINT]** — Present extraction report. Confirm sources used and trust hierarchy.

---

## Logic & Assumptions Memo — method phase 3

**Goal:** Design the schedule structure (WBS, activity catalog, predecessor logic) BEFORE building.

**Tasks:**
1. Lock the **zone-to-Area cross-reference table**
2. Draft the **proposed WBS hierarchy** (typically 7-8 L1 branches)
3. Write the **construction logic narrative** — how trades sequence
4. Identify **interdependency gates** (M1-Mn master milestones, G1-Gn gates)
5. Build the **activity list per Area / room** with durations from templates + project sources
6. Define **procurement-to-install logic** (typically FF for long-lead, FS for short-lead)
7. Map **contractual milestones** and flag any at-risk dates
8. Document **A1-An assumptions** (everything the scheduler is choosing without explicit source data)

**Deliverable:** `Phase3-Logic-And-Assumptions-Memo.md`

**[CHECKPOINT]** — Walk PM through the assumptions list. Get explicit approval on:
- WBS shape
- Activity catalog completeness
- Procurement-to-install tie convention
- Milestone interpretations (especially EFA/FA scope)
- Any contractual not-later-than constraints

**[CAPTURE]** — Append lesson candidates from this phase to `lessons-log.md`: a source-of-truth conflict you resolved, a duration held against a trade's stated number, an ambiguous milestone interpretation, a non-obvious WBS or tie-convention decision.

---

## Build DH4 / First Data Hall — method phase 4

**Goal:** Build ONE Data Hall fully. Validate the structure works before replicating.

**Tasks:**
1. Build the **XER writer script** (or use `scripts/build_xer_starter.py`)
2. Define **DH4 WBS hierarchy** in the script
3. Populate **DH4 activity inventory** per the Logic & Assumptions Memo
4. **Apply actuals** through data date from sources
5. Build all **logic ties** for DH4 activities + procurement + commissioning
6. Generate XER and **verify importable in OPC** (see `06-lessons-learned.md` for gotchas)
7. Write a **critical path narrative** for DH4 EFA + FA

**Deliverable:** `[Project]-Schedule-v1.xer` + `[Project]-Schedule-Narrative-v1.md`

**[CHECKPOINT]** — Import to OPC. Verify dates match expectations. PM approval before Replicate.

**[CAPTURE]** — Append lesson candidates from the first-DH build to `lessons-log.md`: an OPC import gotcha hit and fixed, a validator failure and its cause, a template-default duration that proved wrong, a logic tie that had to be reworked.

---

## Replicate to Other DHs + Admin — method phase 5

**Goal:** Scale DH4 pattern to DH3, DH2, DH1, and any auxiliary buildings.

**Tasks:**
1. Replicate DH4 activity structure for DH3, DH2, DH1, Admin
2. Apply **per-DH stagger** (typically 3-weeks-per-area)
3. Surface conflicts with contractual EFA/FA dates
4. Apply **per-DH actuals** from sources
5. Add **intra-Area concurrency** to close negative float where possible
6. **Ingest sub-schedule updates** if available (trade contractor mpp / xml)
7. Apply **field updates** (status, dates, durations from emails / meetings)
8. Track **assumptions and open items** in a register

**Deliverables:**
- `[Project]-Schedule-v2.xer`
- `[Project]-Schedule-Narrative-v2.md`
- `Open-Items-By-Discipline.md` (use template in `assets/output-templates/`)
- `Assumptions-Register.md`

**[CHECKPOINT]** — PM review. Resolve open items with stakeholders. Iterate on v2.x as new info arrives.

---

## QA & Validation — method phase 6

**Goal:** Run comprehensive validation to ensure the schedule is internally consistent and OPC-importable.

**Tasks:**
1. **Duplicate audit** — verify no activities, codes, or scope duplicates
2. **No-orphans audit** — verify every activity has ≥1 pred AND ≥1 succ AND forward chain reaches a contract milestone
3. **Constraint audit** — only CS_MEOA, CS_MEOB, CS_MSOA in use (no CS_MEO)
4. **Status/date consistency** — TK_Complete needs act_end; TK_Active needs act_start; TK_NotStart no act dates
5. **Predecessor types** — only PR_FS, PR_SS, PR_FF used (no PR_SF unless intentional)
6. **WBS / Calendar / Resource refs** — all valid
7. **Cycle detection** — no circular dependencies
8. **Field count validation** — all TASK rows have the same number of fields
9. **GUID validation** — all populated, none duplicated
10. **OPC import test** — actually import to OPC and verify scheduling succeeds (no PRM-009010001 errors)
11. **Duration cross-check** — compare schedule durations against trade contractor durations; flag major mismatches (template defaults vs trade-reported labor)

**Deliverable:** `Phase6-QA-Report.md` listing all checks + any issues found

**[CHECKPOINT]** — PM sign-off on validation results. Issues resolved or accepted as known-and-flagged.

**[CAPTURE]** — Append lesson candidates from QA to `lessons-log.md`: a duplicate or orphan class that recurred, a constraint-code or status/actuals error pattern, any check that should have caught an issue earlier.

---

## Final Deliverables — method phase 7

**Goal:** Produce the artifacts stakeholders need to communicate, decide, and review.

**Standard deliverables (use templates in `assets/output-templates/`):**

1. **PM Briefing** — schedule overview, source documents, logic principles, milestone dates vs contractual, assumptions, open items, talking points
2. **Critical Path Analysis** — per-DH critical path traced backward, what drives each milestone
3. **Recovery Plan** (if dates slip contract) — compression options, scope-change options, expedite procurement
4. **Mech Team Questions** — discipline-specific questions for trade meetings
5. **Procurement Critical-Items Chase List** — by-priority list of procurement items affecting the schedule
6. **Fragnet xlsx** for mech / electrical commissioning (FluidStack-style format)
7. **P6 Layout** for live status reporting from the schedule
8. **Final Narrative** documenting everything

**Build retrospective (feeds the lessons pipeline):**

Before closing the build, do a retrospective pass and consolidate lesson candidates into the project's `lessons-log.md`:

1. Walk the **assumptions register** — every assumption that closed out (confirmed, changed, or proved wrong) is a candidate lesson.
2. Walk the **open-items list** — every item resolved during the build, and how, is a candidate.
3. Re-read the **[CAPTURE]** entries already logged in Logic & Assumptions, Build DH4, and QA & Validation — confirm each still reads true now the build is done, and add anything missed.
4. Note any **duration, sequencing, or trade-responsibility** call the build proved right or wrong against the reference templates.

This is capture, not promotion — nothing changes this skill here. Hand the consolidated log to the schedule-assistant plugin's `/harvest-lessons`, which reviews it with the user and promotes the keepers back into this skill per `MAINTENANCE.md`.

**[CHECKPOINT]** — Stakeholder review (PM + PE + trade leads + commissioning + FluidStack/owner). Include the build retrospective in the review.

---

## Between phases — version control

Increment major version (`v1`, `v2`, `v3`) on approved phase completion. Minor versions (`v2.1`, `v2.2`) for iterations within a phase. Keep all old XER files in `outputs/` — never overwrite.

## Common mistakes to avoid

See `06-lessons-learned.md` for the full list. Top 5:

1. Using `CS_MEO` constraint code (OPC rejects — use `CS_MEOA`)
2. Setting TK_Active status without act_start_date (OPC scheduler fails)
3. Carrying forward duplicate activities from legacy schedules (always audit before merging)
4. Confusing "Flush & Fill" vs "Fill & Flush" terminology — convention is FLUSH first, then FILL
5. Treating template-default durations as authoritative when trade-contractor durations differ 3-10×
