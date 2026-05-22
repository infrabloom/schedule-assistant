#!/usr/bin/env python3
"""
review_changeset.py - the Change-Set Impact Preview, for the approver.

Dry-runs a change-set and assembles ONE packet so the approver can decide
BEFORE anything is committed:

  1. what the change-set does          (dry-run patch)
  2. independent verification          (diff == change-set, nothing else)
  3. MILESTONE IMPACT                  (predict_milestones, update vs base)
  4. validation                        (no new issues vs base)
  -> VERDICT: safe to approve, or review needed

Nothing is committed: the patched XER is staged under previews/ and the
CHANGELOG is untouched. On approval, run apply_changeset.py (no --preview)
to commit, then import to OPC and run F9.

This orchestrator calls each pipeline script with --json and consumes its
structured result and exit code - it never scrapes prose (review item 6.6).

Usage:
  review_changeset.py <changeset> --xer-dir <dir> [--validators-dir <dir>]
  review_changeset.py <changeset> --xer-dir <dir> --json

With --json, a single JSON object is written to stdout and the human packet is
routed to stderr.

Exit codes:
  0  SAFE TO APPROVE
  1  REVIEW NEEDED (verification failed, milestone regression, or new issue)
  2  usage error / a sub-script could not run
"""
import sys, os, json, subprocess, argparse

try:
    import yaml
except ImportError:
    sys.stderr.write("ERROR: PyYAML is required.  Install it with: pip install pyyaml\n")
    sys.exit(2)

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable


def run_json(cmd):
    """Run a pipeline script with --json appended. Return (rc, data|None,
    stderr). `data` is the parsed JSON object the script printed on stdout,
    or None if it produced none (a crash, or a stand-in that ignores --json)."""
    r = subprocess.run(cmd + ['--json'], capture_output=True, text=True)
    out = (r.stdout or '').strip()
    try:
        data = json.loads(out) if out else None
    except ValueError:                       # incl. json.JSONDecodeError
        data = None
    return r.returncode, data, (r.stderr or '')


def milestone_pattern(xer_dir, explicit):
    """Resolve the contract-milestone regex from project.yaml, if available.
    Returns the pattern string, or None to let predict_milestones use its
    generic default. Auto-discovers project.yaml one level above xer-dir
    unless --project-config gives an explicit path."""
    cfg = explicit
    if not cfg:
        guess = os.path.join(os.path.dirname(os.path.abspath(xer_dir)),
                             'project.yaml')
        cfg = guess if os.path.exists(guess) else None
    if not cfg or not os.path.exists(cfg):
        return None
    try:
        doc = yaml.safe_load(open(cfg, encoding='utf-8')) or {}
        return (doc.get('milestones') or {}).get('contract_pattern') or None
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('changeset')
    ap.add_argument('--xer-dir', required=True)
    ap.add_argument('--validators-dir',
                    default=os.path.join(SCRIPTS, '..', 'skills',
                                         'data-center-schedule', 'scripts'),
                    help='dir with validate_xer.py (default: the bundled skill)')
    ap.add_argument('--project-config', default=None,
                    help='path to project.yaml (default: auto-discover beside '
                         'the project folder)')
    ap.add_argument('--json', action='store_true',
                    help='emit a machine-readable JSON result on stdout '
                         '(the human packet goes to stderr)')
    args = ap.parse_args()

    # In --json mode the human packet runs onto stderr; stdout carries only JSON.
    if args.json:
        sys.stdout = sys.stderr

    review = {'script': 'review_changeset', 'changeset': None, 'ok': False,
              'verdict': None, 'verified': None, 'regression': None,
              'new_validation_issue': None, 'apply': None, 'verify': None,
              'milestones': None, 'error': None}

    def finish(code):
        if args.json:
            sys.stdout = sys.__stdout__
            print(json.dumps(review))
        sys.exit(code)

    cs = yaml.safe_load(open(args.changeset, encoding='utf-8'))['changeset']
    review['changeset'] = cs.get('id')
    base = os.path.join(args.xer_dir, cs['base_xer'])
    staged = os.path.join(args.xer_dir, 'previews', cs['update_xer'])

    bar = '=' * 70
    print(bar)
    print(f"  CHANGE-SET IMPACT PREVIEW   {cs['id']}  -  {cs.get('title', '')}")
    print(bar)
    print(f"  base        : {cs['base_xer']}")
    print(f"  update      : {cs['update_xer']}   (staged - not committed)")
    print(f"  requested by: {cs.get('requested_by', '-')}")
    print(f"  summary     : {cs.get('summary', '').strip()}")

    # 1 -- dry-run patch (apply_changeset --preview) --------------------------
    apply_cmd = [PY, f'{SCRIPTS}/apply_changeset.py', args.changeset,
                 '--xer-dir', args.xer_dir, '--preview']
    if args.validators_dir is not None:
        apply_cmd += ['--validators-dir', args.validators_dir]
    rc_a, data_a, err_a = run_json(apply_cmd)
    review['apply'] = data_a
    print("\n  1. WHAT IT CHANGES " + '-' * 49)
    if rc_a != 0 or not data_a:
        msg = ((data_a or {}).get('error') or err_a.strip()
               or f"apply_changeset exited {rc_a}")
        print('  ' + msg.replace('\n', '\n  '))
        print("\n  VERDICT: change-set could not be applied - REVISE before approval.")
        review['verdict'] = 'REVIEW_NEEDED'
        review['error'] = msg
        finish(1 if rc_a == 1 else 2)
    for op in data_a.get('operations', []):
        print(f"     [{op['id']}] {op['op']}: {op['result']}")
    if data_a.get('output_path'):
        print(f"     staged -> {os.path.basename(data_a['output_path'])}")

    # 2 -- independent verification ------------------------------------------
    rc_v, data_v, err_v = run_json([PY, f'{SCRIPTS}/verify_changeset.py',
                                    args.changeset, '--xer-dir', args.xer_dir,
                                    '--update-xer', staged])
    review['verify'] = data_v
    print("\n  2. INDEPENDENT VERIFICATION " + '-' * 40)
    verified = (rc_v == 0) and bool(data_v) and data_v.get('ok', False)
    if data_v:
        d = data_v.get('diff', {})
        print(f"     actual diff: {d.get('rel_modified', 0)} rel modified, "
              f"{d.get('rel_added', 0)} rel added, "
              f"{d.get('rel_removed', 0)} rel removed, "
              f"{d.get('task_added', 0)} task added, "
              f"{d.get('task_removed', 0)} task removed, "
              f"{d.get('task_modified', 0)} task modified")
        for fl in data_v.get('flags', []):
            print(f"     FLAG  - {fl}")
        if verified:
            print("     PASSED - diff equals the change-set, nothing else")
        else:
            problems = data_v.get('problems', [])
            print(f"     FAILED - {len(problems)} discrepancy(ies):")
            for p in problems:
                print(f"       X {p}")
    else:
        print(f"     (no JSON result - verify_changeset exited {rc_v})")
        if err_v.strip():
            print('  ' + err_v.strip().replace('\n', '\n  '))

    # 3 -- milestone impact --------------------------------------------------
    pcmd = [PY, f'{SCRIPTS}/predict_milestones.py', staged, '--compare', base]
    ms_pat = milestone_pattern(args.xer_dir, args.project_config)
    if ms_pat:
        pcmd += ['--milestone-pattern', ms_pat]
    rc_p, data_p, err_p = run_json(pcmd)
    review['milestones'] = data_p
    print("\n  3. MILESTONE IMPACT " + '-' * 48)
    if data_p:
        regression = bool(data_p.get('regression'))
        rows = data_p.get('milestones', [])
        print(f"     {len(rows)} contract milestone(s); "
              f"data date {data_p.get('data_date')}")
        for m in rows:
            mv = m.get('move_days')
            mvtxt = ((f"{mv:+d}d" + (' !' if mv > 0 else ''))
                     if mv is not None else '-')
            print(f"     {m['code']:16} base {str(m.get('base')):12} "
                  f"-> predicted {str(m.get('predicted')):12}  move {mvtxt}")
        if regression:
            print(f"     REGRESSION: {data_p.get('regression_count')} "
                  f"milestone(s) moved later than the base schedule.")
        else:
            print("     no regression - no milestone moved later than base.")
    else:
        print(f"     (no JSON result - predict_milestones exited {rc_p})")
        if err_p.strip():
            print('  ' + err_p.strip().replace('\n', '\n  '))
        regression = (rc_p == 1)

    # 4 -- validation vs base (from apply's base-relative gate) ---------------
    print("\n  4. VALIDATION " + '-' * 54)
    val = data_a.get('validation', {}) or {}
    regressions = val.get('regressions', [])
    new_issue = bool(regressions)
    base_c, upd_c = val.get('base', {}) or {}, val.get('update', {}) or {}
    if not base_c and not upd_c:
        print("     (no validators configured)")
    else:
        for s in sorted(set(base_c) | set(upd_c)):
            print(f"     {s}: base {base_c.get(s, 0)} -> update {upd_c.get(s, 0)}")
        for s, n in val.get('preexisting', []):
            print(f"     pre-existing (not introduced here): {s} = {n}")
        if new_issue:
            print(f"     NEW ISSUE - this change-set ADDS validation issue(s): "
                  f"{', '.join(regressions)}")
        else:
            print("     no new validation issues vs base")

    # verdict ----------------------------------------------------------------
    ok = verified and not regression and not new_issue
    review['verified'] = verified
    review['regression'] = regression
    review['new_validation_issue'] = new_issue
    review['ok'] = ok
    review['verdict'] = 'SAFE_TO_APPROVE' if ok else 'REVIEW_NEEDED'
    print('\n' + bar)
    if ok:
        print("  VERDICT: SAFE TO APPROVE")
        print("           verified - diff equals the change-set, nothing else")
        print("           no milestone regression, no new validation issues")
    else:
        print("  VERDICT: REVIEW NEEDED")
        if not verified:
            print("           - verification FAILED (see section 2)")
        if regression:
            print("           - milestone REGRESSION - a milestone moved later (section 3)")
        if new_issue:
            print("           - validation: change-set ADDS issue(s) (section 4)")
    print("\n  To commit after approval:")
    print(f"    apply_changeset.py {os.path.basename(args.changeset)} --xer-dir <dir>")
    print(f"    then import {cs['update_xer']} into OPC and run F9.")
    print(bar)
    finish(0 if ok else 1)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"ABORTED - {type(e).__name__}: {e}\n")
        sys.exit(2)
