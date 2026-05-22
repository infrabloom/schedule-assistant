"""
Unit tests for the change-set operations.

Each test loads a fresh copy of the fixture XER, applies one operation through
the `OPS` dispatch table, and asserts on the in-memory result. The engine lives
in `operations.py` and the XER parser/writer in `xer_io.py`; these tests
exercise both directly.

Run from the plugin root:  python -m unittest discover -s tests -v
Requires Python 3.9+ and PyYAML is NOT needed here (the engine is YAML-free).
"""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))
sys.path.insert(0, HERE)

import operations as ops              # noqa: E402
import xer_io as xio                  # noqa: E402
from fixtures import write_mini, mini_xer   # noqa: E402


def load():
    """Parse a fresh copy of the fixture XER; return (ermhdr, tables, ctx)."""
    fd, p = tempfile.mkstemp(suffix='.xer')
    os.close(fd)
    try:
        write_mini(p)
        ermhdr, tables, _ = xio.parse_xer(p)
    finally:
        os.remove(p)
    return ermhdr, tables, ops.Ctx(tables)


class TestParsing(unittest.TestCase):
    def test_ctx_indexes(self):
        _, _, ctx = load()
        self.assertEqual(len(ctx.code2id), 6)
        self.assertEqual(ctx.max_task_id, 60)
        self.assertEqual(ctx.max_pred_id, 1003)
        self.assertEqual(ctx.max_wbs_id, 102)
        self.assertEqual(ctx.proj_id, '1')

    def test_write_roundtrip(self):
        ermhdr, tables, _ = load()
        fd, p = tempfile.mkstemp(suffix='.xer')
        os.close(fd)
        try:
            xio.write_xer(ermhdr, tables, p)
            e2, t2, _ = xio.parse_xer(p)
        finally:
            os.remove(p)
        self.assertEqual(e2, ermhdr)
        by = {t.name: t for t in t2}
        self.assertEqual(len(by['TASK'].rows), 6)
        self.assertEqual(len(by['TASKPRED'].rows), 4)
        self.assertEqual(len(by['PROJWBS'].rows), 3)

    def test_write_roundtrip_crlf(self):
        """A CRLF-terminated XER (a real Windows P6 export) must round-trip
        faithfully: parse_xer reports '\\r\\n', write_xer reproduces it, and
        parsing stays newline-agnostic."""
        fd, src = tempfile.mkstemp(suffix='.xer')
        os.close(fd)
        fd, dst = tempfile.mkstemp(suffix='.xer')
        os.close(fd)
        try:
            with open(src, 'w', encoding='cp1252', newline='') as f:
                f.write(mini_xer().replace('\n', '\r\n'))
            ermhdr, tables, nl = xio.parse_xer(src)
            self.assertEqual(nl, '\r\n')
            by = {t.name: t for t in tables}
            self.assertEqual(len(by['TASK'].rows), 6)        # no stray \r
            self.assertEqual(len(by['TASKPRED'].rows), 4)
            xio.write_xer(ermhdr, tables, dst, newline=nl)
            with open(dst, 'rb') as f:
                data = f.read()
            self.assertIn(b'\r\n', data)
            self.assertNotIn(b'\r\r', data)
            e2, t2, nl2 = xio.parse_xer(dst)
            self.assertEqual(nl2, '\r\n')
            self.assertEqual(e2, ermhdr)
        finally:
            os.remove(src)
            os.remove(dst)


class TestRelationshipOps(unittest.TestCase):
    def test_modify_relationship(self):
        _, _, ctx = load()
        ops.OPS['modify_relationship']({
            'op': 'modify_relationship',
            'set': {'type': 'FF', 'lag_days': 3},
            'expect': {'type': 'FS', 'lag_days': 0},
            'relationships': [{'predecessor': 'A-1000', 'successor': 'A-1010'}],
        }, ctx)
        row = ops.find_pred_row(ctx, 'A-1000', 'A-1010')
        TP = ctx.tbl['TASKPRED']
        self.assertEqual(TP.g(row, 'pred_type'), 'PR_FF')
        self.assertEqual(TP.g(row, 'lag_hr_cnt'), '24')

    def test_modify_relationship_expect_mismatch(self):
        _, _, ctx = load()
        with self.assertRaises(ops.PatchError):
            ops.OPS['modify_relationship']({
                'op': 'modify_relationship',
                'set': {'type': 'FF', 'lag_days': 3},
                'expect': {'type': 'FF', 'lag_days': 0},   # fixture is FS - wrong
                'relationships': [{'predecessor': 'A-1000',
                                   'successor': 'A-1010'}],
            }, ctx)

    def test_modify_relationship_match_selector(self):
        _, _, ctx = load()
        ops.OPS['modify_relationship']({
            'op': 'modify_relationship',
            'set': {'type': 'SS', 'lag_days': 0},
            'match': {'predecessor': 'A-*', 'successor': 'A-*'},
        }, ctx)
        TP = ctx.tbl['TASKPRED']
        ss = sum(1 for r in TP.rows if TP.g(r, 'pred_type') == 'PR_SS')
        # A-1000->A-1010, A-1010->A-1020, A-1020->A-1030 match; ->MS-DONE does not
        self.assertEqual(ss, 3)

    def test_add_relationship(self):
        _, _, ctx = load()
        before = len(ctx.tbl['TASKPRED'].rows)
        ops.OPS['add_relationship']({
            'op': 'add_relationship',
            'relationships': [{'predecessor': 'A-1000', 'successor': 'A-1020',
                               'type': 'FS', 'lag_days': 1}],
        }, ctx)
        self.assertEqual(len(ctx.tbl['TASKPRED'].rows), before + 1)
        row = ops.find_pred_row(ctx, 'A-1000', 'A-1020')
        self.assertEqual(ctx.tbl['TASKPRED'].g(row, 'lag_hr_cnt'), '8')

    def test_add_relationship_duplicate_rejected(self):
        _, _, ctx = load()
        with self.assertRaises(ops.PatchError):
            ops.OPS['add_relationship']({
                'op': 'add_relationship',
                'relationships': [{'predecessor': 'A-1000',
                                   'successor': 'A-1010'}],
            }, ctx)

    def test_remove_relationship(self):
        _, _, ctx = load()
        before = len(ctx.tbl['TASKPRED'].rows)
        ops.OPS['remove_relationship']({
            'op': 'remove_relationship',
            'relationships': [{'predecessor': 'A-1000', 'successor': 'A-1010'}],
        }, ctx)
        self.assertEqual(len(ctx.tbl['TASKPRED'].rows), before - 1)
        self.assertIsNone(ops.find_pred_row(ctx, 'A-1000', 'A-1010'))

    def test_remove_relationship_no_match_rejected(self):
        _, _, ctx = load()
        with self.assertRaises(ops.PatchError):
            ops.OPS['remove_relationship']({
                'op': 'remove_relationship',
                'relationships': [{'predecessor': 'A-1000',
                                   'successor': 'A-1030'}],   # no such tie
            }, ctx)


class TestActivityOps(unittest.TestCase):
    def test_add_activity(self):
        _, _, ctx = load()
        before = len(ctx.tbl['TASK'].rows)
        ops.OPS['add_activity']({
            'op': 'add_activity',
            'activity': {'code': 'A-1050', 'name': 'New Task', 'wbs': 'Area 1',
                         'type': 'Task', 'status': 'NotStarted',
                         'duration_days': 5},
            'predecessors': [{'activity': 'A-1040', 'type': 'FS',
                              'lag_days': 0}],
        }, ctx)
        self.assertEqual(len(ctx.tbl['TASK'].rows), before + 1)
        self.assertIn('A-1050', ctx.code2id)
        self.assertIsNotNone(ops.find_pred_row(ctx, 'A-1040', 'A-1050'))
        # the new activity gets a real 22-char base64 GUID, not a blank one
        # (validate_xer.py check 9 rejects blank/short GUIDs)
        T = ctx.tbl['TASK']
        new = next(r for r in T.rows if T.g(r, 'task_code') == 'A-1050')
        self.assertRegex(T.g(new, 'guid'), r'^[A-Za-z0-9+/]{22}$')

    def test_add_activity_scrubs_inherited_actuals(self):
        """An InProgress add_activity clones the InProgress template row
        (A-1020, which carries an actual start and 50% progress); those
        inherited actuals must be scrubbed off the new activity."""
        _, _, ctx = load()
        ops.OPS['add_activity']({
            'op': 'add_activity',
            'activity': {'code': 'A-1060', 'name': 'Fresh Task', 'wbs': 'Area 1',
                         'type': 'Task', 'status': 'InProgress',
                         'duration_days': 5},
        }, ctx)
        T = ctx.tbl['TASK']
        new = next(r for r in T.rows if T.g(r, 'task_code') == 'A-1060')
        self.assertEqual(T.g(new, 'act_start_date'), '')
        self.assertEqual(T.g(new, 'act_end_date'), '')
        self.assertEqual(T.g(new, 'phys_complete_pct'), '0')
        self.assertEqual(T.g(new, 'cstr_type'), '')

    def test_add_activity_duplicate_code_rejected(self):
        _, _, ctx = load()
        with self.assertRaises(ops.PatchError):
            ops.OPS['add_activity']({
                'op': 'add_activity',
                'activity': {'code': 'A-1000', 'name': 'Dup'},
            }, ctx)

    def test_add_activity_case_collision_rejected(self):
        _, _, ctx = load()
        with self.assertRaises(ops.PatchError):
            ops.OPS['add_activity']({
                'op': 'add_activity',
                'activity': {'code': 'a-1000', 'name': 'Case dup'},
            }, ctx)

    def test_add_activity_codes_block_rejected(self):
        _, _, ctx = load()
        with self.assertRaises(ops.PatchError):
            ops.OPS['add_activity']({
                'op': 'add_activity',
                'activity': {'code': 'A-9999', 'name': 'X',
                             'codes': {'Trade': 'Mechanical'}},
            }, ctx)

    def test_modify_activity(self):
        _, _, ctx = load()
        ops.OPS['modify_activity']({
            'op': 'modify_activity', 'activity': 'A-1000',
            'set': {'name': 'Renamed Task'},
            'expect': {'name': 'First Task'},
        }, ctx)
        T = ctx.tbl['TASK']
        row = next(r for r in T.rows if T.g(r, 'task_code') == 'A-1000')
        self.assertEqual(T.g(row, 'task_name'), 'Renamed Task')

    def test_modify_activity_expect_mismatch(self):
        _, _, ctx = load()
        with self.assertRaises(ops.PatchError):
            ops.OPS['modify_activity']({
                'op': 'modify_activity', 'activity': 'A-1000',
                'set': {'name': 'X'}, 'expect': {'name': 'Wrong Name'},
            }, ctx)

    def test_split_activity(self):
        _, _, ctx = load()
        before = len(ctx.tbl['TASK'].rows)
        ops.OPS['split_activity']({
            'op': 'split_activity', 'original': 'A-1040',
            'modify_original': {'name': 'Splittable Task (part 1)'},
            'new_activity': {'code': 'A-1041',
                             'name': 'Splittable Task (part 2)',
                             'wbs': 'Area 2', 'type': 'Task',
                             'status': 'NotStarted', 'duration_days': 4},
        }, ctx)
        self.assertEqual(len(ctx.tbl['TASK'].rows), before + 1)
        self.assertIn('A-1041', ctx.code2id)

    def test_remove_activity_reroute(self):
        _, _, ctx = load()
        ops.OPS['remove_activity']({
            'op': 'remove_activity', 'activity': 'A-1020', 'reroute': True,
        }, ctx)
        self.assertNotIn('A-1020', ctx.code2id)
        # reroute bridges the gap: A-1010 -> A-1030 now exists
        self.assertIsNotNone(ops.find_pred_row(ctx, 'A-1010', 'A-1030'))

    def test_remove_activity_unknown_rejected(self):
        _, _, ctx = load()
        with self.assertRaises(ops.PatchError):
            ops.OPS['remove_activity']({
                'op': 'remove_activity', 'activity': 'A-NOPE',
            }, ctx)


class TestWbsOps(unittest.TestCase):
    def test_add_wbs(self):
        _, _, ctx = load()
        before = len(ctx.tbl['PROJWBS'].rows)
        ops.OPS['add_wbs']({
            'op': 'add_wbs',
            'wbs': {'parent': 'Area 1', 'code': 'A1-X', 'name': 'Sub Node'},
        }, ctx)
        self.assertEqual(len(ctx.tbl['PROJWBS'].rows), before + 1)

    def test_modify_wbs(self):
        _, _, ctx = load()
        ops.OPS['modify_wbs']({
            'op': 'modify_wbs', 'wbs': 'Area 2',
            'set': {'name': 'Area Two'}, 'expect': {'name': 'Area 2'},
        }, ctx)
        W = ctx.tbl['PROJWBS']
        row = next(r for r in W.rows if W.g(r, 'wbs_id') == '102')
        self.assertEqual(W.g(row, 'wbs_name'), 'Area Two')

    def test_remove_wbs_with_activities_rejected(self):
        _, _, ctx = load()
        with self.assertRaises(ops.PatchError):
            ops.OPS['remove_wbs']({'op': 'remove_wbs', 'wbs': 'Area 1'}, ctx)

    def test_remove_wbs_empty(self):
        _, _, ctx = load()
        ops.OPS['add_wbs']({
            'op': 'add_wbs',
            'wbs': {'parent': 'Area 1', 'code': 'TMP', 'name': 'Temp Node'},
        }, ctx)
        before = len(ctx.tbl['PROJWBS'].rows)
        ops.OPS['remove_wbs']({
            'op': 'remove_wbs', 'wbs': 'Area 1 > Temp Node',
        }, ctx)
        self.assertEqual(len(ctx.tbl['PROJWBS'].rows), before - 1)


class TestDispatch(unittest.TestCase):
    def test_ops_registry_complete(self):
        self.assertEqual(set(ops.OPS), {
            'modify_relationship', 'add_relationship', 'remove_relationship',
            'add_activity', 'modify_activity', 'split_activity',
            'remove_activity', 'add_wbs', 'modify_wbs', 'remove_wbs'})

    def test_deferred_ops_declared(self):
        self.assertEqual(ops.DEFERRED, {
            'define_activity_code', 'assign_activity_code',
            'remove_activity_code'})

    def test_expected_registry_matches_ops(self):
        # the patcher (OPS) and the verifier (EXPECTED) must define the same
        # operations - operations.py asserts this at import; pin it here too
        self.assertEqual(set(ops.EXPECTED), set(ops.OPS))


if __name__ == '__main__':
    unittest.main()
