#!/usr/bin/env python3
"""Observer failure controls; Linux execution does not qualify native Mac input."""
import ctypes as C
import json
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import probe_macos_input as probe


class PreflightControls(unittest.TestCase):
    def test_required_permissions_fail_closed(self):
        post, capture = 'CGPreflightPostEventAccess', 'CGPreflightScreenCaptureAccess'
        for permissions in ({}, {post: False, capture: False}, {post: 1, capture: True}):
            self.assertIn(post, probe.denied_permissions(permissions))
        self.assertEqual(probe.denied_permissions({post: True, capture: True,
                                                  'AXIsProcessTrusted': False}), [])
        self.assertEqual(probe.denied_permissions({post: True, capture: False}), [capture])

    def test_only_owned_layer_zero_metadata_survives(self):
        def window(pid, layer=0):
            return {'kCGWindowOwnerPID': pid, 'kCGWindowLayer': layer, 'kCGWindowNumber': 51,
                    'kCGWindowIsOnscreen': True, 'kCGWindowName': 'private title',
                    'kCGWindowBounds': {'X': 40.0, 'Y': 60.0, 'Width': 960.0, 'Height': 565.0}}
        windows = probe.owned_windows([window(120), window(121), window(120, 2)], 120)
        self.assertEqual(len(windows), 1)
        self.assertEqual(windows[0]['bounds_points_including_chrome'], [40, 60, 960, 565])
        self.assertNotIn('private title', json.dumps(windows))
        for bad in (float('nan'), float('inf'), True, None, '960', 0, -1):
            entry = window(120)
            entry['kCGWindowBounds']['Width'] = bad
            with self.assertRaises(RuntimeError):
                probe.owned_windows([entry], 120)

    def test_native_framework_objects_are_released_on_bad_payload(self):
        released = []
        class CG:
            @staticmethod
            def CGWindowListCopyWindowInfo(*_args):
                return 100
        class CF:
            @staticmethod
            def CFPropertyListCreateData(*_args):
                return 200
            @staticmethod
            def CFDataGetLength(_data):
                return 4 * 1024 * 1024 + 1
            CFRelease = staticmethod(released.append)
        api = object.__new__(probe.MacReadOnly)
        api.cg, api.cf = CG(), CF()
        with self.assertRaisesRegex(RuntimeError, 'bounded byte budget'):
            api.windows(120)
        self.assertEqual(released, [200, 100])

    def test_actual_plist_bytes_decode_through_cf_boundary(self):
        # Exercises the actual ctypes byte read and strict plist decoder, not a
        # fabricated Mac pass. No native framework is loaded on this host.
        blob = plistlib.dumps([{'kCGWindowOwnerPID': 200, 'kCGWindowLayer': 0,
                              'kCGWindowNumber': 75, 'kCGWindowIsOnscreen': True,
                              'kCGWindowBounds': {'X': 10, 'Y': 20, 'Width': 960, 'Height': 565}}])
        buffer = C.create_string_buffer(blob)
        class Library:
            CGWindowListCopyWindowInfo = staticmethod(lambda *_args: 100)
            CFPropertyListCreateData = staticmethod(lambda *_args: 200)
            CFDataGetLength = staticmethod(lambda *_args: len(blob))
            CFDataGetBytePtr = staticmethod(lambda *_args: C.addressof(buffer))
            CFRelease = staticmethod(lambda *_args: None)
        api = object.__new__(probe.MacReadOnly)
        api.cg = api.cf = Library()
        self.assertEqual(api.windows(200)[0]['window_id'], 75)
        self.assertEqual(api.windows(201), [])

    def test_non_native_run_retains_failure_and_never_launches(self):
        with tempfile.TemporaryDirectory() as temporary:
            with (patch.object(probe.platform, 'system', return_value='Linux'),
                  patch.object(probe.platform, 'platform', return_value='Linux observer control'),
                  patch.object(probe.subprocess, 'Popen') as launch):
                self.assertEqual(probe.run(Path(temporary) / 'evidence'), 1)
                launch.assert_not_called()
            result = json.loads((Path(temporary) / 'evidence/results.json').read_text())
            self.assertEqual(result['status'], 'FAILED')
            self.assertEqual(result['permission_requests_made'], 0)
            self.assertFalse(result['native_input_verified'])
            self.assertTrue(result['cleanup']['owned_group_gone'])
            self.assertIn('Requires native ARM macOS', result['failure']['message'])

    def test_prior_attempt_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            original = Path(temporary) / 'original.json'
            original.write_text('original')
            with self.assertRaisesRegex(RuntimeError, 'Preserve earlier attempts'):
                probe.run(temporary)
            self.assertEqual(original.read_text(), 'original')

    @unittest.skipIf(sys.platform == 'win32', 'POSIX owned-group cleanup control')
    def test_actual_owned_process_is_reaped(self):
        process = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'], start_new_session=True)
        try:
            receipt = probe.reap(process)
            self.assertTrue(receipt['owned_group_gone'])
            self.assertIsNotNone(receipt['exit_code'])
            self.assertEqual(receipt['signals_sent'], ['SIGTERM'])
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=3)


if __name__ == '__main__':
    unittest.main()
