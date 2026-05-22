#!/usr/bin/env python3
"""
cohesion_audit.py -- pre-delivery cohesion report for a P6 / OPC XER.

validate_xer.py is a pass/fail gate and caps its output at a few examples.
This script answers the same two cohesion questions in FULL DETAIL, grouped by
WBS, so you can actually fix them before a delivery:

  1. Orphans   -- every activity must have >=1 predecessor AND >=1 successor
                  (project-start / project-finish milestones are exempt).
  2. Cohesion  -- every activity's forward chain must reach a milestone;
                  dead-end logic means the activity drives nothing.

It also reports activities that ride a project-start milestone as their only
predecessor (often a sign of missing real logic).

Run this as the last step before handing over any XER. Mandatory per the
data-center-schedule skill's QA phase.

Usage:  python cohesion_audit.py path/to/Schedule.xer
Exit 0 if cohesive, 1 if any non-exempt orphan or dead-end chain is found.
"""

import sys
import collections
from pathlib import Path

MILESTONE_TYPES = {"TT_Mile", "TT_FinMile"}
START_KEYS = ("SWD", "START", "NTP")
END_KEYS = ("RFS", "PCO", "COMPL", "TCO")


def parse_xer(path):
    text = path.read_text(encoding="cp1252", errors="replace")
    tables, current, fields = {}, None, None
    for line in text.split("\n"):
        line = line.rstrip("\r")
        if line.startswith("%T\t"):
            current = line.split("\t", 1)[1].strip()
            tables[current] = []
            fields = None
        elif line.startswith("%F\t"):
            fields = line.split("\t")[1:]
        elif line.startswith("%R\t") and fields is not None:
            vals = line.split("\t")[1:]
            while len(vals) < len(fields):
                vals.append("")
            tables[current].append(dict(zip(fields, vals)))
        elif line.startswith("%E"):
            break
    return tables


def main():
    if len(sys.argv) < 2:
        print("Usage: python cohesion_audit.py path/to/Schedule.xer")
        sys.exit(2)
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(2)

    t = parse_xer(path)
    tasks = t.get("TASK", [])
    preds = t.get("TASKPRED", [])
    wbs = {w.get("wbs_id"): w.get("wbs_short_name") or w.get("wbs_id")
           for w in t.get("PROJWBS", [])}
    if not tasks:
        print("No TASK rows found.")
        sys.exit(1)

    by_id = {r.get("task_id"): r for r in tasks}
    id_set = set(by_id)
    succ_of = collections.defaultdict(list)
    pred_of = collections.defaultdict(list)
    for p in preds:
        sid, pid = p.get("task_id"), p.get("pred_task_id")
        if sid in id_set and pid in id_set:
            succ_of[pid].append(sid)
            pred_of[sid].append(pid)

    def wname(r):
        return wbs.get(r.get("wbs_id"), "(no WBS)")

    def is_start_ms(r):
        c = r.get("task_code", "").upper()
        return r.get("task_type") in MILESTONE_TYPES and any(k in c for k in START_KEYS)

    def is_end_ms(r):
        c = r.get("task_code", "").upper()
        return r.get("task_type") in MILESTONE_TYPES and any(k in c for k in END_KEYS)

    # orphans
    no_pred = [r for r in tasks if not pred_of.get(r.get("task_id")) and not is_start_ms(r)]
    no_succ = [r for r in tasks if not succ_of.get(r.get("task_id")) and not is_end_ms(r)]

    # forward chain to milestone (reverse BFS)
    milestones = {r.get("task_id") for r in tasks
                  if r.get("task_type") in MILESTONE_TYPES
                  or r.get("task_code", "").upper().startswith(("MS-", "MS_", "MS."))}
    reaches = set(milestones)
    dq = collections.deque(milestones)
    while dq:
        n = dq.popleft()
        for p in pred_of.get(n, ()):
            if p not in reaches:
                reaches.add(p)
                dq.append(p)
    dead_end = [r for r in tasks if r.get("task_id") not in reaches]

    # riding project start
    start_ids = {r.get("task_id") for r in tasks if is_start_ms(r)}
    riding = [r for r in tasks
              if r.get("task_type") not in MILESTONE_TYPES
              and pred_of.get(r.get("task_id"))
              and all(p in start_ids for p in pred_of.get(r.get("task_id")))]

    def dump(title, rows):
        print(f"\n{title}  ({len(rows)})")
        if not rows:
            print("  none")
            return
        grouped = collections.defaultdict(list)
        for r in rows:
            grouped[wname(r)].append(r)
        for w in sorted(grouped):
            print(f"  {w}:")
            for r in sorted(grouped[w], key=lambda x: x.get("task_code", "")):
                print(f"    {r.get('task_code'):<24} {r.get('task_name', '')[:54]}")

    print(f"Cohesion audit -- {path.name}")
    print(f"  {len(tasks)} activities, {len(preds)} ties, {len(milestones)} milestones")

    dump("ORPHANS -- no predecessor", no_pred)
    dump("ORPHANS -- no successor", no_succ)
    dump("DEAD-END -- forward chain never reaches a milestone", dead_end)
    dump("RIDING project-start milestone as only predecessor (review)", riding)

    hard = len(no_pred) + len(no_succ) + len(dead_end)
    print()
    if hard:
        print(f"=== NOT COHESIVE -- {hard} orphan/dead-end issue(s) to fix "
              f"({len(riding)} riding-start to review) ===")
        sys.exit(1)
    print(f"=== COHESIVE -- no orphans, every chain reaches a milestone "
          f"({len(riding)} riding-start to review) ===")
    sys.exit(0)


if __name__ == "__main__":
    main()
