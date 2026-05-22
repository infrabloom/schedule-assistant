# schedule-assistant - Setup & Operating Guide

## 1. What you have

Two parts, kept separate on purpose:

- **The plugin - `schedule-assistant/`** - the reusable engine. Install once; it
  never changes per project. Holds the `/start-project`, `/build-schedule`,
  `/update-schedule`, and `/harvest-lessons` commands, the subagents, the
  change-set pipeline scripts, the schemas, and the bundled
  `data-center-schedule` domain skill (references, P6 templates, validators).
- **The project - your project folder (e.g. `New DC1/`)** - just data. One per
  building. Holds `inputs/`, `outputs/`, `inbox/`, `changesets/`,
  `build-brief.yaml`, `project.yaml`, and `CHANGELOG.md`.

The plugin acts on the project. To run a second building, install the same
plugin and create a second project folder with its own brief and config.

## 2. Two ways to run it

### Option A - Use it now, no install (start here)
The `schedule-assistant/` folder is in your connected workspace. Nothing to
install - just chat: "Build a new schedule" or "Run a schedule update." The
assistant follows the command files directly. The only thing you miss is the
typed `/build-schedule` / `/update-schedule` shortcuts.

### Option B - Install as a plugin (typed commands + multi-device)
Installing registers the slash commands and the named subagents.

**Claude Code:**
```
/plugin marketplace add <path-or-git-url of the schedule-assistant folder>
/plugin install schedule-assistant@schedule-assistant
```
**Cowork:** add the marketplace and install `schedule-assistant` from Cowork's
plugin settings.

**Multi-device:** `git init` the `schedule-assistant/` folder, push to GitHub,
then on each machine `/plugin marketplace add <repo-url>`. Push once, update
everywhere.

## 3. The project folder

`/start-project` scaffolds and fills this for you - run it once before the first
build or update:
```
<project>/
  inputs/          source files for a build (trade schedules, MEL, templates, ...)
  inbox/           you drop new files here for updates
  outputs/         schedule XER versions + automatic backups
  changesets/      the change-set history (immutable)
  build-brief.yaml the build contract  (copy docs/build-brief.example.yaml)
  project.yaml     update config: Project ID, milestone pattern, source hierarchy
  CHANGELOG.md     the human-readable audit log
```

## 4. Starting a NEW schedule - `/build-schedule`

For a new building or a new campus:

1. **In chat: `/start-project`.** It scaffolds the project folder, interviews you
   for identity, contractual milestones, and source hierarchy, takes in your
   source files, and writes `build-brief.yaml` + `project.yaml`. (Skip if the
   project is already set up.)
2. **In chat: `/build-schedule`.** It confirms the build-brief `/start-project`
   produced - or drafts one with you if you skipped that step - and stops at the
   **Brief & classify checkpoint** for your approval.
3. It then runs the phased build - source extraction, logic & assumptions,
   first unit, replicate, QA - **stopping at every checkpoint** for you.
4. The QA & deliverables phase produces the deliverables: the validated XER, schedule narrative,
   assumptions register, open-items list, critical-path trace, PM briefing.
5. **Import the XER into OPC**, run **F9**, and the schedule is live.

From here on, every change goes through `/update-schedule`.

## 5. Updating an EXISTING schedule - `/update-schedule`

First time taking over an existing schedule? Run **`/start-project`** once to
scaffold the project folder, capture its milestones, and place the base XER.
After that, each update cycle is:

1. **Drop the week's files into `inbox/`** - refreshed trade schedules, meeting
   minutes, an OPC export.
2. **In chat: `/update-schedule`.** The assistant drafts a **change-set** and
   posts the **Impact Preview** - what changes, the independent verification,
   the milestone table, the verdict.
3. **Review and reply** - "approved", or request revisions. Nothing commits yet.
4. On approval it commits the new version and appends `CHANGELOG.md`.
5. **Import that XER into OPC**, run **F9**, export the rescheduled XER back into
   `inbox/` as the base for next time.

## 6. Day to day

- **Questions / document review** - just ask. No command, no schedule change.
- **Quick status read** - "milestone health check" runs the forecast.
- **Any change** - one line or a weekly batch, it goes through `/update-schedule`
  and the approval gate.

## 7. The rules that keep it safe

- Nothing reaches OPC without you - the assistant produces the XER; you do the
  import and F9.
- `/build-schedule` stops at every phase checkpoint; `/update-schedule` stops at
  the approval gate. Neither proceeds without you.
- Every change is cited; the XER is never hand-edited.
- Every duration and logic tie cites a source - a minimal-input build flags
  every pattern-derived value in the assumptions register.
- A malformed input aborts the run - it never hands over a half-applied schedule.

The bundled `data-center-schedule` skill provides the domain framework - the
7-phase method, the 14 references, the P6 templates, and the validators - that
both commands run on.
