# Reference P6 Templates -- Read for Structure, Not as Baselines

Three **sanitized** hyperscale data center construction schedules, kept as
structural / domain reference for Phase 1. Full analysis:
`references/12-reference-template-library.md`.

| File | Profile | Size / density |
|---|---|---|
| `VA-DC-Template.xer`  | ~7-phase build | 1,115 tasks -- Level 3 |
| `VA2-DC-Template.xer` | ~10-phase, clean replication | 2,044 tasks -- Level 3 |
| `IN-DC-Template.xer`  | ~12-phase, commissioning-heavy | 7,112 tasks -- Level 4 |

Use them to learn: activity catalog and naming, WBS shape and depth, calendar
conventions, realistic durations, and logic patterns.

## Sanitized

These were sanitized with `scripts/sanitize_xer.py`: client / contractor / site
names and project numbers scrubbed, actuals reset, export-user genericized, all
GUIDs regenerated. Safe to keep bundled in the skill.

## Reference only -- not clean baselines

They still carry orphans, dead-end chains, and "DELETED ACTIVITIES" / "COPY
HERE" branches from their source projects, so they **do not pass
`validate_xer.py` / `cohesion_audit.py`**. **Do not import a template as a
baseline.** Read it for structure, then build clean; re-validate any logic
copied from one.
