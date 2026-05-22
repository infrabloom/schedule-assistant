"""
Test fixtures for the schedule-assistant change-set pipeline.

`mini_xer()` returns the text of a small but structurally complete XER:
1 PROJECT, 1 CALENDAR, 3 WBS nodes, 6 TASK rows (five tasks + a milestone),
and 4 TASKPRED rows forming a chain A-1000 -> A-1010 -> A-1020 -> A-1030 ->
MS-DONE.  It is assembled programmatically so the column counts are always
consistent - no hand-aligned tabs to get wrong.

The fixture is intentionally minimal: it exists to exercise the change-set
operations and the pipeline's safety behaviour, not to be a realistic
production schedule.
"""

ERMHDR = ('ERMHDR\t19.12\t2026-05-22\tProject\tadmin\tadmin\t'
          'dbxDatabaseNoName\tProject Management\tUSD')


def _table(name, cols, rows):
    """Render one XER table block from a column list and a list of row dicts."""
    lines = ['%T\t' + name, '%F\t' + '\t'.join(cols)]
    for r in rows:
        lines.append('%R\t' + '\t'.join(str(r.get(c, '')) for c in cols))
    return '\n'.join(lines)


_PROJECT = _table(
    'PROJECT',
    ['proj_id', 'proj_short_name', 'proj_node_flag'],
    [{'proj_id': '1', 'proj_short_name': 'MINI', 'proj_node_flag': 'Y'}])

_CALENDAR = _table(
    'CALENDAR',
    ['clndr_id', 'clndr_name', 'day_hr_cnt'],
    [{'clndr_id': '1', 'clndr_name': 'Standard 7-Day', 'day_hr_cnt': '8'}])

_PROJWBS = _table(
    'PROJWBS',
    ['wbs_id', 'proj_id', 'parent_wbs_id', 'seq_num',
     'proj_node_flag', 'status_code', 'wbs_short_name', 'wbs_name'],
    [{'wbs_id': '100', 'proj_id': '1', 'parent_wbs_id': '', 'seq_num': '1',
      'proj_node_flag': 'Y', 'status_code': 'WS_Open',
      'wbs_short_name': 'MINI', 'wbs_name': 'Mini Project'},
     {'wbs_id': '101', 'proj_id': '1', 'parent_wbs_id': '100', 'seq_num': '1',
      'proj_node_flag': 'N', 'status_code': 'WS_Open',
      'wbs_short_name': 'A1', 'wbs_name': 'Area 1'},
     {'wbs_id': '102', 'proj_id': '1', 'parent_wbs_id': '100', 'seq_num': '2',
      'proj_node_flag': 'N', 'status_code': 'WS_Open',
      'wbs_short_name': 'A2', 'wbs_name': 'Area 2'}])

_TASK_COLS = ['task_id', 'proj_id', 'wbs_id', 'clndr_id', 'task_code',
              'task_name', 'task_type', 'status_code', 'duration_type',
              'complete_pct_type', 'guid', 'phys_complete_pct',
              'target_drtn_hr_cnt', 'remain_drtn_hr_cnt',
              'act_start_date', 'act_end_date',
              'target_start_date', 'target_end_date',
              'cstr_type', 'cstr_date']


def _task(tid, code, name, wbs, ttype, status, guid,
          dur='40.0', remain='40.0', pct='0',
          a_start='', a_end='', t_start='', t_end='', cstr='', cstr_date=''):
    dtype = 'DT_FixedDrtn' if ttype == 'TT_Mile' else 'DT_FixedDUR2'
    return {'task_id': tid, 'proj_id': '1', 'wbs_id': wbs, 'clndr_id': '1',
            'task_code': code, 'task_name': name, 'task_type': ttype,
            'status_code': status, 'duration_type': dtype,
            'complete_pct_type': 'CP_Drtn', 'guid': guid,
            'phys_complete_pct': pct,
            'target_drtn_hr_cnt': dur, 'remain_drtn_hr_cnt': remain,
            'act_start_date': a_start, 'act_end_date': a_end,
            'target_start_date': t_start, 'target_end_date': t_end,
            'cstr_type': cstr, 'cstr_date': cstr_date}


_TASK = _table('TASK', _TASK_COLS, [
    _task('10', 'A-1000', 'First Task', '101', 'TT_Task', 'TK_NotStart',
          'MiniFixtureGuidAA0001',
          t_start='2026-06-01 08:00', t_end='2026-06-05 17:00'),
    _task('20', 'A-1010', 'Second Task', '101', 'TT_Task', 'TK_NotStart',
          'MiniFixtureGuidAA0002',
          t_start='2026-06-08 08:00', t_end='2026-06-12 17:00'),
    _task('30', 'A-1020', 'Third Task', '101', 'TT_Task', 'TK_Active',
          'MiniFixtureGuidAA0003', dur='80.0', remain='40.0', pct='50',
          a_start='2026-06-15 08:00',
          t_start='2026-06-15 08:00', t_end='2026-06-24 17:00'),
    _task('40', 'A-1030', 'Fourth Task', '101', 'TT_Task', 'TK_NotStart',
          'MiniFixtureGuidAA0004',
          t_start='2026-06-25 08:00', t_end='2026-06-30 17:00'),
    _task('50', 'MS-DONE', 'Project Complete', '101', 'TT_Mile', 'TK_NotStart',
          'MiniFixtureGuidAA0005', dur='0.0', remain='0.0',
          t_end='2026-07-01 08:00'),
    _task('60', 'A-1040', 'Splittable Task', '102', 'TT_Task', 'TK_NotStart',
          'MiniFixtureGuidAA0006', dur='80.0', remain='80.0',
          t_start='2026-06-01 08:00', t_end='2026-06-10 17:00'),
])

_TASKPRED = _table(
    'TASKPRED',
    ['task_pred_id', 'task_id', 'proj_id', 'pred_task_id', 'pred_proj_id',
     'pred_type', 'lag_hr_cnt'],
    [{'task_pred_id': '1000', 'task_id': '20', 'proj_id': '1',
      'pred_task_id': '10', 'pred_proj_id': '1',
      'pred_type': 'PR_FS', 'lag_hr_cnt': '0'},
     {'task_pred_id': '1001', 'task_id': '30', 'proj_id': '1',
      'pred_task_id': '20', 'pred_proj_id': '1',
      'pred_type': 'PR_FS', 'lag_hr_cnt': '0'},
     {'task_pred_id': '1002', 'task_id': '40', 'proj_id': '1',
      'pred_task_id': '30', 'pred_proj_id': '1',
      'pred_type': 'PR_FS', 'lag_hr_cnt': '0'},
     {'task_pred_id': '1003', 'task_id': '50', 'proj_id': '1',
      'pred_task_id': '40', 'pred_proj_id': '1',
      'pred_type': 'PR_FS', 'lag_hr_cnt': '0'}])


def mini_xer():
    """Return the full text of the minimal fixture XER."""
    return '\n'.join(
        [ERMHDR, _PROJECT, _CALENDAR, _PROJWBS, _TASK, _TASKPRED, '%E']) + '\n'


def write_mini(path):
    """Write the fixture XER to `path` (cp1252, as a real P6 export would be)."""
    with open(path, 'w', encoding='cp1252', newline='') as f:
        f.write(mini_xer())
