# Pipeline CLI contract

Every pipeline script speaks one CLI dialect, so scripts can be chained and a
caller never has to scrape prose. This is the contract `review_changeset.py`
relies on when it orchestrates the others.

## Exit codes

| Code | Meaning | Examples |
|---|---|---|
| `0` | OK / clean | validation passed, change-set committed, no milestone regression |
| `1` | Finding | validation FAIL, verification discrepancy, milestone regression, hard duplicates, change-set rejected or blocked |
| `2` | Usage / IO error | bad arguments, missing file, malformed change-set YAML, unknown operation, unreadable XER |

A caller distinguishes "ran and found a problem" (`1`) from "could not run"
(`2`). Both are non-zero; only `0` means proceed.

## `--json`

Every script accepts `--json`. In JSON mode:

- **stdout** carries exactly one JSON object — nothing else.
- the **human-readable report** is routed to **stderr**, unchanged.
- the exit code is the same as in normal mode.

Without `--json` the script prints only the human report, on stdout, exactly as
before. JSON mode is purely additive.

Parse the result by reading stdout; never grep the human text.

## Scripts and their JSON

Each object carries a `script` field naming its producer, plus an `ok` boolean
or an equivalent verdict.

| Script | Key JSON fields |
|---|---|
| `validate_xer.py` | `ok`, `issue_count`, `fail[]`, `warn[]`, `passed_checks`, `counts{}` |
| `duplicate_audit.py` | `ok`, `issue_count`, `hard_duplicates`, `soft_duplicates`, `fuzzy_groups` |
| `predict_milestones.py` | `regression`, `regression_count`, `late_count`, `milestones[]`, `data_date` |
| `verify_changeset.py` | `ok`, `diff{}`, `problems[]`, `flags[]` |
| `apply_changeset.py` | `ok`, `committed`, `preview`, `operations[]`, `validation{}`, `output_path` |
| `review_changeset.py` | `verdict` (`SAFE_TO_APPROVE` / `REVIEW_NEEDED`), `verified`, `regression`, `new_validation_issue` |

`predict_milestones.py` exits `1` only in `--compare` mode when a milestone
moves later than the base; a plain forecast (no `--compare`) always exits `0`.

## CLI conventions

- All scripts use `argparse`, so `-h` / `--help` works everywhere.
- The positional argument is the primary input (an XER, or a change-set YAML).
- Validator and config directories are `--`-flags with sensible defaults.
