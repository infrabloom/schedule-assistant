# Changelog — schedule-assistant plugin

Version history of the **plugin itself**: its engine scripts, commands, agents,
docs, and the bundled `data-center-schedule` skill. Follows semantic versioning.

> **This is not the schedule audit trail.** Each project keeps its own
> `CHANGELOG.md` in the project folder — `apply_changeset.py` appends one entry
> per committed change-set. *That* file is the historic record a scheduler uses
> to trace an unexpected schedule change back to the change-set and date that
> caused it. This file tracks the **tool**, not any one schedule.

The bundled skill carries its own finer-grained version line in
`skills/data-center-schedule/SKILL.md` (currently v1.14). The plugin version and
the skill version move independently; each plugin release bundles whatever skill
version was current at the time.

---

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
