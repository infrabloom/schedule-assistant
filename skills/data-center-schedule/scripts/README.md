# Builder Scripts -- DC Schedule XER Generation

Python tooling to generate, validate, and audit P6 / Oracle Primavera Cloud
(OPC) XER files for hyperscale data center schedules. No external dependencies
for the core tools (Python 3.9+, standard library only).

## Files

| File | Purpose |
|---|---|
| `build_xer_starter.py` | Skeleton builder. Defines `T()` (task), `P()` (predecessor), `TASK_CONSTRAINTS` (milestones), the WBS hierarchy and calendars. Copy to a project's `outputs/`, rename to `build_xer_v1.py`, edit, run to generate `[Project]-Schedule-v1.xer`. |
| `validate_xer.py` | **The single comprehensive validator.** 21 FAIL checks + 7 WARN checks covering every OPC-import and logic-integrity failure mode found on CB4. Run before any XER is considered done. Exits non-zero on any failure. |
| `cohesion_audit.py` | Detailed pre-delivery cohesion report -- lists every orphan and dead-end chain grouped by WBS (validate_xer caps its output; this one is exhaustive). Mandatory before delivery. |
| `duplicate_audit.py` | Scans an XER for duplicate activities by code, name keyword, and WBS scope. Run before merging any legacy schedule. |
| `parse_xer.py` | XER reader. Loads any XER into Python dicts for analysis. |
| `parse_msp.py` | Microsoft Project XML reader (OCE / MLP trade schedules). Direct-child-only field extraction, ISO-8601 duration parsing, calendar parsing, CB4-style activity-code extraction. |
| `analyze_msp.py` | Empirically derives the TRUE duration basis of an MSP file from its completed activities -- so the calendar conversion factor is measured, not guessed. |
| `crosscheck_msp.py` | Cross-checks MSP `Duration` vs planned dates vs %complete, and computes the conversion to an 8h/day work-hour basis. |
| `sanitize_xer.py` | Strips a real project XER into a reusable, client-safe template (see `MAINTENANCE.md`). |

> **History:** `validate_xer.py` here is the merge of the former
> `validate_xer.py` + `validate_xer_v2.py`. Those two never composed into a
> complete gate -- v2 added the OPC-schema checks but dropped orphans, cycles,
> chain-to-milestone, and aref/arls. The merged file carries all of them, plus
> two checks neither had (dangling TASKPRED references, floating milestones).

## What `validate_xer.py` checks

**FAIL (blocks OPC import or corrupts the schedule):**
1 bare `CS_MEO`/`CS_MSO` codes · 2 `TK_Active` w/o act_start · 3 `TK_Complete`
w/o act_start/act_end · 4 `TK_NotStart` w/ actuals · 5 pct/remain/status
inconsistent · 6 duplicate code (exact) · 7 duplicate code (**case-insensitive**)
· 8 duplicate GUID · 9 GUID not 22-char standard base64 · 10 `duration_type`
vs `task_type` · 11 midnight `00:00` timestamps · 12 `proj_id` mismatch ·
13 orphans · 14 forward chain reaches a milestone · 15 dangling TASKPRED
reference · 16 `aref`/`arls` present · 17 predecessor type · 18 cycles ·
19 WBS hierarchy + depth · 20 `wbs_id` reference · 21 calendar reference.

**WARN (review, non-blocking):** W1 constraint code outside the OPC-safe set ·
W2 floating contract milestone · W3 activity riding a project-start milestone ·
W4 no `proj_id` to check task consistency against · W5 no milestone activities
(chain-to-milestone check skipped) · W6 multiple PROJECT rows in the file ·
W7 `PR_SF` ties (legal but discouraged).

## How to use on a new project

1. Copy `build_xer_starter.py` to the project's `outputs/`, rename `build_xer_v1.py`.
2. Edit the WBS hierarchy, calendar, and project metadata at the top.
3. Add `T(...)` calls for every activity and `P(...)` calls for every tie.
4. Populate `TASK_CONSTRAINTS` for milestones.
5. Run: `python build_xer_v1.py` -> emits `[Project]-Schedule-v1.xer`.
6. Validate: `python validate_xer.py outputs/[Project]-Schedule-v1.xer`.
7. Before delivery, also run `python cohesion_audit.py outputs/[Project]-Schedule-v1.xer`.
8. If both pass: import to OPC, run F9, verify dates.
9. Iterate: increment to `v2`, `v3`, ...

## Conventions

- **Activity ID:** `[PREFIX]-[AREA]-[ROOM]-[NNNN]` (e.g. `CONS-DH4-MR-1000`).
- **Prefix:** `CONS` construction, `PROC` procurement, `CX` commissioning, `MS` milestone.
- **Area:** `DH1`-`DH4`, `ADMIN`, `SITE`.
- **Numbering:** `1000`-`9999`, gap-numbered (1000, 1010, 1020 -- room to insert).

## Reminders

- **Always run `validate_xer.py` before delivering.** Fix every FAIL.
- **Run `cohesion_audit.py` as the last pre-delivery step.**
- **Increment the version on every material change.** Never overwrite a delivered XER.
- **Syntax-check the build script** (`python -m py_compile build_xer_vN.py`) before running.

See `../references/06-lessons-learned.md` for the full list of pitfalls these scripts protect against.
