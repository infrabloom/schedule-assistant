---
name: data-center-schedule
description: "Use this skill for hyperscale data center scheduling work — building, auditing, replicating, or refreshing a Primavera P6 / OPC schedule. Triggers include starting a new DC schedule, taking over from a prior scheduler, building or editing XER files, EFA / FA / FR / RFS / MEC / TCO / PCO milestones, sequencing mech rooms / data halls / yards / roof / MMR, multi-DH replication with N-week stagger, L1-L5 commissioning (FAT / PFC / Functional / IST / Load Bank), procurement-to-install ties for long-lead equipment (STS, CDU, Fan Wall, MV switchgear, UPS, generators), trade responsibility mapping, weekly refreshes from electrical / mechanical contractor MS-Project XMLs, reconciling MEL against the schedule, or fixing OPC import errors (PRM-009010001, missing milestones, CS_MEO drops, case-insensitive task code collisions). Use proactively whenever the user mentions data centers, hyperscale, P6, OPC, XER, EFA, FA, FR, RFS, PCO, or commissioning — even if they don't explicitly name P6."
---

<!-- Changelog
v1.0 (2026-05-12): Initial release from the reference project build (v1 -> v4.15 cycle)
v1.1 (2026-05-17): Folded in the reference project's v2/v3 rebuild — electrical-contractor/3
                   calendar conversion, many-to-one aggregation, retie residue, cross-DH FS
                   anti-pattern, MEL reconciliation, F&F sequence, client-vs-owner scope split,
                   OPC case-insensitive uniqueness, GUID base64 (not urlsafe), midnight time
                   rejection. Added validate_xer_v2.py and the 11-agent agentic workflow
                   pattern (ref 07).
v1.3 (2026-05-21): Merged the two validators into one comprehensive validate_xer.py
                   (21 FAIL + 7 WARN checks); added cohesion_audit.py; bundled the MSP
                   toolchain (parse_msp / analyze_msp / crosscheck_msp); added references
                   08 (duration benchmarks), 09 (schedule levels Level 1-5), 10 (build
                   acceptance criteria); generalized the MS-Project duration-basis lesson.
v1.4 (2026-05-22): Added reference 11 (infrastructure primer -- what each system
                   does + the Five-Envelope construction staging framework),
                   distilled from "The Data Center as a Computer" 4th ed. ch.5;
                   added infrastructure/design terms to the glossary and facility
                   staging long-leads to the duration benchmarks.
v1.5 (2026-05-22): Added reference 12 (analysis of the three bundled P6 templates
                   -- VA / VA2 / IN templates); added owner-specific milestone
                   terms to the glossary; flagged that the bundled templates were not yet sanitized.
v1.6 (2026-05-22): Sanitized the three bundled templates with sanitize_xer.py
                   (scrubbed client/contractor/site names + project numbers,
                   reset actuals, regenerated GUIDs); hardened sanitize_xer.py to
                   scrub every non-GUID field + export-user fields; genericized
                   reference 12 and the glossary.
v1.7 (2026-05-22): Mined the reference templates for planned-vs-actual variance
                   and a generic activity catalog; added reference 13 (activity
                   catalog + the per-equipment start-up micro-chain); extended
                   reference 12 and the duration benchmarks with the findings.
v1.8 (2026-05-22): Wired the lessons pipeline into the phased workflow -- [CAPTURE]
                   steps at the Phase 3/4/6 checkpoints and a Phase 7 build
                   retrospective, both feeding the project lessons-log.md; added
                   lessons-log.md to the kickoff checklist. Pairs with the
                   schedule-assistant plugin's /harvest-lessons (review + promote).
v1.9 (2026-05-22): Documentation cleanup -- corrected stale internal references
                   left from an earlier file reorg (old NN-CamelCase paths like
                   02-P6-Templates / 05-Output-Templates / 08-Lessons-Learned,
                   and validate_xer_v2.py -> validate_xer.py) across the phased
                   workflow, kickoff checklist, lessons-learned, agentic-pattern
                   reference, and scripts README; corrected the validator WARN
                   count (7, not 3).
v1.10 (2026-05-22): Skill-script portability fixes -- duplicate_audit.py output
                   uses ASCII tags instead of emoji (the emoji crashed on a
                   Windows cp1252 console and falsely failed the commit gate);
                   analyze_msp.py now takes MSP XML paths/globs as command-line
                   arguments instead of a hardcoded prior-session path.
v1.11 (2026-05-22): Phase-vocabulary cleanup (plugin review 6.1) -- the build
                   method's seven phases now lead each heading with their name
                   ("Domain Knowledge from Templates -- method phase 1"), with a
                   scoping note distinguishing them from the plugin's build /
                   update / harvest workflow phases, which collide by number.
v1.12 (2026-05-22): CLI uniformity (plugin review 6.6/6.7) -- validate_xer.py
                   and duplicate_audit.py now use argparse (so -h works) and
                   accept --json, emitting one machine-readable JSON object on
                   stdout with the human report on stderr. Exit codes follow the
                   0/1/2 convention. See the plugin's docs/pipeline-cli.md.
v1.13 (2026-05-22): Consistency fixes (plugin review 6.8/6.9) -- MAINTENANCE.md
                   documents the append-only reference-numbering policy and how
                   to add a reference file, and its skill-repackaging step now
                   reflects the bundled-skill model; validate_xer.py docstring
                   lists all seven WARN checks; added the assets/exemplars/
                   folder that the contribution model referenced.
v1.14 (2026-05-22): Final polish -- build_xer_starter.py no longer prints a
                   non-ASCII arrow that crashed a Windows cp1252 console
                   (replaced with ASCII); cleared the ambiguous "increment 2"
                   jargon from the change-set schema.
v1.15 (2026-05-22): Full sanitization -- genericized every reference to the
                   original project across all skill references, SKILL.md, and
                   scripts: owner / client / site / contractor / contract names
                   and building codes are now generic ("the owner", "the
                   electrical contractor", "the reference project", etc.). The
                   lessons and patterns are unchanged; only the names are gone.
v1.16 (2026-05-22): Added reference 14 (scheduling basis -- the actuals and
                   milestone-treatment axes, both CPM passes, constraint codes,
                   and how float reads); registered it in the reference table.
                   Pairs with the build-brief's new `scheduling` block.
-->

# Data Center Schedule Toolkit

A reusable framework for building, auditing, and replicating Primavera P6 / OPC schedules on hyperscale data center projects. Distilled from two full rebuilds of **the reference project** schedule (a hyperscale owner-side build) — every pattern, pitfall, and convention here is from real production experience. Designed to be **portable to the next build in the same program** or any equivalent hyperscale owner-side project.

## When to use this skill

Use it for any of these:
- Starting a new DC schedule from scratch (e.g., a new building)
- Taking over a schedule that has issues (broken logic, duplicates, missing actuals)
- Replicating a single Data Hall pattern across multiple DHs
- Building/repairing XER files for OPC import
- Auditing a schedule for orphans, duplicates, cycles, or constraint errors
- Running the **weekly refresh loop** from the electrical and mechanical contractors' detailed schedules
- Reconciling the schedule against the MEL (Master Equipment List)
- Answering questions about EFA/FA/FR/RFS/MEC/TCO/PCO scope or L1-L5 commissioning
- Determining trade responsibility (who owns CDU install? Fan Wall? Flush & Fill?)
- Diagnosing OPC import failures (PRM-009010001, missing milestones, dropped tasks)
- **Standing up an agentic Claude Code workflow** to operationalize the full pipeline — see `references/07-agentic-workflow-pattern.md`

## How to use this skill

### Step 1 — Orient

If this is the user's **first session** on a new project, read these in order before doing anything else:

1. `references/01-phased-workflow.md` -- the 7-phase methodology with checkpoint gates
2. `references/11-infrastructure-primer.md` -- what the equipment does + how a build is staged (domain background)
3. `references/05-project-kickoff-checklist.md` -- what inputs/decisions to collect
4. `references/06-lessons-learned.md` -- every documented pitfall (read this **before** writing any XER)
5. `references/07-agentic-workflow-pattern.md` -- only if standing up a multi-agent Claude Code workflow

If this is a **continuation session** (the user has prior work in the project folder), check existing outputs first, then ask the user which phase they believe they're in before continuing. **Never re-do approved work.** Increment versions; never overwrite a delivered XER.

### Step 2 — Follow the phased workflow

The skill enforces a 7-phase workflow with **hard checkpoint gates**:

```
Phase 1: Templates           -> Domain knowledge from P6 templates (read, don't import)
Phase 2: Source Extraction   -> Read project XERs, BIM, MEL, trade schedules
Phase 3: Logic & Assumptions -> WBS design, activity catalog, predecessor logic
Phase 4: Build first DH      -> One Data Hall fully built + OPC-validated
Phase 5: Replicate           -> Scale to all DHs + Admin + apply stagger + actuals
Phase 6: QA & Validation     -> No orphans, no duplicates, no cycles, OPC-importable
Phase 7: Deliverables        -> PM briefing, narrative, fragnets, P6 layouts
Weekly:  Refresh Loop        -> Diff electrical/mechanical contractor XMLs, transfer actuals, change log
```

At every CHECKPOINT, **stop and present findings to the user**. Do not proceed without explicit approval. This is the single most important rule in this skill — checkpoints exist to catch logic errors before they cascade.

### Step 3 — Consult references as needed

For each phase, you'll need different references. Reading just `SKILL.md` is not enough — open the reference file that matches your task:

| When you're working on... | Read this reference |
|---|---|
| Phase 1-2 (extraction, domain knowledge) | `references/01-phased-workflow.md` |
| Phase 3 (WBS shape, activity catalog, L1-L5 logic) | `references/02-schedule-patterns.md` |
| Phase 3 (who-owns-what scoping decisions) | `references/03-trade-responsibility-map.md` |
| Any phase (decoding acronyms / terminology) | `references/04-acronyms-glossary.md` |
| Pre-Phase 1 (collecting inputs and decisions) | `references/05-project-kickoff-checklist.md` |
| Phase 4-6 (building XER, avoiding pitfalls, validation) | `references/06-lessons-learned.md` |
| Multi-agent orchestration in Claude Code | `references/07-agentic-workflow-pattern.md` |
| Phase 3-4 (sanity-checking trade-reported durations) | `references/08-duration-benchmarks.md` |
| Phase 3-4 (choosing schedule density -- Level 1 to 5) | `references/09-schedule-levels.md` |
| Phase 6-7 (is the build done? acceptance gates) | `references/10-acceptance-criteria.md` |
| Any phase (what the equipment does, construction staging) | `references/11-infrastructure-primer.md` |
| Phase 1 (what the bundled reference XERs teach) | `references/12-reference-template-library.md` |
| Phase 3 (activity catalog + typical durations) | `references/13-activity-catalog.md` |
| Phase 3 (scheduling basis -- actuals + milestone constraints) | `references/14-scheduling-basis.md` |

### Step 4 — Build with the bundled scripts

For Phase 4 (building) and Phase 6 (validation), use the Python scripts in `scripts/`:

- `scripts/build_xer_starter.py` -- skeleton XER generator. Copy to the project's outputs folder, rename `build_xer_v1.py`, edit metadata + activity catalog + ties, run. **For minimal test XERs only -- a production build must clone a real template row (see lesson #38).**
- `scripts/validate_xer.py` -- **the single comprehensive validator** (21 FAIL + 7 WARN checks: every OPC-import and logic-integrity failure mode from the reference project). **Always run before delivering any XER.** Replaces the former validate_xer.py + validate_xer_v2.py.
- `scripts/cohesion_audit.py` -- detailed pre-delivery orphan / dead-end report, grouped by WBS. Mandatory before delivery.
- `scripts/duplicate_audit.py` -- scans for duplicate activities by code, name, and fuzzy keyword. Run before merging any legacy schedule.
- `scripts/parse_xer.py` -- generic XER reader; library for custom analysis.
- `scripts/parse_msp.py` -- Microsoft Project XML reader for electrical / mechanical contractor trade schedules (direct-child field extraction, ISO-8601 durations, calendar parsing).
- `scripts/analyze_msp.py` -- empirically derives a trade file's true duration basis, so the calendar conversion is measured, not guessed (see lesson #20).
- `scripts/crosscheck_msp.py` -- cross-checks MSP durations vs planned dates vs %complete.
- `scripts/sanitize_xer.py` -- strip a real project XER to a reusable template (for contribution-back; see `MAINTENANCE.md`)

Scripts have a `README.md` in `scripts/` covering conventions and usage.

### Step 5 — Use the templates for deliverables

`assets/output-templates/` contains markdown templates for Phase 7 deliverables:

- `PM-Briefing-Template.md` — executive summary of where the schedule lands
- `Open-Questions-Template.md` — chase-list organized by discipline
- `Critical-Path-Analysis-Template.md` — per-milestone backward trace
- `Assumptions-Register-Template.md` — everything baked into the schedule that isn't sourced from a document

Copy + fill in for the specific project.

### Step 6 — P6 template XERs for reference

`assets/p6-templates/` has reference XER files from prior hyperscale DC projects (VA2-DC, IN-DC, VA-DC). Use these in Phase 1 to extract domain knowledge — activity catalog, WBS shape, calendar conventions, standard durations. **Don't import these directly into a new project's OPC** — they're reference material, not starting baselines. They are sanitized exports from real projects and **do not pass `validate_xer.py` / `cohesion_audit.py`** -- they carry orphans, dead-ends and other artifacts from their source schedules. Read them for structure; never copy logic from them without re-validating and repairing it. See `assets/p6-templates/README.md`.

## Core conventions to enforce

These are non-negotiable on every DC schedule project. They come from real failures on the reference project (see `references/06-lessons-learned.md` for the full stories):

1. **Constraint codes in OPC:** Use only `CS_MEOA` (Finish On or After), `CS_MEOB` (FNL, Finish On or Before), `CS_MSOA` (SNE, Start On or After). **Never** use `CS_MEO` or `CS_MSO` — OPC silently drops them and milestones vanish from import.

2. **Status / actuals consistency:** Every `TK_Active` needs `act_start_date`. Every `TK_Complete` needs both `act_start_date` and `act_end_date`. Every `TK_NotStart` should have neither. Violations cause OPC error `PRM-009010001`.

3. **No-orphans rule:** Every activity must have >=1 predecessor AND >=1 successor AND the forward chain must reach a contract milestone (EFA / FA / FR / RFS / MEC / TCO / PCO / Project Completion).

4. **No cycles:** Run Tarjan SCC after every retie operation. The most common cycle source is residue from F&F sequence retie (spurious back-edges to construction crew chain).

5. **GUID format:** Base64-encoded UUID (standard alphabet, **not** urlsafe — no `-` or `_`). Pattern:
   ```python
   import base64, uuid
   guid = base64.b64encode(uuid.uuid4().bytes).decode('ascii').rstrip('=')
   # If you must use urlsafe_b64encode for some reason, replace - -> + and _ -> /
   ```

6. **Case-insensitive task_code uniqueness:** OPC treats `CONS-DH4-mr-1010` and `CONS-DH4-MR-1010` as the same task. Use lowercase-comparison in the build script.

7. **No midnight times.** Every date field in the XER should be `HH:MM` != `00:00`. OPC rejects rows with midnight timestamps. Standard is `08:00` for start, `17:00` for finish.

8. **Procurement-to-install convention:** FF (finish-to-finish) for long-lead equipment (MV SWGR, transformers, STS, UPS, CDU, Fan Wall, chillers); FS for commodity. Document in the assumptions register.

9. **Cross-discipline calendar conversion:** an MSP `<Duration>` is in (displayed days x MinutesPerDay/60) PT-hours. Derive the factor `8 / (MinutesPerDay/60)` per trade file -- it is **/3 for the electrical contractor** (1440 min/day) and **1 for the mechanical contractor** (480 min/day), but never hardcode /3. Run `scripts/analyze_msp.py` to confirm the basis empirically. This is the single most common source of duration errors. See lesson #20.

10. **Many-to-one aggregation:** the electrical and mechanical contractors' detailed schedules have fine-grained per-area sub-activities; the high-level schedule has aggregate activities (e.g., one `MR-1105` per DH represents 8+ electrical-contractor leaves). Build an explicit **electrical-contractor-leaf -> v3-task crosswalk catalog** as a one-time investment, then drive every weekly refresh from it. See lesson #22 and `references/07-agentic-workflow-pattern.md` (Catalog Builder agent).

11. **Stagger pattern:** Apply the project's per-DH stagger explicitly in activity start dates. Surface conflicts with contractual milestone dates immediately.

12. **No cross-DH crew chains.** Multiple crews work in parallel across DHs. Tying DH3 install activities as successors to DH4 install activities is **wrong** — it forces serial execution and inflates the schedule by 9+ weeks. Use the stagger pattern (date offsets) instead of pred chains. See lesson #26.

13. **Trade scope clarity:** CDUs are client scope (or vendor-installed — Schneider/Vertiv); Fan Walls are vendor scope. Flush & Fill is cooling commissioning scope (a cooling-commissioning contractor's trade), not install. Rack install is owner scope. Get the project's specific trade map locked in Phase 1.

## Working rules (always apply)

These apply universally:

1. **Show your reasoning** when making sequencing or logic decisions
2. **Cite the source file** when pulling a duration, logic tie, or actual
3. **Ask before assuming.** Surface gaps; do not fabricate
4. **Flag, don't silently fix.** If you find bad logic in inputs, surface it before changing
5. **Be conservative on actuals** — only mark progress with documentary evidence
6. **Stop at every CHECKPOINT** in the workflow runbook
7. **Never carry forward duplicates or broken logic** from prior schedules without flagging
8. **Validate every XER before delivery** — run `scripts/validate_xer.py` and `scripts/cohesion_audit.py`, fixing all failures or document each as known-and-flagged
9. **Increment version** on every approved phase or material change. Never overwrite a delivered XER.
10. **Re-run cycle detection after every retie operation.** F&F sequence retie is the most common source of new cycles.

## Project-specific things to leave behind

When using this skill on a **new** project, do **not** carry forward:

- Specific contractual dates (e.g., the reference project's EFA Jun 15, FA Jul 31)
- Specific trade names (the mechanical contractor, the cooling-commissioning contractor, the electrical contractor, and any other named subs — all reference-project-specific)
- Specific equipment counts (8 MV SWGRs, 192 STS, 72 Dry Coolers — reference-project-specific)
- Client-specific scope interpretations (the client's EFA = cooling-live, FA = racks)
- Specific actuals or progress percentages

The **pattern** (WBS shape, sequencing logic, L1-L5, FF procurement ties, no-orphans rule, validation checklist, MEL reconciliation, electrical-contractor/3 conversion, weekly refresh loop) is portable. The **numbers** are not.

## Program-specific carry-forward (for the next project in the same program)

These are owner conventions that **do** carry from the reference project to later buildings in the same program:

- **Owner-side scheduler model:** the owner owns the schedule; the GC manages subs (the electrical, mechanical, and cooling-commissioning contractors, the design engineer, etc.); the schedule gives all parties one shared view.
- **Contractual milestones:** EFA -> FA -> FR -> RFS per DH (per the contract's turnover dates).
- **Calendar:** 7-day, 8 hours/day, no holidays (unless the new project changes it — confirm in Phase 1).
- **Client vs owner scope split:**
  - CDUs: client scope (the owner does not procure CDUs)
  - Racks: client/owner-IT scope
  - Mech room equipment, electrical infrastructure, yards, MMRs: owner scope
- **WBS top-level pattern:** Milestones / Site & Shell / Per-DH (Construction + Cx) / Per-DH Procurement / Admin Building / MMRs
- **Per-DH WBS pattern:** MR (Mech Room) / DH (Data Hall proper) / RF (Roof) / CD (Corridors) / Yard
- **Naming convention:** `CONS-DH{n}-{room}-{seq}` for construction, `CX-DH{n}-{system}-{level}` for commissioning, `PROC-{system}-{n}` for procurement
- **Electrical-contractor/3 calendar conversion** (until the electrical contractor switches their MPP to 8h/day basis)
- **Weekly refresh cadence** from the electrical and mechanical contractors

## Decision rules

When in doubt:

- **If you don't know a duration:** ask the trade contractor. Never blindly use template defaults — they're often 3-10x lower than real trade labor (see lessons #6).
- **If two trades claim ownership of the same scope:** ask the GC PM to clarify in writing. Capture in the assumptions register.
- **If a contractual milestone interpretation is ambiguous:** get the owner to define it. Don't assume.
- **If a tie looks wrong but the prior schedule has it:** flag it, don't silently change it. Surface the question.
- **If validation fails:** fix the underlying issue. Don't suppress the check.
- **If electrical-contractor auto-matching produces low-confidence results:** build the crosswalk catalog manually as a one-time investment; don't ship bad auto-matches.

## Output expectations

By Phase 7, the project should have these deliverables:

- `[Project]-Schedule-v[N].xer` — final P6 export
- `[Project]-Schedule-Narrative-v[N].md` — documents WBS, logic, durations, sources
- `PM-Briefing.md` — executive summary
- `Open-Items-By-Discipline.md` — chase list
- `Assumptions-Register.md` — everything baked in
- `Critical-Path-Analysis.md` — per-milestone backward trace
- `Electrical-Mechanical-Crosswalk-Catalog.xlsx` — leaf-to-aggregate map for weekly refresh
- Trade-specific question lists for next meetings
- (Optional) Fragnet xlsx for mech / electrical commissioning
- (Optional) P6 Layout xml for live status reporting

Everything goes in `outputs/` in the project folder.

## Starting a new project (quick-start)

When the user spins up a new Cowork project for the next build in the program:

1. **Create the project folder** with this structure:
   ```
   New {Project}/
     inputs/                  <- user drops source files here
     outputs/                 <- Claude writes here
     project-instructions.md  <- paste the kickoff prompt
   ```

2. **Paste the project-instructions** — adapt the prior project's Cowork prompt (or write fresh from `references/05-project-kickoff-checklist.md`), updating project-specific lines for the new project.

3. **Run Phase 1** — read this SKILL.md, then `references/01-phased-workflow.md`, then `references/06-lessons-learned.md`.

4. **Run Phase 2 (Source Extraction)** — produce one extraction memo per source file. Stop at the Phase 2 checkpoint.

5. **(Optional) Stand up the agentic workflow** in Claude Code — see `references/07-agentic-workflow-pattern.md` for the 11-agent persona pattern. Use the reference project build as the reference implementation.

## Maintaining this skill

When you finish a project, contribute back. See `MAINTENANCE.md` for the full procedure:

1. Sanitize the final XER with `scripts/sanitize_xer.py` and add to `assets/p6-templates/`
2. Append new lessons to `references/06-lessons-learned.md`
3. Add new patterns to `references/02-schedule-patterns.md` if applicable
4. Bump the changelog at the top of this file
5. Repackage with skill-creator

Lessons are no longer gathered from memory at wrap-up. The phased workflow's [CAPTURE] steps and Phase 7 build retrospective log candidates to the project's `lessons-log.md` as the build runs, and the schedule-assistant plugin's `/harvest-lessons` reviews that log and promotes the keepers — steps 2-4 above. `MAINTENANCE.md` has the detail.

The skill compounds in value when every wrapped project contributes back at least one of: a sanitized template XER, a new lesson, a new pattern, or an exemplar deliverable. The XER is the highest-value contribution — Phase 1 of every future project starts by reading these templates.
