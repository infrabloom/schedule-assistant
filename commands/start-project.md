---
description: Stand up a new project before building or updating - scaffold the project folder, take in the input files, interview for milestones and sources, write project.yaml (and build-brief.yaml for a new build), then hand off to /build-schedule or /update-schedule.
---

# Start Project

The on-ramp for a new project. Run this **once per project**, before
`/build-schedule` or `/update-schedule`. It creates the project folder structure,
takes in the input files, collects the project's identity, contractual
milestones, and source hierarchy, and writes the config files - so the build or
update command starts from a complete, confirmed setup instead of an empty
folder.

This command does **not** install the plugin or set up a laptop - that is a
one-time machine step (see `docs/multi-device-setup.md`). `/start-project` owns
everything *after* the plugin is installed.

Locations:
- plugin docs   - `${CLAUDE_PLUGIN_ROOT}/docs/` (the build-brief + project schemas)
- the skill     - `${CLAUDE_PLUGIN_ROOT}/skills/data-center-schedule/`
- the project folder - the folder this Cowork project is connected to (on the
  cloud-synced drive - see `docs/multi-device-setup.md`)

> **Phase numbering.** The phases below are scoped to the **start workflow** only -
> not the same phases as `/build-schedule`, `/update-schedule`, `/harvest-lessons`,
> or the skill's build method. Each section leads with its name; the
> `start phase N` tag is just ordering within this command.

## Scaffold the project folder · start phase 1

**Do this first - before any interview question, before anything else.** The
build and update commands expect the folder structure to already exist; creating
it up front is what makes the rest of the workflow reliable.

1. Confirm the **project folder** with the user. By default it is the folder this
   Cowork project is connected to (e.g. `.../Schedules/DC1`). Confirm the path;
   if the user names a different location, use that.
2. Immediately create this structure inside the project folder (use the shell):

```
<project folder>/
  inputs/       source files for the build or update
  outputs/      schedule XER versions + backups
  inbox/        drop-zone for later updates
  changesets/   the change-set history
  CHANGELOG.md      (seeded - see below)
  lessons-log.md    (seeded empty)
```

3. Seed `CHANGELOG.md` with a title line and the `<!-- ENTRIES -->` marker -
   `apply_changeset.py` inserts each committed change-set's entry directly below
   that marker. Seed `lessons-log.md` with a title and a one-line note of the
   `LL-NNN` entry format (see `docs/lessons-pipeline.md`).
4. Tell the user the folders now exist, and name the full path to `inputs/` -
   they will need it in the next phase.

Do **not** create `project.yaml` or `build-brief.yaml` yet - those are written in
phase 4, from the interview.

## Add the input files · start phase 2

First, classify the project (one question):
- **New build** - no schedule exists yet; the goal is to build one.
- **Takeover** - a schedule (an XER) already exists; the goal is to start
  maintaining it through `/update-schedule`.

Then have the user place the project's files into the folder, using their
**file manager** (File Explorer on Windows, Finder on Mac) - **not** by uploading
them into the chat. The project folder is on disk and the assistant reads files
straight from it; uploading large schedule files as chat attachments bloats the
conversation and slows everything down. Where each file goes depends on the
project type:

- **New build** - all source files go in **`inputs/`**: reference templates,
  client / milestone documents, trade schedules, the equipment list (MEL).
- **Takeover** - the current schedule XER goes in **`outputs/`** - it is the base
  `/update-schedule` builds the first change-set against. Any new information to
  fold into that first update (a refreshed trade schedule, meeting notes) goes in
  **`inbox/`**.

Wait for the user to confirm the files are placed. Then read the folders,
inventory what is there, and role-tag every build input (`template`,
`client-context`, `good-schedule`, `bad-schedule`, `trade-schedule`, `mel` - see
`docs/build-brief-schema.md`). For a **takeover**, confirm the **base XER** in
`outputs/` - that is the file `/update-schedule` treats as the starting point.

Note any gaps. A missing source is an open item to record, not a reason to stop.

## Interview · start phase 3

Collect the following, asking one focused thing at a time:

1. **Identity** - project name, owner, GC, and the OPC **Project ID**. For a
   takeover, read the Project ID from the base XER and confirm it; for a new
   build, set it. The Project ID is carried unchanged through every later XER.
2. **Calendar** - the working calendar (default: 7-day, 8h/day, no holidays -
   confirm, do not assume).
3. **Contractual milestones** - ask the user what this project's contractual
   milestones are. Do **not** suggest milestone codes - every owner uses its own
   naming. For EACH milestone the user names, capture: code, name, the
   **definition in writing**, and the contract date. Press for the written
   definition - an ambiguous milestone definition is the single most expensive
   thing to get wrong (see the skill's `references/06-lessons-learned.md`,
   lesson #8). Record anything the user cannot supply as `TBD - get in writing`
   and carry it as an open item; never invent a date or a definition.
4. **Source-of-truth hierarchy** - have the user rank their input sources,
   highest authority first (typically: contract > sub-detailed electrical /
   mechanical schedules > draft / locked XER > client view > historic prior-GC
   XER).
5. **New build only** - the repeating unit (Data Hall / Phase / Unit), its count
   and sequence, and the per-unit stagger. Flag the stagger as **confirm with the
   GC** - do not assume it.
6. **New build only** - the target detail level (Level 1-5; see the skill's
   `references/09-schedule-levels.md`).
7. **New build only** - the **build mode**: ask whether to build the first
   repeating unit (one Data Hall / Phase) and **pause for review** before
   replicating to the whole schedule, or build the whole schedule in one pass.
   Default and recommendation: pause for review - a wrong pattern caught on one
   unit is far cheaper than the same error replicated across every unit. Record
   as `first_unit_review` (true / false) in the build-brief.

Use the skill's `references/05-project-kickoff-checklist.md` as the backing
checklist - it is the long-form version of this interview.

**CHECKPOINT - present the collected answers; do not write any config until the user approves.**

## Write config · start phase 4

Generate the config files from the interview and the file inventory:

- **`project.yaml`** (always) - per `docs/project-schema.md`: `project` identity,
  calendar, the `paths` block, `source_of_truth`, `conventions`, and
  `milestones.contract_pattern`. Derive the pattern from the milestone codes and
  how they appear in task codes; if the task-code convention is not yet known,
  say so and note that `predict_milestones.py`'s generic default applies until
  the pattern is refined.
- **`build-brief.yaml`** (new build only) - per `docs/build-brief-schema.md`,
  starting from `docs/build-brief.example.yaml`: identity, detail level, mode
  (full-input / minimal-input), the closest bundled template, units + stagger,
  the milestones, and the role-tagged inputs from phase 2.

Write both files into the project folder via the shell (reliable on a
cloud-synced folder).

**CHECKPOINT - present the generated `project.yaml` (and `build-brief.yaml`) for review before hand-off.**

## Hand off · start phase 5

- **New build** -> tell the user to run `/build-schedule`. Its Brief & classify
  phase will confirm the `build-brief.yaml` this command produced, rather than
  drafting one from scratch.
- **Takeover** -> tell the user to run `/update-schedule`. The base XER is in
  place and `project.yaml` is set, so the first run starts cleanly at Intake.

Remind the user: the project folder lives in the cloud-synced drive - one laptop
at a time, let sync settle on handoff (see `docs/multi-device-setup.md`); the
plugin itself travels via git, not the synced folder.

## Rules
- Run once per project. If `project.yaml` already exists, the project is already
  set up - use `/build-schedule` or `/update-schedule` instead.
- **Scaffold the folders first** (phase 1), before the interview - never leave the
  build or update command to find an empty folder.
- Input files go in the `inputs/` folder, never uploaded into the chat.
- Never invent a milestone date or definition - record `TBD - get in writing` and
  carry it as an open item.
- Stop at every CHECKPOINT; do not write the config files or hand off without
  explicit approval.
- The plugin and the bundled skill are never copied into the project folder -
  they are installed once per device.
