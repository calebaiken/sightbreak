#!/usr/bin/env python3
"""Independent bounded source/synthetic controls. No native library or process."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unittest

parser = argparse.ArgumentParser()
parser.add_argument('--root', type=Path, required=True)
args = parser.parse_args()
ROOT = args.root.resolve()
sys.argv = [sys.argv[0]]
sys.path.insert(0, str(ROOT / 'scripts'))
if os.sched_getaffinity(0) != {4}:
    raise SystemExit('CPU 4 is required')

CANDIDATE_SHA = '6fa1ca610e84daecc988c9fa46c980fce50e10d1a5029242b2e8da0cc480b6a9'
ORIGINAL_SHA = '6b64561032d86b60dc1276aea1a642f427b48a1b5257934e89b71afb4269f71f'
FAILURE_SHA = 'd63129b91900c6ad5d2a99767e6d4c35dacc8ec254e54be28981a1613adb1ecf'
FIXTURES = ROOT / 'scripts/fixtures/macos_capture_diagnostics'
BEGIN = b'            report["configured_image_dimensions"] = '
END = b'            guard let output = CGImageDestinationCreateWithURL(pngURL'
OLD = b'''            guard image.width == configuration.width, image.height == configuration.height,
                  closeRect(frame, try ownedWindow(pid, windowID)) else {
                throw CaptureFailure("Captured pixel dimensions or owned-window bounds changed")
            }
'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


def split_block(source):
    start = source.index(BEGIN)
    end = source.index(END, start)
    return source[:start], source[start:end], source[end:]


def simulate(block, width=1024, height=684, owned=(0, 25, 1024, 684)):
    """Interpret only the exact limited guard/assignment syntax; never Swift ABI."""
    report, calls = {}, []
    clauses = []
    for line in block.decode().splitlines():
        line = line.strip()
        if not line or line == '}':
            continue
        match = re.fullmatch(r'report\["([a-z_]+)"\] = (.+)', line)
        if match:
            key, expression = match.groups()
            if expression == '[configuration.width, configuration.height]':
                report[key] = [1024, 684]
            elif expression == 'rectValues(postCaptureFrame)':
                report[key] = list(owned)
            else:
                report[key] = json.loads(expression)
        elif line == 'guard image.width == configuration.width, image.height == configuration.height else {':
            if width != 1024 or height != 684:
                return 'guard_failure', report, calls
        elif line == 'let postCaptureFrame = try ownedWindow(pid, windowID)':
            calls.append('ownedWindow')
            if isinstance(owned, Exception):
                return 'owned_window_unavailable', report, calls
        elif line == 'guard closeRect(frame, postCaptureFrame) else {':
            if not all(abs(a-b) <= .5 for a, b in zip((0,25,1024,684), owned)):
                return 'guard_failure', report, calls
        elif line.startswith('throw CaptureFailure('):
            continue
        else:
            raise AssertionError('Uninterpreted source: ' + line)
    return 'success', report, calls


class IndependentSourceControls(unittest.TestCase):
    def test_exact_candidate_original_and_reverse_transformation(self):
        source = (ROOT/'scripts/macos_window_capture.swift').read_bytes()
        original = (FIXTURES/'original_helper.swift.txt').read_bytes()
        self.assertEqual(sha(source), CANDIDATE_SHA)
        self.assertEqual(sha(original), ORIGINAL_SHA)
        prefix, block, suffix = split_block(source)
        self.assertEqual(prefix + OLD + suffix, original)
        self.assertEqual(source.count(BEGIN), 1)
        self.assertEqual(block.count(b'ownedWindow(pid, windowID)'), 1)
        self.assertEqual(source.count(b'CGWindowListCopyWindowInfo('), original.count(b'CGWindowListCopyWindowInfo('))
        self.assertEqual(source.count(b'SCScreenshotManager.captureImage('), 1)
        self.assertNotIn(b'CGEvent', block)
        self.assertNotIn(b'title', block)
        self.assertNotIn(b'await', block)
        self.assertNotIn(b'catch', block)

    def test_new_version_pin_and_reverse_controls_reject_unregistered_mutations(self):
        from test_macos_capture_diagnostics import original_capture_helper
        source = (ROOT/'scripts/macos_window_capture.swift').read_bytes()
        changes = [
            (b'"pixel_dimensions"', b'"complete"'),
            (b'"exact_owned_window"', b'"complete"'),
            (b'"bounds_agreement"', b'"complete"'),
            (b'rectValues(postCaptureFrame)', b'rectValues(frame)'),
            (b'[configuration.width, configuration.height]', b'[image.width, image.height]'),
            (b'let postCaptureFrame = try ownedWindow(pid, windowID)', b'let postCaptureFrame = frame'),
            (b'closeRect(frame, postCaptureFrame)', b'closeRect(frame, frame)'),
            (b'image.width == configuration.width', b'image.width > 0'),
            (b'image.height == configuration.height', b'image.height > 0'),
            (b'<= 0.5', b'<= 50'),
            (b'.optionIncludingWindow', b'.optionAll'),
            (b'== windowID &&', b'!= 0 &&'),
            (b'== pid &&', b'!= 0 &&'),
            (b'== 0 &&', b'>= 0 &&'),
            (b'== true\n', b'!= nil\n'),
            (b'configuration.capturesAudio = false', b'configuration.capturesAudio = true'),
            (b'configuration.showsCursor = false', b'configuration.showsCursor = true'),
            (b'report["passed"] = true', b'report["passed"] = false'),
            (b'"permission_requests_made": 0', b'"permission_requests_made": 1'),
            (b'"input_events_posted": 0', b'"input_events_posted": 1'),
            (b'let request = VNRecognizeTextRequest()', b'let request = VNRecognizeTextRequest(); request.customWords = ["DEPLOY"]'),
        ]
        for old, new in changes:
            with self.subTest(old=old):
                self.assertIn(old, source)
                changed = source.replace(old, new, 1)
                self.assertNotEqual(sha(changed), CANDIDATE_SHA)
                try:
                    recovered = original_capture_helper(changed)
                except AssertionError:
                    continue
                self.assertNotEqual(sha(recovered), ORIGINAL_SHA)
        for changed in (source.replace(BEGIN, BEGIN + b'[]; // ', 1), source + split_block(source)[1]):
            with self.assertRaises(AssertionError):
                original_capture_helper(changed)

    def test_failure_stages_missing_observations_and_tolerance(self):
        block = split_block((ROOT/'scripts/macos_window_capture.swift').read_bytes())[1]
        cases = [
            ({'width':1023}, 'guard_failure', 'pixel_dimensions', 0, False),
            ({'height':685}, 'guard_failure', 'pixel_dimensions', 0, False),
            ({'owned':RuntimeError('wrong owner/window or unavailable')}, 'owned_window_unavailable', 'exact_owned_window', 1, False),
            ({'owned':(0,25,1004,664)}, 'guard_failure', 'bounds_agreement', 1, True),
            ({'owned':(1,25,1024,684)}, 'guard_failure', 'bounds_agreement', 1, True),
            ({'owned':(.500001,25,1024,684)}, 'guard_failure', 'bounds_agreement', 1, True),
            ({'owned':(.5,25,1024,684)}, 'success', 'complete', 1, True),
            ({'owned':(0,25,1024,684)}, 'success', 'complete', 1, True),
        ]
        for inputs, outcome, stage, calls, bounds in cases:
            with self.subTest(inputs=inputs):
                actual, report, reads = simulate(block, **inputs)
                self.assertEqual((actual, report['post_capture_validation_stage'], len(reads)), (outcome,stage,calls))
                self.assertEqual('post_capture_owned_window_bounds_points' in report, bounds)
                self.assertEqual(set(report)-{'post_capture_owned_window_bounds_points'},
                                 {'configured_image_dimensions','post_capture_validation_stage'})
                self.assertEqual(report['configured_image_dimensions'], [1024,684])
                if bounds:
                    self.assertEqual(report['post_capture_owned_window_bounds_points'], list(inputs['owned']))

    def test_validation_complete_precedes_png_vision_and_does_not_claim_whole_success(self):
        source = (ROOT/'scripts/macos_window_capture.swift').read_bytes()
        ordered = [b'"passed": false', b'report["post_capture_validation_stage"] = "complete"',
                   b'guard let output = CGImageDestinationCreateWithURL(pngURL',
                   b'CGImageDestinationFinalize(output)', b'let request = VNRecognizeTextRequest()',
                   b'try VNImageRequestHandler(cgImage: image, options: [:]).perform([request])',
                   b'report["passed"] = true', b'exitCode = 0']
        # Restrict the search to main; the preserved derived-analysis function
        # has its own earlier PNG/Vision calls.
        main = source[source.index(b'@main'):]
        positions = [main.index(token) for token in ordered]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(main.count(b'report["passed"] = true'), 1)
        self.assertIn(b'} catch {\n            let native = error as NSError', main)

    def test_original_failure_bytes_remain_missing_and_failed(self):
        raw = (FIXTURES/'original-failure-39943145541.json').read_bytes()
        self.assertEqual((len(raw),sha(raw)), (859,FAILURE_SHA))
        receipt = json.loads(raw)
        self.assertFalse(receipt['passed'])
        self.assertEqual(receipt['image_dimensions'], [1024,684])
        self.assertEqual(receipt['point_pixel_scale'], 1)
        self.assertEqual(receipt['bounds_points_including_chrome'], [0,25,1024,684])
        for key in ('configured_image_dimensions','post_capture_validation_stage','post_capture_owned_window_bounds_points','text'):
            self.assertNotIn(key, receipt)


class IndependentControllerControls(unittest.TestCase):
    def execute(self, mutation=None, elapsed=0, status=0):
        from test_macos_ax_controller import SyntheticRun
        class ReceiptRun(SyntheticRun):
            def popen(self, arguments, **keywords):
                process = super().popen(arguments, **keywords)
                if '--png' in arguments:
                    path = Path(arguments[arguments.index('--report')+1])
                    data = json.loads(path.read_text())
                    data.update(configured_image_dimensions=list(data['image_dimensions']),
                                post_capture_validation_stage='complete',
                                post_capture_owned_window_bounds_points=list(data['bounds_points_including_chrome']))
                    if mutation:
                        mutation(data)
                    path.write_text(json.dumps(data))
                    wait = process.wait
                    def changed_wait(timeout):
                        wait(timeout)
                        self.now += elapsed
                        process.returncode = status
                        return status
                    process.wait = changed_wait
                return process
        with tempfile.TemporaryDirectory() as directory:
            harness = ReceiptRun(Path(directory).resolve())
            code, report = harness.execute()
            return code, report, harness

    def test_success_path_keeps_diagnostics_advisory_and_posts_no_events(self):
        code, report, harness = self.execute()
        self.assertEqual(code, 0, report.get('failure'))
        self.assertTrue(report['passed'])
        self.assertFalse(report['gameplay_target_accepted'])
        self.assertEqual((report['cg_event_post_attempts'],harness.focus_calls), (0,1))

    def test_success_flags_and_complete_label_never_override_invalid_core_receipts(self):
        changes = [
            ('owner_pid', 999), ('window_id',35), ('passed',False), ('scope','other'),
            ('permissions',{}), ('point_pixel_scale', True), ('point_pixel_scale',float('nan')),
            ('point_pixel_scale',0), ('point_pixel_scale',4.001),
            ('bounds_points_including_chrome',[40,60,1004,664]),
            ('scwindow_frame_points',[40,60,960,569]),
            ('filter_content_rect_points',[0,0,960,569]),
            ('image_dimensions',[1920,1135]), ('image_dimensions',[True,1136]),
            ('input_events_posted',1), ('permission_requests_made',1),
        ]
        for key,value in changes:
            with self.subTest(key=key,value=value):
                code, report, harness = self.execute(lambda data:data.update({key:value}))
                self.assertEqual(code,1,report)
                self.assertFalse(report['passed'])
                self.assertFalse(report['query_prerequisites'])
                self.assertFalse(harness.ax_done)
                self.assertEqual(report['captures'],[])
                self.assertEqual((report['cg_event_post_attempts'],harness.focus_calls),(0,0))
                self.assertEqual(len(report['capture_attempts']),1)
                self.assertFalse(report['capture_attempts'][0]['accepted'])

    def test_late_success_and_nonzero_exit_do_not_authorize_capture(self):
        for elapsed,status in ((25,0),(25.001,0),(300.001,0),(0,1)):
            with self.subTest(elapsed=elapsed,status=status):
                code, report, harness = self.execute(elapsed=elapsed,status=status)
                self.assertEqual(code,1)
                self.assertFalse(report['passed'])
                self.assertEqual(report['captures'],[])
                self.assertFalse(harness.ax_done)
                self.assertEqual((report['cg_event_post_attempts'],harness.focus_calls),(0,0))
                self.assertEqual(len(report['capture_attempts']),1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
