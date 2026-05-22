#!/usr/bin/env python3
"""
predict_milestones.py - milestone CPM pre-check for the schedule pipeline.

A lightweight critical-path forecast: a forward pass that computes early dates
from logic + durations + actuals + the data date, then reports each contract
milestone's predicted finish against its contract date. Optionally compares two
schedules to show the milestone movement a change introduces - the regression
check to run before an update_xer goes to OPC.

This is the 'lightweight' tier. `cpm_forward_pass()` has a deliberately clean
interface so a fuller forward+backward float/critical-path engine can replace it
later without touching the milestone reporting.

It does NOT replace OPC's scheduler - OPC stays authoritative. This is an
in-house early-warning net that catches big milestone regressions before import.

Durations are advanced in CALENDAR days, not working days - the forward pass is
calendar-agnostic. On a 7-day activity calendar (the data-center default) the two
coincide; on a 5-day or holiday-bearing calendar the forecast runs optimistic.
Treat it as a relative regression check - trust the movement column, not the
absolute dates.

Usage:
  predict_milestones.py <xer>                    forecast one schedule
  predict_milestones.py <xer> --compare <base>   forecast + movement vs base
  predict_milestones.py <xer> --data-date YYYY-MM-DD   override the data date
  predict_milestones.py <xer> --compare <base> --json  machine-readable result

With --json, a single JSON object is written to stdout and the human report is
routed to stderr.

Exit codes:
  0  no milestone regression (or a plain forecast with no --compare)
  1  at least one milestone moved later than the base schedule (--compare mode)
  2  usage error / unreadable XER
"""
import sys, json, argparse, re
from datetime import date, datetime, timedelta
from collections import defaultdict, deque
from xer_io import parse_rows   # one shared XER parser - see scripts/xer_io.py

def pdate(s):
    s = (s or '').strip()
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], '%Y-%m-%d').date()
    except ValueError:
        return None

RT = {'PR_FS': 'FS', 'PR_SS': 'SS', 'PR_FF': 'FF', 'PR_SF': 'SF'}

# ---------------------------------------------------------------- CPM core
def cpm_forward_pass(activities, links, data_date):
    """Forward-pass CPM.  Clean interface - a fuller engine can replace this.

    activities : {code: {status, dur, rem, act_start, act_end, cstr_type, cstr_date}}
                 dur / rem in working days; dates are date objects or None.
    links      : {succ_code: [(pred_code, 'FS'|'SS'|'FF'|'SF', lag_days), ...]}
    returns    : {code: {'ES': date, 'EF': date, 'driver': pred_code or None}}
    """
    indeg = defaultdict(int)
    adj = defaultdict(list)
    for succ, ps in links.items():
        for pred, _t, _l in ps:
            if pred in activities:
                adj[pred].append(succ); indeg[succ] += 1
    q = deque([c for c in activities if indeg[c] == 0])
    topo = []
    while q:
        n = q.popleft(); topo.append(n)
        for m in adj[n]:
            indeg[m] -= 1
            if indeg[m] == 0:
                q.append(m)
    if len(topo) != len(activities):           # cycle - fall back to arbitrary order
        topo = list(activities)

    res = {}
    for c in topo:
        a = activities[c]
        st = a['status']
        if st == 'TK_Complete':
            es = a['act_start'] or data_date
            ef = a['act_end'] or es
            res[c] = {'ES': es, 'EF': ef, 'driver': None}
            continue
        if st == 'TK_Active':
            es = a['act_start'] or data_date
            ef = data_date + timedelta(days=a['rem'])
            res[c] = {'ES': es, 'EF': ef, 'driver': None}
            continue
        # TK_NotStart
        es = data_date; driver = None
        for pred, typ, lag in links.get(c, []):
            if pred not in res:
                continue
            pe, pf = res[pred]['ES'], res[pred]['EF']
            if typ == 'FS':
                cand = pf + timedelta(days=lag)
            elif typ == 'SS':
                cand = pe + timedelta(days=lag)
            elif typ == 'FF':
                cand = pf + timedelta(days=lag - a['dur'])
            elif typ == 'SF':
                cand = pe + timedelta(days=lag - a['dur'])
            else:
                cand = es
            if cand > es:
                es = cand; driver = pred
        if a['cstr_type'] == 'CS_MSOA' and a['cstr_date'] and a['cstr_date'] > es:
            es = a['cstr_date']; driver = '[CS_MSOA]'
        ef = es + timedelta(days=a['dur'])
        if a['cstr_type'] == 'CS_MEOA' and a['cstr_date'] and a['cstr_date'] > ef:
            ef = a['cstr_date']
        res[c] = {'ES': es, 'EF': ef, 'driver': driver}
    return res

# ---------------------------------------------------------------- load
def load(path, data_date_override=None):
    tab = parse_rows(path)
    proj = tab['PROJECT'][0]
    data_date = data_date_override or pdate(proj.get('last_recalc_date')) \
        or pdate(proj.get('plan_start_date')) or date.today()
    T = tab['TASK']
    id2code = {r['task_id']: r['task_code'] for r in T}
    activities = {}
    for r in T:
        activities[r['task_code']] = {
            'status': r.get('status_code', 'TK_NotStart'),
            'type': r.get('task_type', ''),
            'name': r.get('task_name', ''),
            'dur': round(float(r.get('target_drtn_hr_cnt') or 0) / 8),
            'rem': round(float(r.get('remain_drtn_hr_cnt') or 0) / 8),
            'act_start': pdate(r.get('act_start_date')),
            'act_end': pdate(r.get('act_end_date')),
            'cstr_type': r.get('cstr_type', ''),
            'cstr_date': pdate(r.get('cstr_date')),
        }
    links = defaultdict(list)
    for r in tab['TASKPRED']:
        p = id2code.get(r['pred_task_id']); s = id2code.get(r['task_id'])
        if p and s:
            try:
                lag = float(r.get('lag_hr_cnt') or 0) / 8
            except ValueError:
                lag = 0
            links[s].append((p, RT.get(r.get('pred_type', ''), 'FS'), lag))
    return activities, dict(links), data_date

# Generic default: any milestone-type activity whose code carries a recognised
# contract-milestone token, bounded by separators. A project with a different
# milestone-naming convention overrides this via project.yaml's
# `milestones.contract_pattern` - review_changeset.py forwards it as
# --milestone-pattern (see docs/project-schema.md). Not project-specific.
DEFAULT_MILESTONE_PATTERN = r'(?:^|[-_.])(EFA|FA|FR|RFS|MEC|TCO|PCO)(?:[-_.]|$)'

def contract_milestones(activities, pattern):
    rx = re.compile(pattern)
    return sorted(c for c, a in activities.items()
                  if rx.search(c) and 'Mile' in a['type'])

# ---------------------------------------------------------------- report
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('xer')
    ap.add_argument('--compare', default=None, help='base XER to measure movement against')
    ap.add_argument('--data-date', default=None)
    ap.add_argument('--milestone-pattern', default=DEFAULT_MILESTONE_PATTERN,
                    help='regex identifying contract-milestone task codes '
                         '(default: the generic EFA/FA/FR/RFS/MEC/TCO/PCO set; '
                         'a project overrides it via project.yaml)')
    ap.add_argument('--json', action='store_true',
                    help='emit a machine-readable JSON result on stdout '
                         '(the human report goes to stderr)')
    args = ap.parse_args()
    dd_override = pdate(args.data_date) if args.data_date else None

    # In --json mode the human report runs onto stderr; stdout carries only JSON.
    if args.json:
        sys.stdout = sys.stderr

    acts, links, dd = load(args.xer, dd_override)
    res = cpm_forward_pass(acts, links, dd)
    ms = contract_milestones(acts, args.milestone_pattern)
    print(f"== predict_milestones :: {args.xer.split('/')[-1]} ==")
    print(f"   data date: {dd}   contract milestones: {len(ms)}")

    base_res = None
    if args.compare:
        b_acts, b_links, b_dd = load(args.compare, dd_override)
        base_res = cpm_forward_pass(b_acts, b_links, b_dd)
        print(f"   compared against: {args.compare.split('/')[-1]}")
        print(f"\n   {'Milestone':16} {'Contract':12} {'Base':12} {'Predicted':12} "
              f"{'Move':>6} {'vs Contract':>12}")
    else:
        print(f"\n   {'Milestone':16} {'Contract':12} {'Predicted':12} {'vs Contract':>12}")

    late = regress = 0
    ms_rows = []
    for m in ms:
        cd = acts[m]['cstr_date']
        pf = res.get(m, {}).get('EF')
        var = (pf - cd).days if (pf and cd) else None
        vtxt = (f"{var:+d}d" if var is not None else '-')
        if var is not None and var > 0:
            late += 1
        bf = mv = None
        if base_res is not None:
            bf = base_res.get(m, {}).get('EF')
            mv = (pf - bf).days if (pf and bf) else None
            mvtxt = (f"{mv:+d}d" if mv is not None else '-')
            if mv is not None and mv > 0:
                regress += 1
                mvtxt += ' !'
            print(f"   {m:16} {str(cd):12} {str(bf):12} {str(pf):12} {mvtxt:>6} {vtxt:>12}")
        else:
            print(f"   {m:16} {str(cd):12} {str(pf):12} {vtxt:>12}")
        ms_rows.append({
            'code': m,
            'contract': str(cd) if cd else None,
            'predicted': str(pf) if pf else None,
            'base': str(bf) if bf else None,
            'move_days': mv,
            'vs_contract_days': var,
        })

    print()
    print(f"   {late} of {len(ms)} milestone(s) predicted past contract date.")
    if base_res is not None:
        if regress:
            print(f"   REGRESSION: {regress} milestone(s) moved LATER than the base "
                  f"schedule (marked !). Review before importing to OPC.")
        else:
            print("   No regression: no milestone moved later than the base schedule.")
    print("\n   Note: forward-pass forecast - OPC's scheduler (F9) remains authoritative.")
    print("   Durations count calendar days; on a non-7-day calendar treat the dates "
          "as approximate and read the movement column.")

    result = {
        'script': 'predict_milestones',
        'xer': args.xer.split('/')[-1],
        'data_date': str(dd),
        'compared_against': args.compare.split('/')[-1] if args.compare else None,
        'contract_milestone_count': len(ms),
        'milestones': ms_rows,
        'late_count': late,
        'regression_count': regress,
        'regression': bool(base_res is not None and regress),
    }
    if args.json:
        sys.stdout = sys.__stdout__
        print(json.dumps(result))
    sys.exit(1 if result['regression'] else 0)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"ABORTED - {type(e).__name__}: {e}\n")
        sys.exit(2)
