#!/usr/bin/env python3
"""
operations.py - the change-set engine for the schedule pipeline.

Holds the operation context (`Ctx`), the ten change-set operations, and the
`OPS` dispatch table. This is the single definition of what each operation
does; `apply_changeset.py` imports and runs it, and the verifier reads the same
registry (EXPECTED, below) so the patcher and the verifier cannot drift.

Operates on the in-memory tables produced by `xer_io.parse_xer`. Pure logic -
no file or process I/O. Raises `PatchError` on any logical problem so the
caller can abort the whole change-set cleanly.
"""
import base64
import fnmatch
import uuid


class PatchError(Exception):
    pass

# ----------------------------------------------------------------------
# enum maps
# ----------------------------------------------------------------------
RTYPE = {'FS': 'PR_FS', 'SS': 'PR_SS', 'FF': 'PR_FF', 'SF': 'PR_SF'}
STATUS = {'NotStarted': 'TK_NotStart', 'InProgress': 'TK_Active', 'Complete': 'TK_Complete'}
CSTR = {'MSOA': 'CS_MSOA', 'MEOA': 'CS_MEOA', 'MEOB': 'CS_MEOB'}

# ----------------------------------------------------------------------
# context
# ----------------------------------------------------------------------
class Ctx:
    def __init__(self, tables):
        self.tbl = {t.name: t for t in tables}
        T = self.tbl['TASK']
        self.code2id = {T.g(r, 'task_code'): T.g(r, 'task_id') for r in T.rows}
        self.id2code = {v: k for k, v in self.code2id.items()}
        self.proj_id = self.tbl['PROJECT'].g(self.tbl['PROJECT'].rows[0], 'proj_id')
        self.max_task_id = max(int(T.g(r, 'task_id')) for r in T.rows)
        TP = self.tbl['TASKPRED']
        self.max_pred_id = max(int(TP.g(r, 'task_pred_id')) for r in TP.rows)
        W = self.tbl['PROJWBS']
        self.max_wbs_id = max(int(W.g(r, 'wbs_id')) for r in W.rows)
        self._wbs_path = self._build_wbs_paths(W)
    def _build_wbs_paths(self, W):
        by = {W.g(r, 'wbs_id'): r for r in W.rows}
        paths = {}
        for r in W.rows:
            names = []; cur = r; root = None
            while cur is not None:
                pid = W.g(cur, 'parent_wbs_id')
                if pid in by:
                    names.append(W.g(cur, 'wbs_name')); cur = by[pid]
                else:
                    root = cur; cur = None
            paths[' > '.join(reversed(names))] = W.g(r, 'wbs_id')
        return paths
    def new_task_id(self): self.max_task_id += 1; return str(self.max_task_id)
    def new_pred_id(self): self.max_pred_id += 1; return str(self.max_pred_id)
    def new_wbs_id(self): self.max_wbs_id += 1; return str(self.max_wbs_id)
    def wbs_id(self, ref):
        if ref in self._wbs_path: return self._wbs_path[ref]
        # fall back: match by short name
        W = self.tbl['PROJWBS']
        for r in W.rows:
            if W.g(r, 'wbs_short_name') == ref: return W.g(r, 'wbs_id')
        raise PatchError(f"WBS not found: {ref!r}")

# ----------------------------------------------------------------------
# relationship helpers
# ----------------------------------------------------------------------
def resolve_rels(op, ctx):
    """Return list of (pred_code, succ_code) from explicit list or `match:`."""
    if 'relationships' in op:
        return [(r['predecessor'], r['successor']) for r in op['relationships']]
    if 'match' in op:
        m = op['match']; TP = ctx.tbl['TASKPRED']; out = []
        for r in TP.rows:
            p = ctx.id2code.get(TP.g(r, 'pred_task_id'))
            s = ctx.id2code.get(TP.g(r, 'task_id'))
            if p and s and fnmatch.fnmatch(p, m['predecessor']) and fnmatch.fnmatch(s, m['successor']):
                out.append((p, s))
        return out
    raise PatchError("relationship op needs `relationships:` or `match:`")

def find_pred_row(ctx, pcode, scode):
    pid = ctx.code2id.get(pcode); sid = ctx.code2id.get(scode)
    if not pid: raise PatchError(f"unknown predecessor activity: {pcode}")
    if not sid: raise PatchError(f"unknown successor activity: {scode}")
    TP = ctx.tbl['TASKPRED']
    for r in TP.rows:
        if TP.g(r, 'pred_task_id') == pid and TP.g(r, 'task_id') == sid:
            return r
    return None

# ----------------------------------------------------------------------
# operations
# ----------------------------------------------------------------------
def op_modify_relationship(op, ctx):
    TP = ctx.tbl['TASKPRED']
    new_t = RTYPE[op['set']['type']]
    # round, never truncate - int() would silently drop a fractional-day lag
    new_lag = str(round(op['set'].get('lag_days', 0) * 8))
    exp = op.get('expect')
    rels = resolve_rels(op, ctx); n = 0
    for pcode, scode in rels:
        row = find_pred_row(ctx, pcode, scode)
        if row is None:
            raise PatchError(f"relationship not found: {pcode} -> {scode}")
        if exp:
            ct = TP.g(row, 'pred_type'); cl = float(TP.g(row, 'lag_hr_cnt') or 0)
            if ct != RTYPE[exp['type']] or cl != exp.get('lag_days', 0) * 8:
                raise PatchError(
                    f"expect mismatch on {pcode}->{scode}: "
                    f"have {ct}/{cl/8:g}d, expected {RTYPE[exp['type']]}/{exp.get('lag_days',0)}d")
        TP.s(row, 'pred_type', new_t); TP.s(row, 'lag_hr_cnt', new_lag)
        n += 1
    return f"retied {n} relationship(s) -> {op['set']['type']}+{op['set'].get('lag_days',0)}d"

def op_add_relationship(op, ctx):
    TP = ctx.tbl['TASKPRED']; n = 0
    for r in op['relationships']:
        pid = ctx.code2id.get(r['predecessor']); sid = ctx.code2id.get(r['successor'])
        if not pid or not sid:
            raise PatchError(f"unknown activity in add_relationship: {r}")
        if find_pred_row(ctx, r['predecessor'], r['successor']) is not None:
            raise PatchError(f"relationship already exists: {r['predecessor']} -> {r['successor']}")
        row = [''] * len(TP.cols)
        vals = {'task_pred_id': ctx.new_pred_id(), 'task_id': sid, 'pred_task_id': pid,
                'proj_id': ctx.proj_id, 'pred_proj_id': ctx.proj_id,
                'pred_type': RTYPE[r.get('type', 'FS')],
                'lag_hr_cnt': str(round(r.get('lag_days', 0) * 8))}
        for k, v in vals.items(): TP.s(row, k, v)
        TP.rows.append(row); n += 1
    return f"added {n} relationship(s)"

def op_remove_relationship(op, ctx):
    TP = ctx.tbl['TASKPRED']
    exp = op.get('expect')
    rels = set(resolve_rels(op, ctx)); drop = []
    for row in TP.rows:
        p = ctx.id2code.get(TP.g(row, 'pred_task_id'))
        s = ctx.id2code.get(TP.g(row, 'task_id'))
        if (p, s) in rels:
            if exp:
                ct = TP.g(row, 'pred_type'); cl = float(TP.g(row, 'lag_hr_cnt') or 0)
                if ct != RTYPE[exp['type']] or cl != exp.get('lag_days', 0) * 8:
                    raise PatchError(f"expect mismatch removing {p}->{s}")
            drop.append(row)
    if not drop:
        raise PatchError(f"no relationships matched for removal: {sorted(rels)}")
    for row in drop: TP.rows.remove(row)
    return f"removed {len(drop)} relationship(s)"

def _new_guid():
    """A fresh P6-style GUID: 22 chars of standard base64 (the form
    validate_xer.py check 9 accepts), generated from a random UUID. A real P6
    export gives every activity a GUID; a blank one trips the validator."""
    return base64.b64encode(uuid.uuid4().bytes).decode('ascii').rstrip('=')


def _template_row(ctx, status_code):
    T = ctx.tbl['TASK']
    for r in T.rows:
        if T.g(r, 'status_code') == status_code:
            return list(r) + [''] * (len(T.cols) - len(r))
    return list(T.rows[0]) + [''] * (len(T.cols) - len(T.rows[0]))

def _apply_activity_fields(T, row, ctx, a, *, creating):
    if 'code' in a: T.s(row, 'task_code', a['code'])
    if 'name' in a: T.s(row, 'task_name', a['name'])
    if 'wbs' in a: T.s(row, 'wbs_id', ctx.wbs_id(a['wbs']))
    if 'type' in a:
        T.s(row, 'task_type', 'TT_Mile' if a['type'] == 'Milestone' else 'TT_Task')
    if 'status' in a: T.s(row, 'status_code', STATUS[a['status']])
    # round, never truncate - int() would silently drop fractional days
    if 'duration_days' in a:
        T.s(row, 'target_drtn_hr_cnt', str(round(a['duration_days'] * 8)) + '.0')
    if 'remain_duration_days' in a:
        T.s(row, 'remain_drtn_hr_cnt', str(round(a['remain_duration_days'] * 8)) + '.0')
    for k, col in [('actual_start', 'act_start_date'), ('actual_finish', 'act_end_date'),
                   ('target_start', 'target_start_date'), ('target_finish', 'target_end_date')]:
        if k in a:
            T.s(row, col, '' if a[k] in (None, 'null') else str(a[k]))
    if 'constraint' in a:
        c = a['constraint']
        if c in (None, 'null'):
            T.s(row, 'cstr_type', ''); T.s(row, 'cstr_date', '')
        else:
            T.s(row, 'cstr_type', CSTR[c['type']]); T.s(row, 'cstr_date', str(c['date']))
    if 'codes' in a and a['codes']:
        raise PatchError("activity-code assignment (`codes:`) is not yet implemented")

def op_add_activity(op, ctx):
    T = ctx.tbl['TASK']
    a = op['activity']
    if a['code'] in ctx.code2id:
        raise PatchError(f"activity code already exists: {a['code']}")
    if any(a['code'].lower() == c.lower() for c in ctx.code2id):
        raise PatchError(f"case-insensitive task_code collision: {a['code']}")
    status = STATUS.get(a.get('status', 'NotStarted'))
    row = _template_row(ctx, status)
    tid = ctx.new_task_id()
    T.s(row, 'task_id', tid); T.s(row, 'proj_id', ctx.proj_id)
    T.s(row, 'clndr_id', T.g(T.rows[0], 'clndr_id'))
    T.s(row, 'duration_type', 'DT_FixedDUR2')
    T.s(row, 'complete_pct_type', 'CP_Drtn')
    T.s(row, 'guid', _new_guid())
    # the row was cloned from a same-status template - scrub any actuals,
    # progress and constraint it inherited so the new activity starts clean.
    # The change-set can still set them explicitly via _apply_activity_fields
    # below, which runs after this and therefore wins.
    for col, blank in (('act_start_date', ''), ('act_end_date', ''),
                       ('phys_complete_pct', '0'),
                       ('cstr_type', ''), ('cstr_date', '')):
        if col in T.cols:
            T.s(row, col, blank)
    _apply_activity_fields(T, row, ctx, a, creating=True)
    T.rows.append(row)
    ctx.code2id[a['code']] = tid; ctx.id2code[tid] = a['code']
    extra = []
    for p in op.get('predecessors', []):
        extra.append({'predecessor': p['activity'], 'successor': a['code'],
                      'type': p.get('type', 'FS'), 'lag_days': p.get('lag_days', 0)})
    for s in op.get('successors', []):
        extra.append({'predecessor': a['code'], 'successor': s['activity'],
                      'type': s.get('type', 'FS'), 'lag_days': s.get('lag_days', 0)})
    if extra:
        op_add_relationship({'relationships': extra}, ctx)
    return f"added activity {a['code']} (+{len(extra)} ties)"

def op_modify_activity(op, ctx):
    T = ctx.tbl['TASK']
    tid = ctx.code2id.get(op['activity'])
    if not tid: raise PatchError(f"unknown activity: {op['activity']}")
    row = next(r for r in T.rows if T.g(r, 'task_id') == tid)
    exp = op.get('expect') or {}
    FIELD = {'name': 'task_name'}
    for k, v in exp.items():
        col = FIELD.get(k, k)
        if T.g(row, col) != str(v):
            raise PatchError(f"expect mismatch on {op['activity']}.{k}: "
                             f"have {T.g(row,col)!r}, expected {v!r}")
    _apply_activity_fields(T, row, ctx, op['set'], creating=False)
    return f"modified activity {op['activity']} ({', '.join(op['set'])})"

def op_split_activity(op, ctx):
    T = ctx.tbl['TASK']
    if op['original'] not in ctx.code2id:
        raise PatchError(f"unknown activity to split: {op['original']}")
    r1 = op_modify_activity({'activity': op['original'], 'set': op['modify_original'],
                             'expect': op.get('expect')}, ctx)
    na = dict(op['new_activity'])
    r2 = op_add_activity({'activity': na,
                          'predecessors': na.pop('predecessors', []),
                          'successors': na.pop('successors', [])}, ctx)
    return f"split {op['original']}: {r1}; {r2}"

def op_remove_activity(op, ctx):
    T = ctx.tbl['TASK']; TP = ctx.tbl['TASKPRED']
    tid = ctx.code2id.get(op['activity'])
    if not tid: raise PatchError(f"unknown activity: {op['activity']}")
    preds = [TP.g(r, 'pred_task_id') for r in TP.rows if TP.g(r, 'task_id') == tid]
    succs = [TP.g(r, 'task_id') for r in TP.rows if TP.g(r, 'pred_task_id') == tid]
    TP.rows = [r for r in TP.rows
               if TP.g(r, 'task_id') != tid and TP.g(r, 'pred_task_id') != tid]
    T.rows = [r for r in T.rows if T.g(r, 'task_id') != tid]
    n = 0
    if op.get('reroute'):
        for p in preds:
            for s in succs:
                row = [''] * len(TP.cols)
                for k, v in {'task_pred_id': ctx.new_pred_id(), 'task_id': s,
                             'pred_task_id': p, 'proj_id': ctx.proj_id,
                             'pred_proj_id': ctx.proj_id, 'pred_type': 'PR_FS',
                             'lag_hr_cnt': '0'}.items():
                    TP.s(row, k, v)
                TP.rows.append(row); n += 1
    del ctx.code2id[op['activity']]
    return f"removed activity {op['activity']} ({'rerouted '+str(n)+' ties' if op.get('reroute') else 'logic dropped'})"

def op_add_wbs(op, ctx):
    W = ctx.tbl['PROJWBS']
    w = op['wbs']
    parent_id = ctx.wbs_id(w['parent'])
    row = list(W.rows[0]) + [''] * (len(W.cols) - len(W.rows[0]))
    wid = ctx.new_wbs_id()
    for k, v in {'wbs_id': wid, 'proj_id': ctx.proj_id, 'parent_wbs_id': parent_id,
                 'wbs_short_name': w['code'], 'wbs_name': w['name'],
                 'proj_node_flag': 'N', 'status_code': 'WS_Open'}.items():
        if k in W.cols: W.s(row, k, v)
    W.rows.append(row)
    ctx._wbs_path[w['parent'] + ' > ' + w['name']] = wid
    return f"added WBS node {w['code']} {w['name']}"

def op_modify_wbs(op, ctx):
    W = ctx.tbl['PROJWBS']
    wid = ctx.wbs_id(op['wbs'])
    row = next(r for r in W.rows if W.g(r, 'wbs_id') == wid)
    exp = op.get('expect') or {}
    EF = {'code': 'wbs_short_name', 'name': 'wbs_name'}
    for k, v in exp.items():
        if W.g(row, EF.get(k, k)) != str(v):
            raise PatchError(f"expect mismatch on WBS {op['wbs']}.{k}")
    st = op['set']
    if 'code' in st: W.s(row, 'wbs_short_name', st['code'])
    if 'name' in st: W.s(row, 'wbs_name', st['name'])
    if 'parent' in st: W.s(row, 'parent_wbs_id', ctx.wbs_id(st['parent']))
    return f"modified WBS node {op['wbs']} ({', '.join(st)})"

def op_remove_wbs(op, ctx):
    W = ctx.tbl['PROJWBS']; T = ctx.tbl['TASK']
    wid = ctx.wbs_id(op['wbs'])
    if any(T.g(r, 'wbs_id') == wid for r in T.rows):
        raise PatchError(f"WBS {op['wbs']} still holds activities - cannot remove")
    if any(W.g(r, 'parent_wbs_id') == wid for r in W.rows):
        raise PatchError(f"WBS {op['wbs']} still has child nodes - cannot remove")
    W.rows = [r for r in W.rows if W.g(r, 'wbs_id') != wid]
    return f"removed WBS node {op['wbs']}"

OPS = {'modify_relationship': op_modify_relationship, 'add_relationship': op_add_relationship,
       'remove_relationship': op_remove_relationship, 'add_activity': op_add_activity,
       'modify_activity': op_modify_activity, 'split_activity': op_split_activity,
       'remove_activity': op_remove_activity, 'add_wbs': op_add_wbs,
       'modify_wbs': op_modify_wbs, 'remove_wbs': op_remove_wbs}
DEFERRED = {'define_activity_code', 'assign_activity_code', 'remove_activity_code'}

# ----------------------------------------------------------------------
# expected-diff registry  (the verifier side of each operation)
# ----------------------------------------------------------------------
# Each op_* above MUTATES the schedule; each expected_* below records the diff
# that operation SHOULD produce, so verify_changeset.py can confirm an
# update_xer differs from its base by exactly the change-set. Both registries
# live here, side by side, and the assert at the end keeps them in lockstep -
# the patcher and the verifier cannot drift.

AFIELD = {'name': 'task_name', 'code': 'task_code', 'wbs': 'wbs_id', 'calendar': 'clndr_id',
          'type': 'task_type', 'duration_days': 'target_drtn_hr_cnt',
          'remain_duration_days': 'remain_drtn_hr_cnt', 'status': 'status_code',
          'actual_start': 'act_start_date', 'actual_finish': 'act_end_date',
          'target_start': 'target_start_date', 'target_finish': 'target_end_date',
          'constraint': ('cstr_type', 'cstr_date')}

def rels_from_op(op, base):
    """Relationship (pred, succ) code pairs an op targets - explicit list or a
    `match:` glob. Reads the verifier's base index (base['preds']); this is the
    verifier-side counterpart of resolve_rels(op, ctx)."""
    if 'relationships' in op:
        return [(r['predecessor'], r['successor']) for r in op['relationships']]
    if 'match' in op:
        m = op['match']
        return [(p, s) for (p, s) in base['preds']
                if fnmatch.fnmatch(p, m['predecessor'])
                and fnmatch.fnmatch(s, m['successor'])]
    return []

def expected_modify_relationship(op, base, e):
    new = (RTYPE[op['set']['type']], str(int(op['set'].get('lag_days', 0) * 8)))
    for r in rels_from_op(op, base):
        e['rel_modified'][r] = new

def expected_add_relationship(op, base, e):
    for r in op['relationships']:
        e['rel_added'].add((r['predecessor'], r['successor']))

def expected_remove_relationship(op, base, e):
    for r in rels_from_op(op, base):
        e['rel_removed'].add(r)

def expected_add_activity(op, base, e):
    a = op['activity']; e['task_added'].add(a['code'])
    for p in op.get('predecessors', []):
        e['rel_added'].add((p['activity'], a['code']))
    for s in op.get('successors', []):
        e['rel_added'].add((a['code'], s['activity']))

def expected_modify_activity(op, base, e):
    e['task_modified'].setdefault(op['activity'], set())
    for k in op['set']:
        col = AFIELD.get(k, k)
        e['task_modified'][op['activity']].update(
            col if isinstance(col, tuple) else (col,))

def expected_split_activity(op, base, e):
    e['task_modified'].setdefault(op['original'], set())
    for k in op.get('modify_original', {}):
        col = AFIELD.get(k, k)
        e['task_modified'][op['original']].update(
            col if isinstance(col, tuple) else (col,))
    na = op['new_activity']; e['task_added'].add(na['code'])
    for p in na.get('predecessors', []):
        e['rel_added'].add((p['activity'], na['code']))
    for s in na.get('successors', []):
        e['rel_added'].add((na['code'], s['activity']))

def expected_remove_activity(op, base, e):
    e['task_removed'].add(op['activity'])
    for (p, s) in base['preds']:
        if p == op['activity'] or s == op['activity']:
            e['rel_removed'].add((p, s))

def expected_add_wbs(op, base, e):
    e['wbs_added'].add(op['wbs']['name'])

def expected_modify_wbs(op, base, e):
    e['wbs_modified'].add(op['wbs'])

def expected_remove_wbs(op, base, e):
    e['wbs_removed'].add(op['wbs'])

EXPECTED = {'modify_relationship': expected_modify_relationship,
            'add_relationship': expected_add_relationship,
            'remove_relationship': expected_remove_relationship,
            'add_activity': expected_add_activity,
            'modify_activity': expected_modify_activity,
            'split_activity': expected_split_activity,
            'remove_activity': expected_remove_activity,
            'add_wbs': expected_add_wbs,
            'modify_wbs': expected_modify_wbs,
            'remove_wbs': expected_remove_wbs}

assert set(OPS) == set(EXPECTED), \
    "operations.py: OPS and EXPECTED must define the same set of operations"
