#!/usr/bin/env python3
"""Pure capture guard equivalence and failed-controller replays; no native calls."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
from types import SimpleNamespace
import unittest


parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--source-root', type=Path, default=Path(__file__).resolve().parents[1])
options, remaining = parser.parse_known_args()
ROOT = options.source_root.resolve()
sys.path.insert(0, str(ROOT / 'scripts'))

ORIGINAL_SHA256 = '6b64561032d86b60dc1276aea1a642f427b48a1b5257934e89b71afb4269f71f'
FAILURE_SHA256 = 'd63129b91900c6ad5d2a99767e6d4c35dacc8ec254e54be28981a1613adb1ecf'
FIXTURES = Path(__file__).resolve().parent / 'fixtures/macos_capture_diagnostics'
ORIGINAL_GUARD = b'''            guard image.width == configuration.width, image.height == configuration.height,
                  closeRect(frame, try ownedWindow(pid, windowID)) else {
                throw CaptureFailure("Captured pixel dimensions or owned-window bounds changed")
            }
'''
DIAGNOSTIC_GUARD = b'''            report["configured_image_dimensions"] = [configuration.width, configuration.height]
            report["post_capture_validation_stage"] = "pixel_dimensions"
            guard image.width == configuration.width, image.height == configuration.height else {
                throw CaptureFailure("Captured pixel dimensions or owned-window bounds changed")
            }
            report["post_capture_validation_stage"] = "exact_owned_window"
            let postCaptureFrame = try ownedWindow(pid, windowID)
            report["post_capture_owned_window_bounds_points"] = rectValues(postCaptureFrame)
            report["post_capture_validation_stage"] = "bounds_agreement"
            guard closeRect(frame, postCaptureFrame) else {
                throw CaptureFailure("Captured pixel dimensions or owned-window bounds changed")
            }
            report["post_capture_validation_stage"] = "complete"
'''


def original_capture_helper(native):
    """Permit exactly the registered evidence block; recover every original byte."""
    if native.count(DIAGNOSTIC_GUARD) != 1:
        raise AssertionError('Expected exactly one registered capture diagnostic block')
    return native.replace(DIAGNOSTIC_GUARD, ORIGINAL_GUARD, 1)


def guard_outcome(block, width, height, owned):
    """Interpret only the exact, separately byte-bound Swift guard statements.

    This checks short-circuit/native-read equivalence, not Swift compilation/ABI.
    Report assignments do not participate in either guard's success condition.
    """
    calls = []
    frame = [0., 25., 1024., 684.]
    def read_owned(_pid, _window):
        calls.append('ownedWindow')
        if isinstance(owned, Exception):
            raise owned
        return owned
    context = {'image': SimpleNamespace(width=width, height=height),
               'configuration': SimpleNamespace(width=1024, height=684),
               'pid': 3602, 'windowID': 24, 'frame': frame,
               'ownedWindow': read_owned,
               'closeRect': lambda a, b: all(abs(x-y) <= .5 for x,y in zip(a,b))}
    statements = re.findall(r'guard (.*?) else \{|let (postCaptureFrame = try ownedWindow\(pid, windowID\))',
                            block.decode(), re.S)
    try:
        for guard, assignment in statements:
            if assignment:
                name, value = assignment.split(' = ', 1)
                context[name] = eval(value.replace('try ', ''), {'__builtins__': {}}, context)
                continue
            # Split Swift guard clauses only at their top-level comma.
            clauses, start, depth = [], 0, 0
            for index, char in enumerate(guard):
                depth += int(char == '(') - int(char == ')')
                if char == ',' and depth == 0:
                    clauses.append(guard[start:index]); start = index + 1
            clauses.append(guard[start:])
            for clause in clauses:
                if not eval(clause.strip().replace('try ', ''), {'__builtins__': {}}, context):
                    return 'guard_failure', calls
        return 'success', calls
    except RuntimeError:
        return 'owned_window_unavailable', calls


class GuardSourceControls(unittest.TestCase):
    def test_original_snapshot_and_exact_reverse_transformation_preserve_every_other_byte(self):
        original = (FIXTURES / 'original_helper.swift.txt').read_bytes()
        current = (ROOT / 'scripts/macos_window_capture.swift').read_bytes()
        self.assertEqual(hashlib.sha256(original).hexdigest(), ORIGINAL_SHA256)
        self.assertEqual(original_capture_helper(current), original)
        self.assertEqual(original.count(ORIGINAL_GUARD), 1)
        with self.assertRaises(AssertionError):
            original_capture_helper(original)

    def test_other_guard_privacy_success_or_extra_diagnostic_change_cannot_reconstruct_original(self):
        current = (ROOT / 'scripts/macos_window_capture.swift').read_bytes()
        original = (FIXTURES / 'original_helper.swift.txt').read_bytes()
        mutations = [current.replace(b'abs($0.0 - $0.1) <= 0.5', b'abs($0.0 - $0.1) <= 1.0'),
                     current.replace(b'scale <= 4', b'scale <= 5'),
                     current.replace(b'"passed": false', b'"passed": true'),
                     current.replace(b'"permission_requests_made": 0', b'"permission_requests_made": 1'),
                     current.replace(b'configuration.capturesAudio = false', b'configuration.capturesAudio = true'),
                     current.replace(b'let postCaptureFrame = try ownedWindow(pid, windowID)',
                                     b'let postCaptureFrame = frame')]
        for changed in mutations:
            with self.subTest(mutation=hashlib.sha256(changed).hexdigest()):
                self.assertNotEqual(changed, current)
                try:
                    reconstructed = original_capture_helper(changed)
                except AssertionError:
                    continue
                self.assertNotEqual(reconstructed, original)

    def test_dimension_bounds_identity_loss_and_tolerance_have_identical_short_circuit_reads(self):
        current = (ROOT / 'scripts/macos_window_capture.swift').read_bytes()
        self.assertEqual(current.count(DIAGNOSTIC_GUARD), 1)
        for width in (1024, 1023, 1025):
            for height in (684, 683, 685):
                for owned in ([0,25,1024,684], [.5,25,1024,684], [.50001,25,1024,684],
                              [0,25,1004,664], RuntimeError('Exact owner/window unavailable')):
                    with self.subTest(width=width,height=height,owned=owned):
                        old = guard_outcome(ORIGINAL_GUARD, width, height, owned)
                        new = guard_outcome(DIAGNOSTIC_GUARD, width, height, owned)
                        self.assertEqual(new, old)
                        self.assertEqual(len(new[1]), int(width == 1024 and height == 684))

    def test_evidence_is_fixed_size_and_only_uses_same_read_guard_inputs(self):
        fields = re.findall(rb'report\["([^"]+)"\] = ([^\n]+)', DIAGNOSTIC_GUARD)
        self.assertEqual(set(name for name,_ in fields),
                         {b'configured_image_dimensions', b'post_capture_validation_stage',
                          b'post_capture_owned_window_bounds_points'})
        self.assertIn((b'configured_image_dimensions', b'[configuration.width, configuration.height]'), fields)
        self.assertIn((b'post_capture_owned_window_bounds_points', b'rectValues(postCaptureFrame)'), fields)
        self.assertEqual([value for name,value in fields if name == b'post_capture_validation_stage'],
                         [b'"pixel_dimensions"', b'"exact_owned_window"', b'"bounds_agreement"', b'"complete"'])
        self.assertEqual(DIAGNOSTIC_GUARD.count(b'ownedWindow(pid, windowID)'), 1)
        self.assertNotIn(b'await', DIAGNOSTIC_GUARD)
        self.assertNotIn(b'catch', DIAGNOSTIC_GUARD)


class FailedReceiptControls(unittest.TestCase):
    def execute_failure(self, raw, *, status=1, elapsed=0.):
        from test_macos_ax_controller import SyntheticRun
        class FailedCaptureRun(SyntheticRun):
            def popen(self, arguments, **keywords):
                process = super().popen(arguments, **keywords)
                if '--png' in arguments:
                    png = Path(arguments[arguments.index('--png')+1])
                    png.unlink()
                    Path(arguments[arguments.index('--report')+1]).write_bytes(raw)
                    original_wait = process.wait
                    def wait(timeout):
                        original_wait(timeout)
                        self.now += elapsed
                        process.returncode = status
                        return status
                    process.wait = wait
                return process
        with tempfile.TemporaryDirectory() as directory:
            harness = FailedCaptureRun(Path(directory).resolve())
            code, result = harness.execute()
            self.assertEqual(code, 1, result)
            self.assertFalse(result['passed'])
            self.assertEqual(len(result['capture_attempts']), 1)
            self.assertFalse(result['capture_attempts'][0]['accepted'])
            self.assertEqual(result['captures'], [])
            self.assertEqual((harness.focus_calls,result['cg_event_post_attempts']), (0,0))
            self.assertFalse(harness.ax_done)
            self.assertFalse(result['query_prerequisites'])
            self.assertFalse(result['bounded_traversal_complete'])
            if elapsed >= 300:
                self.assertNotIn('normal_exit_code', result)
                self.assertTrue(any('whole_flow:' in row for row in result['finalization_failures']))
            else:
                self.assertEqual(result['normal_exit_code'], 0)
            self.assertTrue(all(row['owned_group_gone'] and not row['signals_sent'] for row in result['cleanup']))
            self.assertEqual(result['capture_attempts'][0]['retained_files']['00-startup-menu-1.json']['sha256'],
                             hashlib.sha256(raw).hexdigest())
            return result

    def test_original_actual_receipt_remains_failed_without_invented_after_geometry(self):
        raw = (FIXTURES / 'original-failure-39943145541.json').read_bytes()
        self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()), (859,FAILURE_SHA256))
        receipt = json.loads(raw)
        self.assertNotIn('post_capture_owned_window_bounds_points', receipt)
        self.assertNotIn('configured_image_dimensions', receipt)
        self.assertFalse(receipt['passed'])
        self.assertEqual(receipt['image_dimensions'], [1024,684])
        result = self.execute_failure(raw)
        self.assertEqual(result['failure']['message'], 'Original read-only capture helper failed')

    def test_new_diagnostics_never_convert_resize_identity_or_mapping_failure_into_success_or_retry(self):
        original = json.loads((FIXTURES / 'original-failure-39943145541.json').read_bytes())
        for change in ('same', 'resize', 'move', 'pid', 'window', 'mapping', 'dimensions', 'large_array'):
            receipt = copy.deepcopy(original)
            receipt.update(configured_image_dimensions=[1024,684],
                           post_capture_validation_stage='bounds_agreement',
                           post_capture_owned_window_bounds_points=[0,25,1024,684])
            if change == 'resize': receipt['post_capture_owned_window_bounds_points']=[0,25,1004,664]
            elif change == 'move': receipt['post_capture_owned_window_bounds_points'][0]=100
            elif change == 'pid': receipt['owner_pid']=999
            elif change == 'window': receipt['window_id']=25
            elif change == 'mapping': receipt['point_pixel_scale']=False
            elif change == 'dimensions': receipt['image_dimensions']=[960,568]
            elif change == 'large_array': receipt['post_capture_owned_window_bounds_points']=[0]*4096
            with self.subTest(change=change):
                self.execute_failure(json.dumps(receipt).encode())

    def test_stage_label_passed_flag_or_exit_code_alone_never_authorizes_failed_capture(self):
        original = json.loads((FIXTURES / 'original-failure-39943145541.json').read_bytes())
        for status, passed in ((0,False),(1,False),(1,True)):
            receipt = dict(original, passed=passed, post_capture_validation_stage='complete')
            with self.subTest(status=status,passed=passed):
                self.execute_failure(json.dumps(receipt).encode(), status=status)

    def test_late_failed_helpers_preserve_raw_failure_and_original_stage_whole_deadlines(self):
        raw = (FIXTURES / 'original-failure-39943145541.json').read_bytes()
        for elapsed in (25.,25.001,300.001):
            with self.subTest(elapsed=elapsed):
                result = self.execute_failure(raw, elapsed=elapsed)
                self.assertEqual(result['failure']['type'], 'TimeoutError')
                self.assertEqual((result['budgets_seconds']['capture'],result['budgets_seconds']['total']), (25,300))


if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0], *remaining])
