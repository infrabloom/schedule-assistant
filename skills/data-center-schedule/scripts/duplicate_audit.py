"""
duplicate_audit.py — scan an XER for likely duplicate activities.

Three levels of duplicate detection:
  1. Identical task_code (hard duplicate — always fail)
  2. Identical task_name within the same WBS branch (probable duplicate)
  3. Similar task_name within the same WBS branch (heuristic — "Fill" + "Flush",
     "Test" + "Commission", etc.)

Run BEFORE merging any legacy schedule into a new project.

Usage:
    python duplicate_audit.py path/to/Schedule.xer
    python duplicate_audit.py path/to/Schedule.xer --json

With --json, a single machine-readable JSON object is written to stdout and the
human-readable report is routed to stderr.

Exit codes:
    0  no hard (same-code) duplicates
    1  one or more hard duplicates found
    2  usage error / file not found
"""

import sys
import json
import argparse
import collections
import re
from pathlib import Path


def parse_xer(path: Path) -> dict:
    text = path.read_text(encoding="cp1252", errors="replace")
    tables = {}
    current_table = None
    current_fields = None
    for line in text.split("\n"):
        line = line.rstrip("\r")
        if line.startswith("%T\t"):
            current_table = line.split("\t", 1)[1].strip()
            tables[current_table] = []
            current_fields = None
        elif line.startswith("%F\t"):
            current_fields = line.split("\t")[1:]
        elif line.startswith("%R\t") and current_fields is not None:
            values = line.split("\t")[1:]
            while len(values) < len(current_fields):
                values.append("")
            tables[current_table].append(dict(zip(current_fields, values)))
        elif line.startswith("%E"):
            break
    return tables


# Keyword groups for fuzzy duplicate detection
DUPE_KEYWORDS = [
    {"flush", "fill"},      # F&F vs Fill/Flush
    {"test", "commission"}, # Test vs Commission overlap
    {"energize", "energization"},  # variant spelling
    {"sts", "static"},      # STS = Static Transfer Switch
    {"cdu"},
    {"chiller", "chw"},
    {"transformer", "tx"},
    {"switchgear", "swgr", "swbd"},
    {"ups"},
    {"generator", "gen", "genset"},
    {"rack"},
    {"hydrotest", "hydro"},
]


def find_duplicates(tables, xer_name):
    tasks = tables.get("TASK", [])
    wbs_by_id = {w.get("wbs_id"): w.get("wbs_short_name") for w in tables.get("PROJWBS", [])}

    print(f"Scanning {len(tasks)} tasks for duplicates...")
    print()

    # Level 1: hard duplicates (same code)
    codes = [t.get("task_code") for t in tasks]
    code_counts = collections.Counter(codes)
    hard_dupes = {c: n for c, n in code_counts.items() if n > 1}
    if hard_dupes:
        print(f"FAIL  LEVEL 1: HARD DUPLICATES - {len(hard_dupes)} task codes appear more than once")
        for c, n in sorted(hard_dupes.items()):
            print(f"    {c} (×{n})")
        print()
    else:
        print("OK    Level 1: no duplicate task codes")
        print()

    # Level 2: same name in same WBS
    name_wbs = collections.defaultdict(list)
    for t in tasks:
        wbs = wbs_by_id.get(t.get("wbs_id"), "?")
        name_wbs[(wbs, t.get("task_name", "").strip().lower())].append(t.get("task_code"))
    soft_dupes = {k: v for k, v in name_wbs.items() if len(v) > 1}
    if soft_dupes:
        print(f"WARN  LEVEL 2: SAME NAME IN SAME WBS - {len(soft_dupes)} cases")
        for (wbs, name), codes_ in sorted(soft_dupes.items()):
            print(f"    [{wbs}] '{name}': {codes_}")
        print()
    else:
        print("OK    Level 2: no same-name duplicates in same WBS")
        print()

    # Level 3: fuzzy by keyword group within WBS
    print("INFO  LEVEL 3: HEURISTIC GROUPING (review each for true duplicates)")
    fuzzy_dupes = []
    by_wbs = collections.defaultdict(list)
    for t in tasks:
        wbs = wbs_by_id.get(t.get("wbs_id"), "?")
        by_wbs[wbs].append(t)
    for wbs, wbs_tasks in by_wbs.items():
        for kw_group in DUPE_KEYWORDS:
            matches = []
            for t in wbs_tasks:
                name = t.get("task_name", "").lower()
                if any(kw in name for kw in kw_group):
                    matches.append(t)
            if len(matches) > 1:
                fuzzy_dupes.append((wbs, kw_group, matches))

    for wbs, kw_group, matches in fuzzy_dupes[:30]:  # cap output
        print(f"    [{wbs}] keywords {kw_group}:")
        for m in matches:
            print(f"        {m.get('task_code'):30s}  {m.get('task_name')}")
        print()

    if len(fuzzy_dupes) > 30:
        print(f"    ... and {len(fuzzy_dupes)-30} more fuzzy groups")

    print()
    print("Summary:")
    print(f"  Hard duplicates (code): {len(hard_dupes)}")
    print(f"  Soft duplicates (name in WBS): {len(soft_dupes)}")
    print(f"  Fuzzy groups (keyword): {len(fuzzy_dupes)}")
    print()
    if hard_dupes:
        print("FAIL: hard duplicates must be resolved before delivery.")
    return {
        "script": "duplicate_audit",
        "xer": xer_name,
        "ok": not hard_dupes,
        "hard_duplicates": len(hard_dupes),
        "soft_duplicates": len(soft_dupes),
        "fuzzy_groups": len(fuzzy_dupes),
        "issue_count": len(hard_dupes),
    }


def main():
    ap = argparse.ArgumentParser(
        description="Scan an XER for likely duplicate activities "
                    "(hard / soft / fuzzy).")
    ap.add_argument("xer", help="path to the XER file to scan")
    ap.add_argument("--json", action="store_true",
                    help="emit a machine-readable JSON result on stdout "
                         "(the human report goes to stderr)")
    args = ap.parse_args()

    path = Path(args.xer)
    if not path.exists():
        if args.json:
            print(json.dumps({"script": "duplicate_audit", "xer": str(path),
                              "ok": False, "error": "file not found"}))
        else:
            print(f"File not found: {path}", file=sys.stderr)
        sys.exit(2)

    # In --json mode the human report runs onto stderr; stdout carries only JSON.
    if args.json:
        sys.stdout = sys.stderr
    tables = parse_xer(path)
    result = find_duplicates(tables, path.name)
    if args.json:
        sys.stdout = sys.__stdout__
        print(json.dumps(result))
    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
