# schedule-assistant

A full-lifecycle assistant for Primavera P6 / Oracle Primavera Cloud (OPC) data
center schedules. It does two jobs:

- **`/build-schedule`** - create a new schedule from scratch. Intake templates,
  client context, trade schedules and equipment lists (or just a project
  description), then run a phased build with checkpoint gates to a chosen detail
  level (1-5).
- **`/update-schedule`** - maintain an existing schedule. Every change flows
  through a reviewed, independently verified change-set: no hand-edited XERs, no
  unexplained changes, a full audit trail.

## What's inside
- `commands/start-project.md` - the `/start-project` command (scaffold + onboard a new project)
- `commands/build-schedule.md` - the `/build-schedule` command (6-phase build)
- `commands/update-schedule.md` - the `/update-schedule` command (change-set cycle)
- `commands/harvest-lessons.md` - the `/harvest-lessons` command (review + promote lessons)
- `agents/` - `source-extractor` + `build-auditor` (build), `schedule-verifier` (update),
  `lessons-harvester` (lessons review)
- `scripts/` - the change-set pipeline (apply / verify / predict / review) on a
  shared `xer_io` + `operations` core
- `skills/data-center-schedule/` - the bundled domain skill: 14 references, P6
  reference templates, the activity catalog, and the build / validate / parse toolkit
- `docs/` - `build-brief-schema.md`, `changeset-schema.md`, `project-schema.md`,
  `pipeline-cli.md`, `lessons-pipeline.md`, `multi-device-setup.md`, `setup-guide.md`
- `tests/` - the test harness (`unittest`): fixture builder, operation unit
  tests, and pipeline regression tests. Run `python -m unittest discover -s tests`

## How it works
A **build-brief** (YAML) declares what to build; `/build-schedule` runs it
through extraction -> logic -> first unit -> replicate -> QA, stopping at every
checkpoint. Once the schedule lives, a **change-set** (YAML) declares each batch
of edits; `/update-schedule` runs change-set -> patch -> independent verify ->
milestone pre-check -> commit. OPC's F9 scheduler stays authoritative throughout.

## How it learns
Every `/build-schedule` and `/update-schedule` run captures lesson candidates to the
project's `lessons-log.md` - at the build checkpoints, the build retrospective,
and each update's Capture-lessons step. `/harvest-lessons` then reviews that log
with you and promotes the keepers into the bundled `data-center-schedule` skill, so
each project starts smarter than the last. Capture is automatic; promotion needs
your approval. See `docs/lessons-pipeline.md`.

## Install
This repository is a single-plugin marketplace. On any machine:
```
/plugin marketplace add https://github.com/infrabloom/schedule-assistant
/plugin install schedule-assistant@schedule-assistant
```
`/build-schedule` and `/update-schedule` are then available in Claude Code and Cowork.

## Requirements
- **Python 3.9+** - the pipeline scripts use PEP 585 builtin generics.
- **PyYAML** - the only third-party dependency: `pip install -r requirements.txt`.

Plugin version history lives in `CHANGELOG.md` at the plugin root. That is the
history of the *tool*; it is distinct from each project's own `CHANGELOG.md`,
which is the schedule's per-change-set audit trail.

## Per-project setup
The plugin is generic. Each project (DC1, DC2, ...) keeps its own folder:
```
inputs/  outputs/  inbox/  changesets/  build-brief.yaml  project.yaml  CHANGELOG.md  lessons-log.md
```
`build-brief.yaml` drives a new build; `project.yaml` + `changesets/` drive
updates. The plugin code never changes per project.

## Lifecycle
New project -> `/start-project` (scaffold + onboard) -> `/build-schedule` -> the
schedule lives -> `/update-schedule` for every change after that -> at project
close, sanitize the final XER and contribute it back to the skill's template library.

See `docs/setup-guide.md` for the full walkthrough.
