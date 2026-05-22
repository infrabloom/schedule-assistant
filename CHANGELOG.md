# Changelog — schedule-assistant plugin

Version history of the **plugin itself**: its engine scripts, commands, agents,
docs, and the bundled `data-center-schedule` skill. Follows semantic versioning.

> **This is not the schedule audit trail.** Each project keeps its own
> `CHANGELOG.md` in the project folder — `apply_changeset.py` appends one entry
> per committed change-set. *That* file is the historic record a scheduler uses
> to trace an unexpected schedule change back to the change-set and date that
> caused it. This file tracks the **tool**, not any one schedule.

The bundled skill carries its own finer-grained version line in
`skills/data-center-schedule/SKILL.md` (currently v1.16). The plugin version and
the skill version move independently; each plugin release bundles whatever skill
version was current at the time.

---

## 0.5.6 — 2026-05-22 — Scheduling basis is now explicit

- New build-brief / `project.yaml` block **`scheduling`** with two fields:
  `actuals` (`applied` = status-updated to the data date · `none` = clean
  baseline) and `milestones` (`to-contract` = pin contract dates as `CS_MEOB`
  constraints and show float · `forecast` = leave milestones free, compare to
  contract separately).
- `/start-project` asks for both in its interview; `/build-schedule` builds to
  them — milestone constraints and actuals are now a deliberate, recorded choice
  instead of implicit.
- New skill reference **`14-scheduling-basis.md`** documents the P6 mechanics:
  both CPM passes, the OPC-safe constraint codes, how float reads, and the common
  combinations. Bundled skill → v1.16.

## 0.5.5 — 2026-05-22 — Staged build is a choice, and a real hard stop

- New build-brief field **`first_unit_review`** (default `true`): build the first
  repeating unit, pause for your review, then replicate — or set it `false` to
  build the whole schedule in one pass. `/start-project`'s interview asks for it.
- Fixed: `/build-schedule` built the entire schedule at once, blowing past the
  first-unit checkpoint. When `first_unit_review` is true, that checkpoint is now
  a hard STOP — build exactly one unit and wait for approval before replicating,
  the same gate model as `/update-schedule`'s approval gate.

## 0.5.4 — 2026-05-22 — /build-schedule writes into the project folder

- Fixed: the first-unit XER (and other build outputs) could land in the
  assistant's temporary scratch directory instead of the project's `outputs/`
  folder, where the user couldn't find it. `/build-schedule` now states
  explicitly that every file it produces — the builder script, every XER, every
  deliverable — is written into the connected project folder (XERs in
  `outputs/`), never a scratch location, and reports each file's full path at the
  first-unit checkpoint.

## 0.5.3 — 2026-05-22 — Full project-name sanitization

- Genericized **every** reference to the project the plugin was built from —
  ~294 occurrences across ~30 files (skill references, `SKILL.md`,
  `MAINTENANCE.md`, docs, scripts, command files). Owner / client / site /
  contractor / contract names and building codes are now generic: "the owner",
  "the client", "the site", "the electrical contractor", "the mechanical
  contractor", "the cooling-commissioning contractor", "the contract", "the
  reference project".
- The skill's lessons, patterns, durations, and guidance are unchanged — only
  the names were swapped, so nothing ties the plugin to a specific job. The
  bundled template XERs were already sanitized (skill v1.6).
- Bundled skill → **v1.15**.

## 0.5.2 — 2026-05-22 — Update-side on-ramp + generic prompts

- **`/update-schedule` precondition.** On an empty or bare folder it now stops and
  directs the user to `/start-project` (takeover path) instead of dead-ending —
  setup (folders + `project.yaml`) stays a single job, `/start-project`.
- **Takeover file placement.** `/start-project`'s takeover path now puts the
  current schedule XER in `outputs/` (the base `/update-schedule` works from) and
  new update info in `inbox/`; build sources still go in `inputs/`.
- **Generic command prompts.** `/update-schedule` no longer names project-specific
  contractors or documents — it cites "trade schedules", "the equipment list", and
  "the contract document" generically.
- **Update files via `inbox/`.** `/update-schedule`'s Intake step now explicitly
  routes new files to the `inbox/` folder, not chat uploads.

## 0.5.1 — 2026-05-22 — /start-project on-ramp fixes from the first test run

- **Scaffold first.** `/start-project` now creates the project folder structure
  (`inputs/ outputs/ inbox/ changesets/` + seeded `CHANGELOG.md` /
  `lessons-log.md`) as its unmissable first action, before any interview — so the
  build and update commands never find an empty folder.
- **Files go in the folder, not the chat.** The intake step moved up and tells the
  user to copy files in with their file manager rather than uploading them.
- **Generic milestone interview.** Dropped the preloaded `EFA / FA` examples; the
  interview asks the user for their own milestone codes without steering.
- **`/build-schedule` precondition.** It checks the project folder is set up and
  tells the user to run `/start-project` first if not, instead of stumbling.

## 0.5.0 — 2026-05-22 — New command: /start-project

- Added the **`/start-project`** command — the on-ramp for a new project, run
  once before `/build-schedule` or `/update-schedule`. It scaffolds the project
  folder (`inputs/ outputs/ inbox/ changesets/`, a seeded `CHANGELOG.md` and
  `lessons-log.md`), classifies new-build vs takeover, interviews the user for
  identity, contractual milestones (code / name / written definition / date),
  and source hierarchy, takes in and role-tags the input files, and writes
  `project.yaml` (plus `build-brief.yaml` for a new build).
- `/build-schedule`'s Brief & classify phase now *confirms* a brief that
  `/start-project` produced rather than always drafting one; `/update-schedule`
  notes the first-run base XER. `README.md` and `docs/setup-guide.md` updated.

## 0.4.11 — 2026-05-22 — Multi-device setup guide

- Replaced `docs/google-drive-setup.md` with `docs/multi-device-setup.md` — a
  cloud-agnostic guide (OneDrive *or* Google Drive) covering both layers: the
  plugin distributed via git, project data via cloud sync, the per-laptop
  Windows/Mac setup, the daily loop, and the rules that keep a sync client from
  corrupting files. Updated the four references to the old filename.

## 0.4.10 — 2026-05-22 — Final polish before first git release

- Fixed a latent Windows crash: `build_xer_starter.py` printed a `←` arrow that
  is not in the cp1252 codepage — replaced with ASCII `<-`.
- Cleared the ambiguous "increment 2" jargon from the deferred-operation messages
  and docstrings (`apply_changeset.py`, `operations.py`, `changeset-schema.md`).
- Rewrote the stale `tests/README.md` — it described the suite as it stood three
  refactors ago and omitted two test files.
- `README.md` "What's inside": added `docs/pipeline-cli.md` and the shared
  `xer_io` / `operations` core to the listings.

## 0.4.9 — 2026-05-22 — Consistency fixes (review §6.8 / §6.9)

- `MAINTENANCE.md`: documented the **append-only** reference-numbering policy and
  how to add a new reference file; replaced the stale "repackage the `.skill`"
  step with the bundled-skill model (validate, then commit the plugin).
- `validate_xer.py`: docstring now lists all seven WARN checks (was W1–W3).
- Created `skills/data-center-schedule/assets/exemplars/` — the contribution
  model referenced it but the folder did not exist.
- Neutral "PyYAML is required" message (dropped the Debian-specific flag).
- `operations.py`: durations and lags now round instead of silently truncating.
- `predict_milestones.py`: documented the calendar-day forecast approximation.

## 0.4.8 — 2026-05-22 — Shipping hygiene (review §7)

- Added this plugin-level `CHANGELOG.md`.
- Added `requirements.txt` (PyYAML; documents the Python 3.9 floor).
- Added `.gitignore` and a GitHub Actions CI workflow (`.github/workflows/ci.yml`)
  that runs the test suite on Python 3.9 and 3.12.
- `plugin.json`: added `repository` and `homepage`.
- Archived five superseded standalone skill snapshots out of the working tree.

## 0.4.7 — 2026-05-22 — Docs cleanup (review §6.2)

- Removed the dangling `/weekly-issue` reference from `update-schedule.md`. The
  "Issuing to stakeholders" guidance is kept, reworded to describe issuing as the
  manual OPC step it actually is.

## 0.4.6 — 2026-05-22 — Uniform CLI + JSON output (review §6.6 / §6.7)

- Every pipeline script now accepts `--json` (one JSON object on stdout, the
  human report on stderr) and follows the `0` / `1` / `2` exit-code convention.
- `review_changeset.py` consumes the sub-scripts' JSON and exit codes instead of
  scraping their prose. `predict_milestones.py` now exits non-zero on a milestone
  regression.
- `validate_xer.py` and `duplicate_audit.py` moved to `argparse` (so `-h` works).
- Added `docs/pipeline-cli.md` documenting the contract.

## 0.4.5 — 2026-05-22 — Phase vocabulary (review §6.1)

- The build / update / harvest workflows and the skill's build method each had
  their own bare "Phase N". Headings now lead with a descriptive name and the
  number is scoped to its workflow (`build phase 2`, `update phase 4`, …).

## 0.4.0 – 0.4.4 — 2026-05-22 — P0/P1 hardening + core refactor

- **P0:** atomic staged writes (temp + `os.replace`), a base-relative validation
  gate that blocks only change-set-introduced issues, clean aborts on bad input,
  and a single source-of-truth validator.
- **P1:** de-hardcoded the contract-milestone pattern into `project.yaml`; added
  `docs/project-schema.md`; built the `tests/` harness.
- **Refactor:** consolidated the XER parser/writer into `scripts/xer_io.py` and
  the change-set engine into `scripts/operations.py` (shared by the patcher and
  the verifier via one operation registry); CRLF-faithful round-trips; real
  base64 GUIDs on newly created activities.

## 0.3.0 — Expert plugin review baseline

- The version at which the full plugin review (P0/P1/P2 roadmap) was conducted.
