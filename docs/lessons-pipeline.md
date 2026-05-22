# Lessons Pipeline

How the schedule-assistant learns. Building and maintaining schedules generates
lessons; this pipeline captures them, reviews them with you, and promotes the
keepers into the bundled `data-center-schedule` skill - so each project starts
smarter than the last.

Three stages - **capture -> review -> promote** - and one firm rule: capture is
automatic, promotion is not. Nothing changes the skill without your approval.

## Two layers of learning

The pipeline routes each candidate to one of three homes.

| Layer | Examples | Home |
|---|---|---|
| Scheduling craft | durations, OPC constraint quirks, sequencing logic, trade responsibility, stagger patterns | the bundled skill - `references/06-lessons-learned.md`, `references/02-schedule-patterns.md` |
| Tooling / workflow | a change-set schema gap, a script bug, something an agent missed | the plugin - `docs/`, `scripts/`, the schema |
| Project facts | a client's EFA definition, real contractual dates, named people | the project folder only - never promoted |

The skill is the compounding asset: Phase 1 of every future build reads it. Project
facts are deliberately kept out - see the skill's `MAINTENANCE.md`, "What NOT to
contribute".

## Stage 1 - Capture (automatic)

Both commands capture lesson candidates to the project's `lessons-log.md`:

- **`/build-schedule`** - the phased build has `[CAPTURE]` steps at the Logic &
  assumptions, first-unit Build, and QA checkpoints, plus a build retrospective
  (see the skill's `references/01-phased-workflow.md`). A build is the single
  richest source of lessons.
- **`/update-schedule`** - the Capture-lessons step captures from every update run: bad input logic,
  a source-of-truth conflict, an approval-gate override, a duration off by more than
  a shift from the sub's value, a corrected validator issue, a change-set that
  reversed an earlier one.

Capture is non-blocking and cadence-neutral - it never gates a phase or a commit.
The log lives in the project folder; it is project data, one log per project.

## Stage 2 - Review (gated)

Run `/harvest-lessons` at a wrap-up, a phase boundary, or whenever the log has built
up. The `lessons-harvester` subagent reads the log, the change-sets, and the change
log; deduplicates; cross-checks against the lessons already in the skill so nothing
is proposed twice; categorizes each candidate by home; and recommends an action. The
command presents the proposal and **stops at an approval gate** - the same gate model
as `/update-schedule`'s Approval gate.

## Stage 3 - Promote (after approval)

The skill is bundled inside this plugin, so promotion edits the plugin's own files.
Approved craft lessons append to
`skills/data-center-schedule/references/06-lessons-learned.md` or
`02-schedule-patterns.md`; tooling lessons edit the plugin directly. The skill
changelog and `plugin.json` are bumped, each promoted log entry is dispositioned, and
the plugin repo is committed and pushed so every device gets the update.

## Why capture is automatic but promotion is not

Capturing costs nothing, and a missed lesson is the real loss - so capture runs on
every build and every update with no gate. Promotion changes the skill that every
future project depends on, and a wrong lesson baked in there is expensive to undo. So
promotion always goes through review and your explicit approval - consistent with the
project rule to flag and ask rather than assume.

## Files

| File | Role |
|---|---|
| `commands/build-schedule.md` | `[CAPTURE]` at build checkpoints + build retrospective |
| `commands/update-schedule.md` | Capture-lessons step captures from each update run |
| `commands/harvest-lessons.md` | the review-and-promote command |
| `agents/lessons-harvester.md` | the independent review subagent |
| `lessons-log.md` (project folder) | the running capture log, one per project |
| skill `references/01-phased-workflow.md` | defines the `[CAPTURE]` steps + retrospective |
| skill `MAINTENANCE.md` | the promotion procedure |
| skill `references/06-lessons-learned.md` | where promoted craft lessons land |
