#!/usr/bin/env python3
"""
verify_changeset.py - independent verification for the schedule pipeline.

Confirms that update_xer differs from base_xer by EXACTLY the operations in the
change-set - nothing more, nothing less. It re-derives the ACTUAL diff from the
two XERs independently; the EXPECTED diff comes from the shared per-operation
registry in operations.py. Exits non-zero on any discrepancy to gate the pipeline.

Checks:
  * every actual change is explained by a change-set operation
  * every change-set operation is reflected in the actual diff
  * PROJECT is unchanged (the Project ID must carry through untouched)
  * flags any newly-created cross-DH relationship (consolidation caveat, schema 2.7)

Usage:
    verify_changeset.py <changeset.yaml> --xer-dir <dir>
    verify_changeset.py <changeset.yaml> --xer-dir <dir> --json

With --json, a single JSON object is written to stdout and the human report is
routed to stderr.

Exit codes:
    0  update_xer differs from base_xer by exactly the change-set
    1  one or more verification discrepancies
    2  usage error / file not found
"""
import sys, os, json, argparse, fnmatch, re

try:
    import yaml
except ImportError:
    sys.stderr.write("ERROR: PyYAML is required.  Install it with: pip install pyyaml\n")
    sys.exit(2)

from xer_io import parse_rows     # one shared XER parser - see scripts/xer_io.py
from operations import EXPECTED   # per-op expected-diff registry - see operations.py

def dh(code):
    m = re.search(r'DH(\d)', code or '')
    return m.group(1) if m else None

# ---------------------------------------------------------------- diff
def index(tables):
    T = tables['TASK']
    id2code = {r['task_id']: r['task_code'] for r in T}
    code2row = {r['task_code']: r for r in T}
    preds = {}
    for r in tables['TASKPRED']:
        p = id2code.get(r['pred_task_id']); s = id2code.get(r['task_id'])
        if p and s:
            preds[(p, s)] = (r.get('pred_type', ''), r.get('lag_hr_cnt', '0') or '0')
    wbs = {r['wbs_id']: r for r in tables['PROJWBS']}
    proj = tables['PROJECT'][0]
    return dict(code2row=code2row, preds=preds, wbs=wbs, proj=proj)

def diff(base, upd):
    d = {}
    # tasks (keyed by task_code)
    bc, uc = set(base['code2row']), set(upd['code2row'])
    d['task_added'] = uc - bc
    d['task_removed'] = bc - uc
    d['task_modified'] = {}
    for c in bc & uc:
        b, u = base['code2row'][c], upd['code2row'][c]
        chg = {k for k in u if k != 'task_id' and b.get(k, '') != u.get(k, '')}
        if chg:
            d['task_modified'][c] = chg
    # relationships (keyed by code pair)
    bp, up = set(base['preds']), set(upd['preds'])
    d['rel_added'] = up - bp
    d['rel_removed'] = bp - up
    d['rel_modified'] = {k: (base['preds'][k], upd['preds'][k])
                         for k in bp & up if base['preds'][k] != upd['preds'][k]}
    # wbs (keyed by wbs_id)
    bw, uw = set(base['wbs']), set(upd['wbs'])
    d['wbs_added'] = uw - bw
    d['wbs_removed'] = bw - uw
    d['wbs_modified'] = {}
    for w in bw & uw:
        b, u = base['wbs'][w], upd['wbs'][w]
        chg = {k for k in u if b.get(k, '') != u.get(k, '')}
        if chg:
            d['wbs_modified'][w] = chg
    # project
    d['proj_changed'] = {k: (base['proj'].get(k, ''), upd['proj'].get(k, ''))
                         for k in upd['proj']
                         if base['proj'].get(k, '') != upd['proj'].get(k, '')}
    return d

# ---------------------------------------------------------------- expected
def expected(changes, base):
    """The diff the change-set SHOULD produce. Computed from the shared
    per-operation registry in operations.py - the same definitions the patcher
    uses - so the verifier cannot drift from apply_changeset.py."""
    e = dict(rel_modified={}, rel_added=set(), rel_removed=set(),
             task_added=set(), task_removed=set(), task_modified={},
             wbs_added=set(), wbs_modified=set(), wbs_removed=set())
    for op in changes:
        fn = EXPECTED.get(op['op'])
        if fn:
            fn(op, base, e)
    return e

# ---------------------------------------------------------------- compare
def verify(changes, base, upd):
    d = diff(base, upd)
    e = expected(changes, base)
    problems = []; flags = []

    # relationships --------------------------------------------------
    if set(d['rel_modified']) != set(e['rel_modified']):
        for r in set(d['rel_modified']) - set(e['rel_modified']):
            problems.append(f"UNEXPLAINED relationship change: {r[0]} -> {r[1]}")
        for r in set(e['rel_modified']) - set(d['rel_modified']):
            problems.append(f"MISSING relationship change (change-set says modify): {r[0]} -> {r[1]}")
    for r, exp in e['rel_modified'].items():
        if r in d['rel_modified'] and d['rel_modified'][r][1] != exp:
            problems.append(f"relationship {r[0]}->{r[1]} set to "
                            f"{d['rel_modified'][r][1]}, change-set expected {exp}")
    if d['rel_added'] != e['rel_added']:
        for r in d['rel_added'] - e['rel_added']:
            problems.append(f"UNEXPLAINED relationship added: {r[0]} -> {r[1]}")
        for r in e['rel_added'] - d['rel_added']:
            problems.append(f"MISSING relationship (change-set says add): {r[0]} -> {r[1]}")
    if d['rel_removed'] != e['rel_removed']:
        for r in d['rel_removed'] - e['rel_removed']:
            problems.append(f"UNEXPLAINED relationship removed: {r[0]} -> {r[1]}")
        for r in e['rel_removed'] - d['rel_removed']:
            problems.append(f"MISSING removal (change-set says remove): {r[0]} -> {r[1]}")

    # tasks ----------------------------------------------------------
    if d['task_added'] != e['task_added']:
        for c in d['task_added'] - e['task_added']:
            problems.append(f"UNEXPLAINED activity added: {c}")
        for c in e['task_added'] - d['task_added']:
            problems.append(f"MISSING activity (change-set says add): {c}")
    if d['task_removed'] != e['task_removed']:
        for c in d['task_removed'] - e['task_removed']:
            problems.append(f"UNEXPLAINED activity removed: {c}")
        for c in e['task_removed'] - d['task_removed']:
            problems.append(f"MISSING removal (change-set says remove): {c}")
    for c, cols in d['task_modified'].items():
        if c not in e['task_modified']:
            problems.append(f"UNEXPLAINED activity change: {c} (fields: {', '.join(sorted(cols))})")
        else:
            extra = cols - e['task_modified'][c]
            if extra:
                problems.append(f"activity {c} changed unexpected field(s): {', '.join(sorted(extra))}")

    # wbs ------------------------------------------------------------
    if len(d['wbs_added']) != len(e['wbs_added']):
        problems.append(f"WBS added count {len(d['wbs_added'])} != change-set {len(e['wbs_added'])}")
    if len(d['wbs_removed']) != len(e['wbs_removed']):
        problems.append(f"WBS removed count {len(d['wbs_removed'])} != change-set {len(e['wbs_removed'])}")
    if d['wbs_modified'] and not e['wbs_modified']:
        problems.append(f"UNEXPLAINED WBS change(s): {len(d['wbs_modified'])} node(s)")

    # project --------------------------------------------------------
    for k, (o, n) in d['proj_changed'].items():
        problems.append(f"UNEXPLAINED PROJECT change: {k}  {o!r} -> {n!r}  "
                        f"(Project ID / settings must carry through untouched)")

    # judgment flag: new cross-DH relationships ----------------------
    for (p, s) in d['rel_added']:
        if dh(p) and dh(s) and dh(p) != dh(s):
            flags.append(f"cross-DH relationship created: DH{dh(p)} {p} -> DH{dh(s)} {s} "
                         f"(review per consolidation caveat)")
    return d, problems, flags

# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('changeset')
    ap.add_argument('--xer-dir', required=True)
    ap.add_argument('--update-xer', default=None,
                    help='explicit path to the update XER (overrides xer-dir/update_xer)')
    ap.add_argument('--json', action='store_true',
                    help='emit a machine-readable JSON result on stdout '
                         '(the human report goes to stderr)')
    args = ap.parse_args()

    # In --json mode the human report runs onto stderr; stdout carries only JSON.
    if args.json:
        sys.stdout = sys.stderr

    def finish(code, result):
        if args.json:
            sys.stdout = sys.__stdout__
            print(json.dumps(result))
        sys.exit(code)

    doc = yaml.safe_load(open(args.changeset, encoding='utf-8'))
    cs, changes = doc['changeset'], doc['changes']
    base_p = os.path.join(args.xer_dir, cs['base_xer'])
    upd_p = args.update_xer or os.path.join(args.xer_dir, cs['update_xer'])
    for p in (base_p, upd_p):
        if not os.path.exists(p):
            print(f"ERROR: not found: {p}", file=sys.stderr)
            finish(2, {'script': 'verify_changeset', 'changeset': cs.get('id'),
                       'ok': False, 'error': f'not found: {p}'})

    print(f"== verify_changeset :: {cs['id']} ==")
    print(f"   base   : {cs['base_xer']}")
    print(f"   update : {cs['update_xer']}")
    print(f"   change-set operations: {len(changes)}")

    base = index(parse_rows(base_p))
    upd = index(parse_rows(upd_p))
    d, problems, flags = verify(changes, base, upd)

    print(f"\n   actual diff: {len(d['rel_modified'])} rel modified, "
          f"{len(d['rel_added'])} rel added, {len(d['rel_removed'])} rel removed, "
          f"{len(d['task_added'])} task added, {len(d['task_removed'])} task removed, "
          f"{len(d['task_modified'])} task modified, "
          f"{len(d['proj_changed'])} project field(s) changed")

    result = {
        'script': 'verify_changeset',
        'changeset': cs['id'],
        'ok': not problems,
        'diff': {
            'rel_modified': len(d['rel_modified']),
            'rel_added': len(d['rel_added']),
            'rel_removed': len(d['rel_removed']),
            'task_added': len(d['task_added']),
            'task_removed': len(d['task_removed']),
            'task_modified': len(d['task_modified']),
            'project_fields_changed': len(d['proj_changed']),
        },
        'problems': problems,
        'flags': flags,
    }

    for f in flags:
        print(f"   FLAG  - {f}")
    if problems:
        print(f"\n   VERIFICATION FAILED - {len(problems)} discrepancy(ies):")
        for p in problems:
            print(f"     X {p}")
        finish(1, result)
    print("\n   VERIFICATION PASSED - update_xer differs from base_xer by exactly "
          "the change-set" + (" (see FLAGs above for review items)" if flags else ", nothing else."))
    finish(0, result)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"ABORTED - {type(e).__name__}: {e}\n")
        sys.exit(2)
