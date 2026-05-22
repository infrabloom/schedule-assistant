---
description: Build a new P6 / OPC schedule from scratch - intake inputs, draft a build-brief, then run the phased build with checkpoint gates.
---

# Build Schedule

Create a new data center schedule from the ground up. Use this when starting a
new building (a new campus, a follow-on building, ...) - as opposed to `/update-schedule`, which
maintains an existing one. The build is driven by a **build-brief** and follows
the bundled `data-center-schedule` skill's phased method, stopping at every
CHECKPOINT for explicit approval.

Locations:
- domain skill - `${CLAUDE_PLUGIN_ROOT}/skills/data-center-schedule/` (references + scripts)
- build-brief  - the project's `build-brief.yaml`
- inputs       - the project's `inputs/` folder
- outputs      - the project's `outputs/` folder

Before starting, read the skill: `SKILL.md`, then `references/01-phased-workflow.md`,
`references/06-lessons-learned.md`, and `references/11-infrastructure-primer.md`.

> **Precondition - the project must be set up first.** This command builds *into
> an existing project folder*. Before anything else, check that the folder has
> the `inputs/`, `outputs/`, and `changesets/` structure. If it does not, the
> project has not been set up - **stop and tell the user to run `/start-project`
> first.** `/build-schedule` does not scaffold the folder; it expects it to exist.

> **Where files go.** The project folder is the folder this Cowork project is
> connected to - refer to it by its absolute path. **Every file this command
> produces - the builder script, every schedule XER, every deliverable - is
> written inside that project folder** (XERs and the builder script go in its
> `outputs/` subfolder). **Never write a schedule file to a temporary, scratch,
> or session working directory** - the user must be able to open these files on
> their own drive. At every checkpoint that produces a file, state the file's
> full absolute path.

> **Phase numbering.** The phases below are scoped to the **build workflow** only.
> They are not the same phases as `/update-schedule`, `/harvest-lessons`, or the
> skill's build method (`references/01-phased-workflow.md`). Each section leads
> with its name; the `build phase N` tag is just ordering within this command.

## Brief & classify · build phase 0

**If `/start-project` was already run for this project, `build-brief.yaml`
exists** - read it, confirm it with the user, and go straight to the checkpoint
below. Otherwise establish the **build-brief** here (`docs/build-brief-schema.md`
defines every field; copy `docs/build-brief.example.yaml` as the starting point).
Two intake modes:

**Full-input mode** - the project has real inputs. Inventory every file in
`inputs/` and tag each by role: `template` (a P6 reference XER), `client-context`
(milestone definitions, contract dates), `good-schedule` (a sound prior schedule
- import its logic + durations), `bad-schedule` (a flawed prior schedule - mine
it for ACTUALS ONLY, never logic), `trade-schedule` (a sub's detailed schedule),
`mel` (a Master Equipment List).

**Minimal-input mode** - the only input is a project description. Build the
draft from the bundled skill itself: pick the closest P6 template
(`skills/.../assets/p6-templates/`, see `references/12-reference-template-library.md`),
seed activities from `references/13-activity-catalog.md`, durations from
`references/08-duration-benchmarks.md`, structure from `references/02-schedule-patterns.md`,
the staging picture from `references/11-infrastructure-primer.md`. EVERYTHING
produced this way is pattern-derived, not sourced - so it must be delivered as a
clearly-marked DRAFT with a prominent assumptions register, every fabricated
duration and tie flagged for trade confirmation. Never present a minimal-input
build as if it were sourced.

Then set the **target schedule level (Level 1-5)** per `references/09-schedule-levels.md`
- L1 milestone, L2 summary, L3 control CPM, L4 execution, L5 look-ahead -
confirm the repeating-unit count + stagger, and set the **build mode**
(`first_unit_review`: build the first unit and pause for your review - the default
and recommendation - or build the whole schedule at once). Set the **scheduling
basis** too - `scheduling.actuals` (status-updated to actuals, or a clean
baseline) and `scheduling.milestones` (contract milestones pinned, or a free
forecast); see `references/14-scheduling-basis.md`.

Write `build-brief.yaml`. **CHECKPOINT - present the brief before extraction.**

## Source extraction · build phase 1

Hand the input inventory to the **source-extractor** subagent. It reads every
input in parallel and returns one extraction note per file: what it holds, what
to pull, what to ignore, conflicts with higher-authority sources (resolve by the
brief's source-of-truth hierarchy). In minimal-input mode this phase is light -
the "source" is the chosen template plus the skill references.
**CHECKPOINT - present extraction notes + conflicts.**

## Logic & assumptions · build phase 2

- Lock the WBS (from a `good-schedule` / `template`, or the skill's pattern).
- Build the activity catalog at the target level (`09-schedule-levels.md` sets
  how dense; `13-activity-catalog.md` says which activities exist).
- Define predecessor logic per discipline - cite the source for every tie and
  every duration; never invent one. Stamp the per-equipment start-up micro-chain
  from `13-activity-catalog.md` onto each equipment assembly.
- Apply the **scheduling basis** (`references/14-scheduling-basis.md`): if the
  brief's `scheduling.milestones` is `to-contract`, every contractual milestone
  gets a `CS_MEOB` constraint at its contract date; if `forecast`, milestones stay
  unconstrained. If `scheduling.actuals` is `applied`, actual start / finish / %
  are applied through the data date and remaining work forecasts forward; if
  `none`, the build is a clean baseline (all `TK_NotStart`).
- Start the assumptions register - every non-sourced number goes here.
**CHECKPOINT - present catalog + logic + assumptions before building.**

**[CAPTURE]** - append lesson candidates from extraction and logic design to the
project's `lessons-log.md`: a resolved source-of-truth conflict, a duration held
against a trade's stated number, an ambiguous milestone interpretation, a non-obvious
WBS or tie decision. Non-blocking - see `docs/lessons-pipeline.md`.

## Build the first unit · build phase 3

Copy `${CLAUDE_PLUGIN_ROOT}/skills/data-center-schedule/scripts/build_xer_starter.py`
into the **project's `outputs/` folder** as `build_xer_v1.py` - i.e. to the full
path `<project folder>/outputs/build_xer_v1.py`. The builder writes its XER next
to itself, so the schedule lands in the project's `outputs/` folder; after it
runs, confirm the XER is actually there.

Build ONE repeating unit (the first Data Hall / Phase) fully - clone a real
template TASK row as the schema baseline (lesson #38; never assemble rows from
scratch). Run `validate_xer.py` on the XER; fix every FAIL.

**How this phase ends depends on `first_unit_review` in the build-brief:**
- **`first_unit_review: true` (the default) - HARD STOP.** Build ONLY the first
  unit. Do **not** build, replicate, or even begin any other unit. Present the
  first unit, the validation result, and the full XER path, and **wait for the
  user's explicit approval** before the Replicate phase. This is a hard gate, like
  the `/update-schedule` approval gate - building the rest before approval defeats
  the entire purpose of building one unit first.
- **`first_unit_review: false` - no stop.** The first unit is just the pattern;
  continue straight into Replicate. There is still one checkpoint at the end
  (QA & deliverables).

**CHECKPOINT (when `first_unit_review: true`) - present the first unit + validation
result + the full XER path in the project's `outputs/` folder, and STOP for approval.**

**[CAPTURE]** - append lesson candidates from the first-unit build to `lessons-log.md`:
an OPC import gotcha hit and fixed, a validator failure and its cause, a
template-default duration that proved wrong, a logic tie that had to be reworked.

## Replicate · build phase 4

On approval of the first unit (or directly, if `first_unit_review: false`), scale
the first unit to all units with the brief's confirmed stagger - as date offsets,
NOT cross-unit predecessor chains (lesson #26). Apply actuals where a source
provides them. Add cross-area ties only where physically real.

## QA & deliverables · build phase 5

Hand the built XER to the **build-auditor** subagent: it runs `validate_xer.py`,
`cohesion_audit.py`, and `duplicate_audit.py` and reports. Fix every FAIL; review
every WARN. Then produce the deliverables per the skill, **written into the
project folder**: schedule narrative, assumptions register, open-items list,
critical-path trace per milestone, PM briefing. Confirm the build-complete
checklist in `references/10-acceptance-criteria.md`.

**Build retrospective** - before closing the build, consolidate lesson candidates into
`lessons-log.md`: walk the assumptions register (every assumption that closed out is a
candidate) and the open-items list, and re-read the earlier `[CAPTURE]` entries
(Logic & assumptions, Build the first unit) to confirm they still read true now
the build is done. This is capture, not promotion -
the log is reviewed later via `/harvest-lessons`. A build is the richest source of
lessons; do not skip it. See `docs/lessons-pipeline.md`.

## Rules
- Stop at every CHECKPOINT; do not proceed without explicit approval.
- When `first_unit_review` is true, the first-unit checkpoint is a hard STOP -
  build exactly one unit and wait; never replicate before the user approves.
- Cite a source for every duration and logic tie; never fabricate. A
  minimal-input build flags every pattern-derived value in the assumptions register.
- Clone a template row; never hand-assemble XER rows from scratch (lesson #38).
- Validate before every checkpoint and before delivery.
- Every file produced - the builder script, every XER, every deliverable - is
  written into the project folder, never a temporary or scratch directory.
- Increment the version on every material change; never overwrite a delivered XER.
- Use only OPC-safe constraint codes: CS_MEOA / CS_MEOB / CS_MSOA.
- Capture lessons as you go - `[CAPTURE]` at the Logic & assumptions and Build-the-
  first-unit checkpoints and a build retrospective at QA & deliverables, all feeding
  `lessons-log.md`. See `docs/lessons-pipeline.md`.

## After the build
The schedule then lives. Ongoing changes flow through `/update-schedule` -
change-sets, impact preview, approval gate. When the project finishes, contribute
back: sanitize its XER with `sanitize_xer.py` and add it to the skill's template
library (see the skill's `MAINTENANCE.md`).
