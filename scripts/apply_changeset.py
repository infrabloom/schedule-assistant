#!/usr/bin/env python3
"""
apply_changeset.py - apply an approved change-set (YAML) to an XER file.

Pipeline:  load base_xer -> apply operations in memory (expect-guarded)
           -> stage to a temp file -> validate -> commit via atomic rename
           -> append CHANGELOG.  Aborts cleanly, with nothing committed, on any
           error (bad YAML, expect-mismatch, validation failure).

This file is the CLI and the commit orchestration only. The XER parser/writer
lives in `xer_io.py`; the operation engine (Ctx + the op_* functions + OPS)
lives in `operations.py`. Activity-code operations are not yet implemented.

See docs/changeset-schema.md (v1.5).

Usage:
    apply_changeset.py <changeset.yaml> --xer-dir <dir> [--validators-dir <dir>]
    apply_changeset.py <changeset.yaml> --xer-dir <dir> --json

With --json, a single JSON object is written to stdout and the human report is
routed to stderr.

Exit codes:
    0  committed (or preview staged) with no change-set-introduced issues
    1  blocked: change-set rejected (PatchError) or it ADDS validation issues
    2  usage error / bad change-set file / IO error
"""
import sys, os, json, shutil, datetime, subprocess, argparse

try:
    import yaml
except ImportError:
    sys.stderr.write("ERROR: PyYAML is required.  Install it with: pip install pyyaml\n")
    sys.exit(2)

from xer_io import parse_xer, write_xer
from operations import Ctx, OPS, DEFERRED, PatchError

# ----------------------------------------------------------------------
# changelog
# ----------------------------------------------------------------------
def append_changelog(changelog_path, cs, results):
    if not os.path.exists(changelog_path):
        return "CHANGELOG.md not found - skipped"
    ver = cs['update_xer'].rsplit('.', 1)[0].split('-')[-1]
    lines = [f"## {ver} - {cs['update_xer']} - {datetime.date.today()}",
             f"**Change-set:** {cs['id']} - **Type:** pipeline - "
             f"**Requested by:** {cs.get('requested_by','-')}",
             f"**Trigger:** {cs.get('trigger','').strip()}", "",
             "| Operation | Result | Source |", "|---|---|---|"]
    for opdef, res in results:
        lines.append(f"| {opdef['op']} ({opdef['id']}) | {res} | "
                     f"{opdef['source'].strip().splitlines()[0]} |")
    lines += ["", "---"]
    entry = '\n'.join(lines)
    txt = open(changelog_path, encoding='utf-8').read()
    marker = '<!-- ENTRIES -->'
    if marker in txt:
        txt = txt.replace(marker, marker + '\n\n' + entry, 1)
    else:
        txt = txt.rstrip() + '\n\n' + entry + '\n'
    open(changelog_path, 'w', encoding='utf-8').write(txt)
    return f"appended {ver} entry to CHANGELOG.md"

# ----------------------------------------------------------------------
# validation gate
# ----------------------------------------------------------------------
# Default validators live in the bundled skill - one source of truth.
SKILL_SCRIPTS = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', 'skills', 'data-center-schedule', 'scripts'))

def run_validators(vdir, xer_path, label):
    """Run the bundled validators on xer_path in --json mode. Print one human
    line per validator. Return {script_name: issue_count}. Reads the validator's
    structured JSON result rather than scraping its prose (review item 6.6)."""
    counts = {}
    if not vdir:
        print(f"   validators ({label}): none configured - SKIPPED")
        return counts
    found = False
    for script in ('validate_xer.py', 'duplicate_audit.py'):
        sp = os.path.join(vdir, script)
        if not os.path.exists(sp):
            continue
        found = True
        r = subprocess.run([sys.executable, sp, xer_path, '--json'],
                           capture_output=True, text=True)
        try:
            data = json.loads((r.stdout or '').strip())
        except ValueError:                       # incl. json.JSONDecodeError
            data = None
        if data is None:
            # no JSON on stdout - a crash, or a stand-in that ignores --json.
            counts[script] = 0 if r.returncode == 0 else 1
            print(f"   {script} ({label}): "
                  + ('clean' if counts[script] == 0
                     else 'non-zero exit (no JSON result)'))
        else:
            counts[script] = int(data.get('issue_count',
                                          0 if data.get('ok') else 1))
            print(f"   {script} ({label}): "
                  + ('clean' if counts[script] == 0
                     else f"{counts[script]} issue(s)"))
    if not found:
        print(f"   validators ({label}): not found in {vdir} - SKIPPED")
    return counts

# ----------------------------------------------------------------------
# main
# ----------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('changeset')
    ap.add_argument('--xer-dir', required=True)
    ap.add_argument('--validators-dir', default=SKILL_SCRIPTS,
                    help='dir with validate_xer.py + duplicate_audit.py '
                         '(default: the bundled data-center-schedule skill)')
    ap.add_argument('--preview', action='store_true',
                    help='dry run: stage update_xer under previews/, skip the changelog')
    ap.add_argument('--json', action='store_true',
                    help='emit a machine-readable JSON result on stdout '
                         '(the human report goes to stderr)')
    args = ap.parse_args()

    # In --json mode the human report runs onto stderr; stdout carries only JSON.
    if args.json:
        sys.stdout = sys.stderr

    result = {'script': 'apply_changeset', 'changeset': None,
              'preview': args.preview, 'ok': False, 'committed': False,
              'aborted': False, 'update_xer': None, 'output_path': None,
              'operations': [], 'validation': {}, 'message': None, 'error': None}

    def finish(code):
        if args.json:
            sys.stdout = sys.__stdout__
            print(json.dumps(result))
        sys.exit(code)

    def fail(code, msg):
        """Record the abort, print the human line to stderr, emit JSON, exit."""
        result['aborted'] = True
        result['error'] = msg
        print(msg, file=sys.stderr)
        finish(code)

    cs_doc = yaml.safe_load(open(args.changeset, encoding='utf-8'))
    if not isinstance(cs_doc, dict) or 'changeset' not in cs_doc or 'changes' not in cs_doc:
        fail(2, "ERROR: change-set file must have top-level 'changeset:' and "
                "'changes:' keys")
    cs = cs_doc['changeset']; changes = cs_doc['changes']
    if not isinstance(changes, list):
        fail(2, "ERROR: 'changes:' must be a list of operations")
    if isinstance(cs, dict):
        result['changeset'] = cs.get('id')

    # header validation
    for f in ('id', 'base_xer', 'update_xer', 'data_date', 'prepared', 'author',
              'trigger', 'summary'):
        if not cs.get(f):
            fail(2, f"ERROR: change-set header missing required field: {f}")
    for c in changes:
        for f in ('id', 'op', 'reason', 'source'):
            if not c.get(f):
                fail(2, f"ERROR: operation {c.get('id','?')} missing required field: {f}")
        if c['op'] in DEFERRED:
            fail(2, f"ERROR: operation {c['op']} ({c['id']}) is not yet implemented "
                    f"(activity-code operations are planned but not built)")
        if c['op'] not in OPS:
            fail(2, f"ERROR: unknown operation: {c['op']}")

    result['update_xer'] = cs['update_xer']
    base = os.path.join(args.xer_dir, cs['base_xer'])
    if args.preview:
        prevdir = os.path.join(args.xer_dir, 'previews')
        os.makedirs(prevdir, exist_ok=True)
        update = os.path.join(prevdir, cs['update_xer'])
    else:
        update = os.path.join(args.xer_dir, cs['update_xer'])
    if not os.path.exists(base):
        fail(2, f"ERROR: base_xer not found: {base}")
    if os.path.abspath(base) == os.path.abspath(update):
        fail(2, "ERROR: update_xer must differ from base_xer")

    print(f"== apply_changeset :: {cs['id']} =="
          + ("   [PREVIEW - dry run, not committed]" if args.preview else ""))
    print(f"   base   : {cs['base_xer']}")
    print(f"   update : {cs['update_xer']}")

    ermhdr, tables, base_newline = parse_xer(base)
    ctx = Ctx(tables)
    P0 = ctx.tbl['PROJECT']
    print(f"   project: {P0.g(P0.rows[0], 'proj_short_name')}  "
          f"(Project ID - preserved unchanged from base_xer)")

    # apply atomically (all in memory; abort before any write on error)
    results = []
    try:
        for c in changes:
            res = OPS[c['op']](c, ctx)
            results.append((c, res))
            result['operations'].append({'id': c['id'], 'op': c['op'],
                                         'result': res})
            print(f"   [{c['id']}] {c['op']}: {res}")
    except PatchError as e:
        fail(1, f"ABORTED - {e}\n   No file written; base_xer untouched.")

    # stage: write to a temp file in the destination directory, validate it,
    # and commit only via an atomic rename.  Nothing is ever half-applied.
    tmp = update + '.tmp'
    try:
        write_xer(ermhdr, tables, tmp, newline=base_newline)
    except Exception as e:
        if os.path.exists(tmp):
            os.remove(tmp)
        fail(2, f"ABORTED - could not write staged XER: {e}\n"
                f"   Nothing committed; base_xer untouched.")
    print(f"   staged : {os.path.basename(tmp)}  (validating before commit)")

    # validation gate -- base-relative: block only on issue(s) this change-set
    # ADDS versus base_xer. Pre-existing issues are reported, never blocked.
    base_counts = run_validators(args.validators_dir, base, 'base')
    upd_counts = run_validators(args.validators_dir, tmp, 'update')
    regressions = [s for s, n in upd_counts.items()
                   if n > base_counts.get(s, 0)]
    preexisting = [(s, base_counts[s]) for s in sorted(base_counts)
                   if base_counts[s] > 0 and s not in regressions]
    result['validation'] = {'base': base_counts, 'update': upd_counts,
                            'regressions': regressions,
                            'preexisting': [[s, n] for s, n in preexisting]}
    if preexisting:
        print("   note   : pre-existing validation issue(s) NOT introduced by "
              "this change-set -")
        for s, n in preexisting:
            print(f"            {s}: {n} (carried over from base_xer)")
        print("            fix these in a separate schedule-cleanup pass.")
    if regressions:
        det = '; '.join(f"{s} {base_counts.get(s, 0)} -> {upd_counts[s]}"
                        for s in regressions)
        if args.preview:
            print(f"   WARNING: this change-set ADDS validation issue(s): {det}")
            result['message'] = f"preview: change-set ADDS validation issue(s): {det}"
        else:
            os.remove(tmp)
            fail(1, f"ABORTED - this change-set ADDS validation issue(s): {det}.\n"
                    f"   Change-set NOT committed; base_xer untouched. "
                    f"Fix the change-set and re-run.")

    # commit -- back up base_xer, then atomically rename temp -> update_xer
    if not args.preview:
        ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        bak = base + f'.bak-{ts}'
        shutil.copy2(base, bak)
        print(f"   backup : {os.path.basename(bak)}")
    os.replace(tmp, update)
    result['output_path'] = update
    print(f"   wrote  : {os.path.relpath(update, args.xer_dir)}")

    # changelog (commit only - never on a preview)
    if args.preview:
        print("== preview done ==  (staged under previews/ - nothing committed)")
        result['message'] = result['message'] or \
            'preview done - staged under previews/, nothing committed'
    else:
        cl = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(args.changeset))),
                          'CHANGELOG.md')
        try:
            print(f"   {append_changelog(cl, cs, results)}")
        except Exception as e:
            print(f"   WARNING: CHANGELOG append failed ({e}) - update_xer is "
                  f"committed; add the entry by hand.")
        print("== done ==  (update_xer is import-ready but NOT yet scheduled - run F9 in OPC)")
        result['committed'] = True
        result['message'] = 'committed - update_xer is import-ready'

    result['ok'] = True
    finish(0)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"ABORTED - {type(e).__name__}: {e}\n")
        sys.exit(2)
