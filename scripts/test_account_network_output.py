#!/usr/bin/env python3
"""Regression/negative controls for expected account admission rejection output."""
import subprocess
import unittest
from test_account_network import probe_passed


def result(stdout, stderr='', code=0):
    return subprocess.CompletedProcess([], code, stdout, stderr)


class AccountProbeOutputTest(unittest.TestCase):
    def test_expected_terminal_rejections(self):
        for role in ('guest', 'replay'):
            output = 'PROTOCOL_CLIENT_FAILED A valid account join ticket is required.\nACCOUNT_NETWORK_REJECT_PASS ' + role + '\n'
            self.assertIn('FAIL', output)  # Preserved negative control for the old broad filter.
            self.assertTrue(probe_passed(role, result(output)))

    def test_explicit_success_markers(self):
        self.assertTrue(probe_passed('client', result('ACCOUNT_NETWORK_BOUND_PASS\n')))
        self.assertTrue(probe_passed('reclaim', result('ACCOUNT_NETWORK_BOUND_PASS\n')))
        self.assertTrue(probe_passed('mismatch', result('ACCOUNT_NETWORK_MISMATCH_PASS reply={} closed_after=0.1\n')))

    def test_missing_or_wrong_role_is_failure(self):
        for output in ('', 'PASS', 'notice ACCOUNT_NETWORK_REJECT_PASS guest',
                       'ACCOUNT_NETWORK_REJECT_PASS replay', 'ACCOUNT_NETWORK_REJECT_PASS guest_extra'):
            self.assertFalse(probe_passed('guest', result(output)))

    def test_errors_never_pass(self):
        passed = 'ACCOUNT_NETWORK_BOUND_PASS\n'
        for output in ('ACCOUNT_NETWORK_BOUND_FAIL', 'SCRIPT ERROR: broken', 'ERROR: broken',
                       'Parse Error: broken', 'PROTOCOL_CLIENT_FAILED disconnected'):
            self.assertFalse(probe_passed('client', result(passed + output)))
        self.assertFalse(probe_passed('client', result(passed, 'ERROR: stderr')))
        self.assertFalse(probe_passed('client', result(passed, code=1)))


if __name__ == '__main__':
    unittest.main()
