"""
Integration / regression tests for the change-set pipeline.

These run apply_changeset.py as a subprocess and assert on its exit code and
output. They verify the P0 hardening:

  * 3.4  bad input aborts cleanly - "ABORTED ...", never a Python traceback
  * 3.2  the write is staged - no .tmp left behind, a preview commits nothing
  * 3.3  the validation gate - a change-set that ADDS issues blocks the commit

Run from the plugin root:  python -m unittest discover -s tests -v
Requires Python 3.9+ and PyYAML.
"""
import os
import sys
import json
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from fixtures import write_mini       # noqa: E402

APPLY = os.path.join(HERE, '..', 'scripts', 'apply_changeset.py')
REVIEW = os.path.join(HERE, '..', 'scripts', 'review_changeset.py')
PREDICT = os.path.join(HERE, '..', 'scripts', 'predict_milestones.py')
VALIDATE = os.path.join(HERE, '..', 'skills', 'data-center-schedule',
                        'scripts', 'validate_xer.py')

# A valid one-operation change-set. `exp_type` is templated so a test can make
# the expect-guard match the fixture (FS) or deliberately mismatch it.
CHANGESET = """\
changeset:
  id: CS-TEST
  title: pipeline test
  base_xer: base.xer
  update_xer: out.xer
  data_date: 2026-06-01
  prepared: 2026-06-01
  author: test
  trigger: automated test
  summary: a one-operation test change-set
changes:
  - id: C1
    op: modify_relationship
    reason: test retie
    source: tests/test_pipeline.py
    set: {{type: FF, lag_days: 3}}
    expect: {{type: {exp_type}, lag_days: 0}}
    relationships:
      - {{predecessor: A-1000, successor: A-1010}}
"""


def run_apply(*args):
    """Run apply_changeset.py; return (returncode, combined_output)."""
    r = subprocess.run([sys.executable, APPLY, *args],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout or '') + (r.stderr or '')


def run_review(*args):
    """Run review_changeset.py; return (returncode, combined_output)."""
    r = subprocess.run([sys.executable, REVIEW, *args],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout or '') + (r.stderr or '')


def run_json(script, *args):
    """Run a pipeline script with --json appended. Return (rc, data|None,
    stderr). In --json mode stdout carries one JSON object and the human
    report goes to stderr - so stdout must parse cleanly on its own."""
    r = subprocess.run([sys.executable, script, *args, '--json'],
                       capture_output=True, text=True)
    out = (r.stdout or '').strip()
    try:
        data = json.loads(out) if out else None
    except ValueError:
        data = None
    return r.returncode, data, (r.stderr or '')


def write(path, text):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


class TestCleanAbort(unittest.TestCase):
    """3.4 - bad input must abort cleanly, never with a traceback."""

    def test_malformed_yaml(self):
        with tempfile.TemporaryDirectory() as d:
            bad = os.path.join(d, 'bad.yaml')
            write(bad, 'changeset: [1, 2\n')          # unbalanced bracket
            rc, out = run_apply(bad, '--xer-dir', d)
            self.assertNotEqual(rc, 0)
            self.assertIn('ABORTED', out)
            self.assertNotIn('Traceback', out)

    def test_missing_top_level_keys(self):
        with tempfile.TemporaryDirectory() as d:
            bad = os.path.join(d, 'nokeys.yaml')
            write(bad, 'foo: bar\n')                  # valid YAML, wrong shape
            rc, out = run_apply(bad, '--xer-dir', d)
            self.assertNotEqual(rc, 0)
            self.assertNotIn('Traceback', out)

    def test_expect_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            write_mini(os.path.join(d, 'base.xer'))
            cs = os.path.join(d, 'cs.yaml')
            write(cs, CHANGESET.format(exp_type='FF'))   # fixture is FS
            rc, out = run_apply(cs, '--xer-dir', d, '--preview')
            self.assertNotEqual(rc, 0)
            self.assertIn('ABORTED', out)
            self.assertNotIn('Traceback', out)


class TestStaging(unittest.TestCase):
    """3.2 - staged write: nothing committed on preview, no .tmp left."""

    def test_preview_stages_without_committing(self):
        with tempfile.TemporaryDirectory() as d:
            write_mini(os.path.join(d, 'base.xer'))
            cs = os.path.join(d, 'cs.yaml')
            write(cs, CHANGESET.format(exp_type='FS'))
            rc, out = run_apply(cs, '--xer-dir', d, '--preview',
                                '--validators-dir', '')
            self.assertEqual(rc, 0, out)
            self.assertIn('preview done', out)
            self.assertTrue(os.path.exists(
                os.path.join(d, 'previews', 'out.xer')))
            self.assertFalse(os.path.exists(os.path.join(d, 'out.xer')))
            self.assertFalse(os.path.exists(
                os.path.join(d, 'previews', 'out.xer.tmp')))

    def test_commit_writes_update_and_backup(self):
        with tempfile.TemporaryDirectory() as d:
            write_mini(os.path.join(d, 'base.xer'))
            cs = os.path.join(d, 'cs.yaml')
            write(cs, CHANGESET.format(exp_type='FS'))
            rc, out = run_apply(cs, '--xer-dir', d, '--validators-dir', '')
            self.assertEqual(rc, 0, out)
            self.assertTrue(os.path.exists(os.path.join(d, 'out.xer')))
            self.assertFalse(os.path.exists(os.path.join(d, 'out.xer.tmp')))
            baks = [f for f in os.listdir(d) if f.startswith('base.xer.bak-')]
            self.assertEqual(len(baks), 1)


class TestValidationGate(unittest.TestCase):
    """3.3 - base-relative gate: a change-set that ADDS validation issues is
    blocked; pre-existing issues are reported but do not block the commit."""

    @staticmethod
    def _validators(d, body):
        """Create a validators dir; both validators share the same body."""
        vdir = os.path.join(d, 'validators')
        os.makedirs(vdir)
        for name in ('validate_xer.py', 'duplicate_audit.py'):
            write(os.path.join(vdir, name), body)
        return vdir

    def _setup(self, d):
        write_mini(os.path.join(d, 'base.xer'))
        cs = os.path.join(d, 'cs.yaml')
        write(cs, CHANGESET.format(exp_type='FS'))
        return cs

    def test_clean_validators_allow_commit(self):
        with tempfile.TemporaryDirectory() as d:
            cs = self._setup(d)
            vdir = self._validators(d, 'import sys\nsys.exit(0)\n')
            rc, out = run_apply(cs, '--xer-dir', d, '--validators-dir', vdir)
            self.assertEqual(rc, 0, out)
            self.assertTrue(os.path.exists(os.path.join(d, 'out.xer')))

    def test_new_failure_blocks_commit(self):
        # validator is clean on base (*.xer) but fails on the staged *.tmp
        body = ('import sys\n'
                'sys.exit(1 if sys.argv[1].endswith(".tmp") else 0)\n')
        with tempfile.TemporaryDirectory() as d:
            cs = self._setup(d)
            vdir = self._validators(d, body)
            rc, out = run_apply(cs, '--xer-dir', d, '--validators-dir', vdir)
            self.assertNotEqual(rc, 0)
            self.assertIn('ADDS validation', out)
            self.assertFalse(os.path.exists(os.path.join(d, 'out.xer')))
            self.assertFalse(os.path.exists(os.path.join(d, 'out.xer.tmp')))

    def test_preexisting_failure_does_not_block(self):
        # validator fails on BOTH base and update - a carried-over issue
        body = 'import sys\nprint("3 issue(s)")\nsys.exit(1)\n'
        with tempfile.TemporaryDirectory() as d:
            cs = self._setup(d)
            vdir = self._validators(d, body)
            rc, out = run_apply(cs, '--xer-dir', d, '--validators-dir', vdir)
            self.assertEqual(rc, 0, out)
            self.assertTrue(os.path.exists(os.path.join(d, 'out.xer')))
            self.assertIn('pre-existing', out)


class TestReview(unittest.TestCase):
    """Exercises review_changeset.py end-to-end. It chains apply (preview),
    verify_changeset, and predict_milestones as subprocesses, so this single
    test covers the verifier and the forecaster after the xer_io parser
    consolidation - paths the other tests do not reach."""

    def test_review_runs_end_to_end(self):
        with tempfile.TemporaryDirectory() as d:
            write_mini(os.path.join(d, 'base.xer'))
            cs = os.path.join(d, 'cs.yaml')
            write(cs, CHANGESET.format(exp_type='FS'))
            rc, out = run_review(cs, '--xer-dir', d, '--validators-dir', '')
            # review reached every section without a crash
            self.assertIn('IMPACT PREVIEW', out)
            self.assertIn('INDEPENDENT VERIFICATION', out)
            self.assertIn('MILESTONE IMPACT', out)
            self.assertIn('VERDICT', out)
            self.assertNotIn('Traceback', out)
            # 0 = safe to approve, 1 = review needed; both mean it ran cleanly
            self.assertIn(rc, (0, 1))


class TestJsonContract(unittest.TestCase):
    """6.6 / 6.7 - every pipeline script offers --json (one JSON object on
    stdout, the human report on stderr) and follows the 0 / 1 / 2 exit-code
    convention (0 ok, 1 finding, 2 usage / IO error)."""

    def test_apply_json_preview_emits_object(self):
        with tempfile.TemporaryDirectory() as d:
            write_mini(os.path.join(d, 'base.xer'))
            cs = os.path.join(d, 'cs.yaml')
            write(cs, CHANGESET.format(exp_type='FS'))
            rc, data, err = run_json(APPLY, cs, '--xer-dir', d, '--preview',
                                     '--validators-dir', '')
            self.assertEqual(rc, 0, err)
            self.assertIsNotNone(data, "stdout did not parse as JSON: " + err)
            self.assertEqual(data['script'], 'apply_changeset')
            self.assertTrue(data['preview'])
            self.assertFalse(data['committed'])
            self.assertEqual(len(data['operations']), 1)

    def test_apply_json_malformed_yaml_exits_2(self):
        with tempfile.TemporaryDirectory() as d:
            bad = os.path.join(d, 'bad.yaml')
            write(bad, 'changeset: [1, 2\n')          # unbalanced bracket
            rc, data, err = run_json(APPLY, bad, '--xer-dir', d)
            self.assertEqual(rc, 2)                    # usage / bad-input
            self.assertNotIn('Traceback', err)

    def test_validate_xer_json(self):
        with tempfile.TemporaryDirectory() as d:
            xer = os.path.join(d, 'base.xer')
            write_mini(xer)
            rc, data, err = run_json(VALIDATE, xer)
            self.assertIn(rc, (0, 1))                  # 0 clean, 1 findings
            self.assertIsNotNone(data, err)
            self.assertEqual(data['script'], 'validate_xer')
            self.assertIn('issue_count', data)
            self.assertIsInstance(data['fail'], list)

    def test_validate_xer_missing_file_exits_2(self):
        rc, data, err = run_json(VALIDATE, os.path.join('no', 'such.xer'))
        self.assertEqual(rc, 2)

    def test_predict_json_no_regression(self):
        with tempfile.TemporaryDirectory() as d:
            xer = os.path.join(d, 'base.xer')
            write_mini(xer)
            # comparing a schedule against itself can never regress -> exit 0
            rc, data, err = run_json(PREDICT, xer, '--compare', xer)
            self.assertEqual(rc, 0, err)
            self.assertIsNotNone(data, err)
            self.assertEqual(data['script'], 'predict_milestones')
            self.assertFalse(data['regression'])

    def test_review_json_emits_verdict(self):
        with tempfile.TemporaryDirectory() as d:
            write_mini(os.path.join(d, 'base.xer'))
            cs = os.path.join(d, 'cs.yaml')
            write(cs, CHANGESET.format(exp_type='FS'))
            rc, data, err = run_json(REVIEW, cs, '--xer-dir', d,
                                     '--validators-dir', '')
            self.assertIn(rc, (0, 1), err)
            self.assertIsNotNone(data, err)
            self.assertEqual(data['script'], 'review_changeset')
            self.assertIn(data['verdict'],
                          ('SAFE_TO_APPROVE', 'REVIEW_NEEDED'))


if __name__ == '__main__':
    unittest.main()
