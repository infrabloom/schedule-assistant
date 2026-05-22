"""
Unit tests for predict_milestones.contract_milestones.

Milestone detection must work for any project's naming convention, not just
CB4's - these tests pin the generic default pattern and confirm a custom
pattern (from project.yaml) overrides it.

Run from the plugin root:  python -m unittest discover -s tests -v
Requires Python 3.9+.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))

import predict_milestones as pm       # noqa: E402


def acts(*code_type_pairs):
    """Build a minimal activities dict: {code: {'type': task_type}}."""
    return {code: {'type': ttype} for code, ttype in code_type_pairs}


class TestContractMilestones(unittest.TestCase):
    def test_default_pattern_catches_common_tokens(self):
        a = acts(('MS-DH4-EFA', 'TT_Mile'), ('MS-DH1-FA', 'TT_Mile'),
                 ('MS-DH2-RFS', 'TT_FinMile'), ('MS-DH3-TCO', 'TT_Mile'))
        got = pm.contract_milestones(a, pm.DEFAULT_MILESTONE_PATTERN)
        self.assertEqual(
            got, ['MS-DH1-FA', 'MS-DH2-RFS', 'MS-DH3-TCO', 'MS-DH4-EFA'])

    def test_default_pattern_ignores_non_milestone_type(self):
        # a normal task whose code happens to contain a token is NOT a milestone
        a = acts(('CONS-DH4-FACADE', 'TT_Task'), ('MS-DH4-EFA', 'TT_Mile'))
        got = pm.contract_milestones(a, pm.DEFAULT_MILESTONE_PATTERN)
        self.assertEqual(got, ['MS-DH4-EFA'])

    def test_default_pattern_ignores_non_contract_milestone(self):
        # a procurement milestone with no contract token is not picked up
        a = acts(('MS-PM-1000', 'TT_Mile'), ('MS-DH4-EFA', 'TT_Mile'))
        got = pm.contract_milestones(a, pm.DEFAULT_MILESTONE_PATTERN)
        self.assertEqual(got, ['MS-DH4-EFA'])

    def test_custom_pattern_overrides_default(self):
        # a project whose milestones follow a different convention
        a = acts(('GATE-ADMIN-SC', 'TT_Mile'), ('MS-DH4-EFA', 'TT_Mile'))
        got = pm.contract_milestones(a, r'GATE-.*-SC$')
        self.assertEqual(got, ['GATE-ADMIN-SC'])


if __name__ == '__main__':
    unittest.main()
