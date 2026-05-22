#!/usr/bin/env python3
"""
validate_xer.py -- Comprehensive P6 / Oracle Primavera Cloud (OPC) XER validator.

ONE consolidated validator for the data-center-schedule skill. It merges the
logic-integrity checks (orphans, cycles, forward-chain-to-milestone, aref/arls)
with the OPC-schema checks (case-insensitive code collisions, duration_type,
midnight timestamps, proj_id) so a single run catches every failure mode found
during the CB4 schedule rebuild.

This file REPLACES the former validate_xer.py + validate_xer_v2.py pair. Those
two did not compose into a complete gate -- v2 added the schema checks but
silently dropped orphans / cycles / chain-to-milestone / aref-arls. Run this and
nothing falls through the crack between them.

Usage:
    python validate_xer.py path/to/Schedule.xer
    python validate_xer.py path/to/Schedule.xer --json

With --json, a single machine-readable JSON object is written to stdout and the
human-readable report is routed to stderr. Pipeline scripts consume the JSON.

Exit codes:
    0  all FAIL-level checks pass (warnings are allowed)
    1  one or more FAIL-level checks failed
    2  usage error / file not found

FAIL checks (block OPC import or corrupt the schedule):
    1  bare CS_MEO / CS_MSO constraint codes (OPC silently drops the constraint)
    2  TK_Active without act_start_date
    3  TK_Complete without act_start_date or act_end_date
    4  TK_NotStart with actuals populated
    5  phys_complete_pct / remain_drtn_hr_cnt / status_code inconsistent
    6  duplicate task_code (exact)
    7  duplicate task_code (CASE-INSENSITIVE -- OPC matches codes case-insensitively)
    8  duplicate GUID
    9  GUID not in 22-char standard-base64 form (urlsafe -/_ is rejected by OPC)
    10 duration_type does not match task_type
    11 midnight (00:00) timestamp in a date field (OPC rejects it)
    12 task proj_id does not match the PROJECT row's proj_id
    13 orphan activity (no predecessor, or no successor)
    14 forward chain never reaches a milestone (dead-end logic)
    15 TASKPRED references a non-existent task_id / pred_task_id (dangling tie)
    16 TASKPRED row missing aref or arls
    17 predecessor type not PR_FS / PR_SS / PR_FF
    18 circular dependency (cycle) in TASKPRED
    19 WBS branch with a missing parent, or WBS depth over the OPC limit (10)
    20 task references a non-existent / empty wbs_id
    21 task references a non-existent calendar

WARN checks (worth a look, never blocking):
    W1 constraint code outside {CS_MEOA, CS_MEOB, CS_MSOA}
    W2 contract milestone with no constraint and no predecessor (floating)
    W3 activities whose only predecessor is a project-start milestone
    W4 no PROJECT.proj_id -- task proj_id consistency cannot be checked
    W5 no milestone activities found -- chain-to-milestone check skipped
    W6 more than one PROJECT row in the file
    W7 PR_SF (start-to-finish) relationship in use -- legal but discouraged
"""

import sys
import re
import json
import argparse
import collections
from pathlib import Path

CONSTRAINT_ALLOW = {"", "CS_MEOA", "CS_MEOB", "CS_MSOA"}
CONSTRAINT_KILLERS = {"CS_MEO", "CS_MSO"}
MILESTONE_TYPES = {"TT_Mile", "TT_FinMile"}
PRED_TYPES_OK = {"PR_FS", "PR_SS", "PR_FF"}
CONTRACT_TOKENS = ("EFA", "FA", "FR", "RFS", "MEC", "TCO", "PCO", "COMPL")
GUID_RE = re.compile(r"^[A-Za-z0-9+/]{22}$")
MIDNIGHT_RE = re.compile(r"\d{4}-\d{2}-\d{2}\s+00:00(?::00)?\b")
DATE_FIELDS = ("act_start_date", "act_end_date", "cstr_date", "cstr_date2",
               "early_start_date", "early_end_date", "late_start_date",
               "late_end_date", "target_start_date", "target_end_date",
               "expect_end_date", "restart_date", "reend_date",
               "rem_late_start_date", "rem_late_end_date")


def parse_xer(path):
    """Parse an XER file into {table_name: list[dict]}."""
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
    ap = argparse.ArgumentParser(
        description="Comprehensive P6 / OPC XER validator "
                    "(21 FAIL checks + 7 WARN checks).")
    ap.add_argument("xer", help="path to the XER file to validate")
    ap.add_argument("--json", action="store_true",
                    help="emit a machine-readable JSON result on stdout "
                         "(the human report goes to stderr)")
    args = ap.parse_args()

    path = Path(args.xer)
    if not path.exists():
        if args.json:
            print(json.dumps({"script": "validate_xer", "xer": str(path),
                              "ok": False, "error": "file not found"}))
        else:
            print(f"File not found: {path}", file=sys.stderr)
        sys.exit(2)

    # In --json mode the human report still runs, but onto stderr; stdout is
    # reserved for the single JSON object emitted by finish().
    if args.json:
        sys.stdout = sys.stderr

    def finish(code, result):
        if args.json:
            sys.stdout = sys.__stdout__
            print(json.dumps(result))
        sys.exit(code)

    t = parse_xer(path)
    tasks = t.get("TASK", [])
    preds = t.get("TASKPRED", [])
    wbs = t.get("PROJWBS", [])
    cals = t.get("CALENDAR", [])
    proj = (t.get("PROJECT") or [{}])[0]

    FAIL, WARN, OKL = [], [], []
    fail = lambda n, m: FAIL.append((n, m))
    warn = lambda n, m: WARN.append((n, m))
    okl = lambda n, m: OKL.append((n, m))

    print(f"Validating {path.name}")
    print(f"  TASK={len(tasks)}  TASKPRED={len(preds)}  "
          f"PROJWBS={len(wbs)}  CALENDAR={len(cals)}\n")

    if not tasks:
        print("=== FAILED -- no TASK rows found (not an XER, or empty) ===")
        finish(1, {"script": "validate_xer", "xer": path.name, "ok": False,
                   "error": "no TASK rows found (not an XER, or empty)",
                   "issue_count": 1})

    id_to_code = {r.get("task_id"): r.get("task_code", "") for r in tasks}
    id_set = set(id_to_code)
    codes = [r.get("task_code", "") for r in tasks]

    # --- pred / succ maps (built once, reused) -------------------------------
    succ_of = collections.defaultdict(list)
    pred_of = collections.defaultdict(list)
    has_pred, has_succ = collections.defaultdict(int), collections.defaultdict(int)
    for p in preds:
        sid, pid = p.get("task_id"), p.get("pred_task_id")
        if sid in id_set and pid in id_set:
            succ_of[pid].append(sid)
            pred_of[sid].append(pid)
        if sid in id_set:
            has_pred[sid] += 1
        if pid in id_set:
            has_succ[pid] += 1

    def is_start_ms(r):
        c = r.get("task_code", "").upper()
        return (r.get("task_type") in MILESTONE_TYPES
                and any(k in c for k in ("SWD", "START", "NTP")))

    def is_end_ms(r):
        c = r.get("task_code", "").upper()
        return (r.get("task_type") in MILESTONE_TYPES
                and any(k in c for k in ("RFS", "PCO", "COMPL", "TCO")))

    # --- 1. constraint codes -------------------------------------------------
    killers = [r.get("task_code") for r in tasks
               if r.get("cstr_type", "").strip() in CONSTRAINT_KILLERS
               or r.get("cstr_type2", "").strip() in CONSTRAINT_KILLERS]
    if killers:
        fail(1, f"{len(killers)} task(s) use bare CS_MEO/CS_MSO -- OPC silently "
                f"drops the constraint: {killers[:5]}")
    else:
        okl(1, "no bare CS_MEO / CS_MSO constraint codes")
    odd = sorted({r.get("cstr_type", "").strip() for r in tasks
                  if r.get("cstr_type", "").strip() not in CONSTRAINT_ALLOW
                  and r.get("cstr_type", "").strip() not in CONSTRAINT_KILLERS})
    if odd:
        warn("W1", f"constraint codes outside CS_MEOA/MEOB/MSOA in use: {odd}")

    # --- 2-5. status / actuals / pct consistency -----------------------------
    c2, c3a, c3b, c4, c5 = [], [], [], [], []
    for r in tasks:
        s = r.get("status_code", "")
        as_ = r.get("act_start_date", "").strip()
        ae = r.get("act_end_date", "").strip()
        cd = r.get("task_code")
        if s == "TK_Active" and not as_:
            c2.append(cd)
        if s == "TK_Complete":
            if not as_:
                c3a.append(cd)
            if not ae:
                c3b.append(cd)
        if s == "TK_NotStart" and (as_ or ae):
            c4.append(cd)
        try:
            pct = float(r.get("phys_complete_pct", "0") or 0)
            rem = float(r.get("remain_drtn_hr_cnt", "0") or 0)
        except ValueError:
            pct = None
        if pct is not None:
            if pct >= 99.9 and (rem > 0.01 or s != "TK_Complete"):
                c5.append(cd)
            elif s == "TK_Complete" and rem > 0.01:
                c5.append(cd)
            elif s == "TK_NotStart" and pct > 0.01:
                c5.append(cd)
    if c2:
        fail(2, f"{len(c2)} TK_Active task(s) with no act_start_date: {c2[:5]}")
    else:
        okl(2, "every TK_Active has act_start_date")
    if c3a or c3b:
        fail(3, f"TK_Complete missing actuals -- {len(c3a)} no act_start, "
                f"{len(c3b)} no act_end: {(c3a + c3b)[:5]}")
    else:
        okl(3, "every TK_Complete has act_start + act_end")
    if c4:
        fail(4, f"{len(c4)} TK_NotStart task(s) with actuals populated: {c4[:5]}")
    else:
        okl(4, "no TK_NotStart task carries actuals")
    if c5:
        fail(5, f"{len(c5)} task(s) with inconsistent pct/remain/status: {c5[:5]}")
    else:
        okl(5, "phys_complete_pct / remain / status consistent")

    # --- 6. exact duplicate codes -------------------------------------------
    dup6 = [c for c, n in collections.Counter(codes).items() if c and n > 1]
    if dup6:
        fail(6, f"duplicate task_code (exact): {dup6[:5]}")
    else:
        okl(6, f"{len(codes)} task_codes unique (exact match)")

    # --- 7. case-insensitive duplicate codes (the CB4 389-drop bug) ----------
    ci = collections.Counter(c.lower() for c in codes if c)
    ci_dups = [k for k, n in ci.items() if n > 1]
    if ci_dups:
        shown = []
        for k in ci_dups[:5]:
            variants = sorted({c for c in codes if c.lower() == k})
            shown.append("/".join(variants))
        fail(7, f"{len(ci_dups)} case-insensitive duplicate task_code(s) -- OPC "
                f"matches codes case-insensitively and rejects the file: {shown}")
    else:
        okl(7, "task_codes unique case-insensitively")

    # --- 8-9. GUIDs ----------------------------------------------------------
    guids = [r.get("guid", "").strip() for r in tasks if r.get("guid", "").strip()]
    dup8 = [g for g, n in collections.Counter(guids).items() if n > 1]
    if dup8:
        fail(8, f"duplicate GUID(s): {dup8[:3]}")
    else:
        okl(8, f"{len(guids)} GUIDs unique")
    bad9 = [r.get("task_code") for r in tasks
            if r.get("guid", "").strip() and not GUID_RE.match(r.get("guid", "").strip())]
    if bad9:
        fail(9, f"{len(bad9)} GUID(s) not 22-char standard base64 "
                f"(urlsafe -/_ rejected by OPC): {bad9[:3]}")
    else:
        okl(9, "all GUIDs in 22-char standard-base64 form")

    # --- 10. duration_type vs task_type -------------------------------------
    bad10 = []
    for r in tasks:
        tt, dt = r.get("task_type", ""), r.get("duration_type", "")
        if tt in MILESTONE_TYPES and dt and dt not in ("DT_FixedDrtn", "DT_FixedDUR2"):
            bad10.append(f"{r.get('task_code')}({tt}/{dt})")
    if bad10:
        fail(10, f"{len(bad10)} milestone(s) with a duration_type that does not "
                 f"match task_type (silent drop on import): {bad10[:3]}")
    else:
        okl(10, "duration_type consistent with task_type")

    # --- 11. midnight timestamps --------------------------------------------
    mids = []
    for r in tasks:
        for f in DATE_FIELDS:
            v = r.get(f, "")
            if v and MIDNIGHT_RE.search(v):
                mids.append(f"{r.get('task_code')}.{f}")
    if mids:
        fail(11, f"{len(mids)} midnight (00:00) timestamp(s) -- OPC rejects them, "
                 f"use 08:00 / 16:00: {mids[:3]}")
    else:
        okl(11, "no midnight (00:00) timestamps")

    # --- 12. proj_id consistency --------------------------------------------
    proj_ids = {p.get("proj_id", "").strip() for p in t.get("PROJECT", [])
                if p.get("proj_id", "").strip()}
    if proj_ids:
        bad12 = [r.get("task_code") for r in tasks
                 if r.get("proj_id", "").strip()
                 and r.get("proj_id") not in proj_ids]
        if bad12:
            fail(12, f"{len(bad12)} task(s) with a proj_id matching no PROJECT row "
                     f"{sorted(proj_ids)}: {bad12[:3]}")
        else:
            okl(12, f"all tasks reference a valid PROJECT proj_id {sorted(proj_ids)}")
        if len(proj_ids) > 1:
            warn("W6", f"XER contains {len(proj_ids)} PROJECT rows -- a single "
                       f"deliverable schedule should contain one project")
    else:
        warn("W4", "no PROJECT.proj_id -- cannot check task proj_id consistency")

    # --- 13. orphans ---------------------------------------------------------
    np = [r.get("task_code") for r in tasks
          if not has_pred.get(r.get("task_id")) and not is_start_ms(r)]
    ns = [r.get("task_code") for r in tasks
          if not has_succ.get(r.get("task_id")) and not is_end_ms(r)]
    if np:
        fail(13, f"{len(np)} activity(ies) with NO predecessor: {np[:5]}")
    if ns:
        fail(13, f"{len(ns)} activity(ies) with NO successor: {ns[:5]}")
    if not np and not ns:
        okl(13, "no orphans -- every activity has a predecessor and a successor")

    # --- 14. forward chain reaches a milestone (reverse BFS, no recursion) ---
    milestones = {r.get("task_id") for r in tasks
                  if r.get("task_type") in MILESTONE_TYPES
                  or r.get("task_code", "").upper().startswith(("MS-", "MS_", "MS."))}
    if not milestones:
        warn("W5", "no milestone activities found -- skipping chain-to-milestone check")
    else:
        reaches = set(milestones)
        dq = collections.deque(milestones)
        while dq:
            n = dq.popleft()
            for p in pred_of.get(n, ()):
                if p not in reaches:
                    reaches.add(p)
                    dq.append(p)
        dead = [id_to_code[i] for i in id_set if i not in reaches]
        if dead:
            fail(14, f"{len(dead)} activity(ies) whose forward chain never reaches "
                     f"a milestone: {dead[:5]}")
        else:
            okl(14, f"every activity's forward chain reaches a milestone "
                    f"({len(milestones)} milestones)")

    # --- 15. dangling TASKPRED references -----------------------------------
    dangling = []
    for p in preds:
        if p.get("task_id") not in id_set:
            dangling.append(f"task_id={p.get('task_id')}")
        if p.get("pred_task_id") not in id_set:
            dangling.append(f"pred_task_id={p.get('pred_task_id')}")
    if dangling:
        fail(15, f"{len(dangling)} TASKPRED reference(s) to a non-existent task "
                 f"(dangling tie, or stray cross-project pred): {dangling[:4]}")
    else:
        okl(15, "all TASKPRED rows reference existing tasks")

    # --- 16. aref / arls -----------------------------------------------------
    miss16 = sum(1 for p in preds
                 if not p.get("aref", "").strip() or not p.get("arls", "").strip())
    if miss16:
        fail(16, f"{miss16} TASKPRED row(s) missing aref or arls")
    else:
        okl(16, f"all {len(preds)} TASKPRED rows have aref + arls")

    # --- 17. predecessor types ----------------------------------------------
    sf17 = sum(1 for p in preds if p.get("pred_type", "") == "PR_SF")
    bad17 = collections.Counter(p.get("pred_type", "") for p in preds
                                if p.get("pred_type", "") not in PRED_TYPES_OK
                                and p.get("pred_type", "") != "PR_SF")
    if bad17:
        fail(17, f"invalid predecessor type(s): {dict(bad17)}")
    else:
        okl(17, "all predecessor types are PR_FS / PR_SS / PR_FF"
                + (" / PR_SF" if sf17 else ""))
    if sf17:
        warn("W7", f"{sf17} PR_SF (start-to-finish) tie(s) -- legal but discouraged; "
                   f"confirm the logic is intentional")

    # --- 18. cycles (iterative DFS, safe on large graphs) -------------------
    WHITE, GRAY, BLACK = 0, 1, 2
    color = dict.fromkeys(id_set, WHITE)
    cyc = None
    for s0 in id_set:
        if color[s0] != WHITE or cyc:
            continue
        stack = [(s0, 0)]
        dfs_path = []
        while stack and not cyc:
            node, idx = stack[-1]
            if idx == 0:
                color[node] = GRAY
                dfs_path.append(node)
            kids = succ_of.get(node, [])
            if idx < len(kids):
                stack[-1] = (node, idx + 1)
                nxt = kids[idx]
                if color[nxt] == WHITE:
                    stack.append((nxt, 0))
                elif color[nxt] == GRAY:
                    j = dfs_path.index(nxt)
                    cyc = [id_to_code[x] for x in dfs_path[j:]] + [id_to_code[nxt]]
            else:
                color[node] = BLACK
                dfs_path.pop()
                stack.pop()
    if cyc:
        fail(18, f"circular dependency: {' -> '.join(cyc)}")
    else:
        okl(18, "no cycles")

    # --- 19. WBS hierarchy + depth ------------------------------------------
    wbs_ids = {w.get("wbs_id") for w in wbs}
    by_id = {w.get("wbs_id"): w for w in wbs}
    orphan_wbs = [w.get("wbs_short_name") or w.get("wbs_id") for w in wbs
                  if w.get("parent_wbs_id", "").strip()
                  and w.get("parent_wbs_id") not in wbs_ids]

    def wdepth(wid):
        d, cur, seen = 0, wid, set()
        while cur and cur in by_id and cur not in seen:
            seen.add(cur)
            par = by_id[cur].get("parent_wbs_id", "").strip()
            if not par:
                break
            d += 1
            cur = par
        return d
    maxd = max((wdepth(w.get("wbs_id")) for w in wbs), default=0)
    if orphan_wbs:
        fail(19, f"{len(orphan_wbs)} WBS branch(es) with a missing parent: "
                 f"{orphan_wbs[:3]}")
    if maxd > 10:
        fail(19, f"WBS depth {maxd} exceeds the OPC limit of 10")
    if not orphan_wbs and maxd <= 10:
        okl(19, f"WBS hierarchy valid (max depth {maxd})")

    # --- 20. wbs_id references ----------------------------------------------
    empty_wbs = [r.get("task_code") for r in tasks if not r.get("wbs_id", "").strip()]
    bad_wbs = [r.get("task_code") for r in tasks
               if r.get("wbs_id", "").strip() and r.get("wbs_id") not in wbs_ids]
    if empty_wbs:
        fail(20, f"{len(empty_wbs)} task(s) with an empty wbs_id: {empty_wbs[:3]}")
    if bad_wbs:
        fail(20, f"{len(bad_wbs)} task(s) reference a non-existent wbs_id: "
                 f"{bad_wbs[:3]}")
    if not empty_wbs and not bad_wbs:
        okl(20, "all tasks reference a valid WBS")

    # --- 21. calendar references --------------------------------------------
    cal_ids = {c.get("clndr_id") for c in cals}
    bad21 = [r.get("task_code") for r in tasks
             if r.get("clndr_id", "").strip() and r.get("clndr_id") not in cal_ids]
    if bad21:
        fail(21, f"{len(bad21)} task(s) reference a non-existent calendar: {bad21[:3]}")
    else:
        okl(21, f"all tasks reference a valid calendar ({len(cal_ids)} defined)")

    # --- W2. floating contract milestones -----------------------------------
    for r in tasks:
        if r.get("task_type") in MILESTONE_TYPES:
            c = r.get("task_code", "").upper()
            if any(tok in c for tok in CONTRACT_TOKENS):
                if not r.get("cstr_type", "").strip() and not has_pred.get(r.get("task_id")):
                    warn("W2", f"{r.get('task_code')}: contract milestone with no "
                               f"constraint and no predecessor (floating)")

    # --- W3. activities riding a project-start milestone --------------------
    start_ids = {r.get("task_id") for r in tasks if is_start_ms(r)}
    riding = [r.get("task_code") for r in tasks
              if r.get("task_type") not in MILESTONE_TYPES
              and pred_of.get(r.get("task_id"))
              and all(p in start_ids for p in pred_of.get(r.get("task_id")))]
    if riding:
        warn("W3", f"{len(riding)} activity(ies) ride a project-start milestone as "
                   f"their only predecessor -- confirm intentional: {riding[:5]}")

    # --- report --------------------------------------------------------------
    print("Checks:")
    for n, m in OKL:
        print(f"  [{str(n):>3}] OK    {m}")
    for n, m in WARN:
        print(f"  [{str(n):>3}] WARN  {m}")
    print()
    result = {
        "script": "validate_xer",
        "xer": path.name,
        "ok": not FAIL,
        "counts": {"task": len(tasks), "taskpred": len(preds),
                   "projwbs": len(wbs), "calendar": len(cals)},
        "fail": [{"check": str(n), "message": m} for n, m in FAIL],
        "warn": [{"check": str(n), "message": m} for n, m in WARN],
        "passed_checks": len(OKL),
        "issue_count": len(FAIL),
    }
    if FAIL:
        print(f"=== FAILED -- {len(FAIL)} issue(s) ===")
        for n, m in FAIL[:60]:
            print(f"  [FAIL {n}] {m}")
        if len(FAIL) > 60:
            print(f"  ... and {len(FAIL) - 60} more")
        if WARN:
            print(f"  ({len(WARN)} warning(s) listed above)")
        finish(1, result)
    else:
        tail = f"  ({len(WARN)} warning(s))" if WARN else ""
        print(f"=== ALL {len(OKL)} HARD CHECKS PASSED -- XER ready for OPC import ==={tail}")
        finish(0, result)


if __name__ == "__main__":
    main()
