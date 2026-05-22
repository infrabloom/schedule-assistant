# Tests — schedule-assistant

The test harness for the change-set pipeline. It is the safety net every refactor
and every new operation is checked against: the suite must pass before a change
and still pass after it.

## Prerequisites

- Python 3.9 or newer
- PyYAML — `pip install pyyaml` (or `pip install -r ../requirements.txt`)

## Run

From the plugin root:

```
python -m unittest discover -s tests -v
```

Or from this folder:

```
cd tests
python -m unittest -v
```

All tests are standard-library `unittest` — no third-party test framework. Every
test is self-contained: it builds its inputs in a temp directory and cleans up
after itself, so a run touches nothing in any project.

## What's covered

| File | Covers |
|---|---|
| `fixtures.py` | Builds `mini_xer()` — a small, structurally complete fixture XER (1 project, 1 calendar, 3 WBS nodes, 6 activities, a 4-link chain to a milestone). Assembled programmatically so column counts are always consistent. |
| `test_operations.py` | Unit tests for the engine: the `xer_io` parser/writer (LF *and* CRLF round-trips), all ten implemented change-set operations, the `expect:` guards, the `match:` selector, duplicate / case-collision rejection, real-GUID stamping, the deferred-operation guard, and the patcher/verifier registry-consistency check. |
| `test_pipeline.py` | Integration tests that run the scripts as subprocesses: clean aborts (never a traceback), atomic staging (no `.tmp` left, nothing committed on a preview), the base-relative validation gate, the end-to-end `review_changeset` packet, and the `--json` / exit-code contract on every pipeline script. |
| `test_predict.py` | Unit tests for `predict_milestones`' contract-milestone detection — the generic default pattern and project-specific overrides. |

## Notes

- `test_pipeline.py` uses **stub validators** — tiny scripts that exit `0` or `1`
  — so the gate logic is tested without depending on the bundled `validate_xer.py`
  or on the fixture passing all 21 real checks.
- The tests import `apply_changeset` / `operations` / `xer_io` directly; those
  modules import PyYAML at load time, so PyYAML must be installed for the suite
  to run.
- CI runs this suite on Python 3.9 and 3.12 on every push — see
  `.github/workflows/ci.yml`.
