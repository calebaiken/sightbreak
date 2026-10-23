#!/usr/bin/env python3
"""Control native-close serialization and export identity without a display."""
import ctypes as C
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock, patch

import verify_integration_export as controller


class NativeCloseTests(unittest.TestCase):
    def make_ui(self, result):
        self.sent = []
        ui = controller.NativeUI.__new__(controller.NativeUI)
        ui.d, ui.window = 123, 456
        def send(display, window, propagate, mask, pointer):
            event = C.cast(pointer, C.POINTER(controller.XEvent)).contents.xclient
            self.sent.append((display, window, propagate, mask, event.type, event.display,
                              event.window, event.message_type, event.format, event.data.l[0]))
            return result
        ui.x = SimpleNamespace(XInternAtom=lambda _display, name, _only: {b'WM_PROTOCOLS': 7, b'WM_DELETE_WINDOW': 8}[name],
                               XSendEvent=send, XFlush=Mock())
        return ui

    def test_completion_close_serializes_standard_window_protocol(self):
        ui = self.make_ui(1)
        ui.request_close()
        self.assertEqual(self.sent, [(123, 456, 0, 0, 33, 123, 456, 7, 32, 8)])
        ui.x.XFlush.assert_called_once_with(123)

    def test_undelivered_close_is_not_a_success(self):
        with self.assertRaisesRegex(RuntimeError, 'not delivered'):
            self.make_ui(0).request_close()


class ExportPreflightTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.executable = self.root / 'export/sightbreak.x86_64'
        self.executable.parent.mkdir()
        self.output = self.root / 'evidence'
        self.output.mkdir()
        self.current = dict(source_commit='commit-A', source_game_tree='tree',
                            source_content_sha256='runtime', source_validation_sha256='tooling',
                            source_game_dirty=False, source_dirty=False)
        self.executable.write_bytes(b'fixture, not native game')
        self.receipt = {**self.current, 'export_completed': True,
                        'artifact': {'sha256': hashlib.sha256(self.executable.read_bytes()).hexdigest()}}
        self.save_receipt()
        snapshot = patch.object(controller, 'source', lambda: dict(self.current))
        snapshot.start()
        self.addCleanup(snapshot.stop)

    def save_receipt(self):
        (self.executable.parent / 'source.json').write_text(json.dumps(self.receipt))

    def test_same_frozen_identity_is_required(self):
        receipt, before, digest = controller.frozen_export(self.executable, self.output)
        self.assertEqual(before, self.current)
        self.assertEqual(digest, receipt['artifact']['sha256'])
        self.assertFalse((self.output / 'results.json').exists())

    def test_changed_commit_same_runtime_is_retained_failure(self):
        self.current['source_commit'] = 'commit-B'
        with self.assertRaisesRegex(RuntimeError, 'frozen source'):
            controller.frozen_export(self.executable, self.output)
        result = json.loads((self.output / 'results.json').read_text())
        self.assertFalse(result['passed'])
        self.assertEqual(result['stage'], 'preflight')

    def test_missing_receipt_is_retained_failure(self):
        (self.executable.parent / 'source.json').unlink()
        with self.assertRaises(FileNotFoundError):
            controller.frozen_export(self.executable, self.output)
        self.assertFalse(json.loads((self.output / 'results.json').read_text())['passed'])

    def test_dirty_tooling_is_retained_failure(self):
        self.current['source_dirty'] = True
        with self.assertRaises(SystemExit):
            controller.frozen_export(self.executable, self.output)
        self.assertFalse(json.loads((self.output / 'results.json').read_text())['passed'])

    def test_export_is_rechecked_at_use_boundaries(self):
        manifest, before, digest = controller.frozen_export(self.executable, self.output)
        self.assertEqual(controller.unchanged_export(self.executable, manifest, before, digest), digest)
        self.executable.write_bytes(b'different ignored build bytes after preflight')
        with self.assertRaisesRegex(RuntimeError, 'executable changed'):
            controller.unchanged_export(self.executable, manifest, before, digest)

    def test_receipt_cannot_change_after_preflight(self):
        manifest, before, digest = controller.frozen_export(self.executable, self.output)
        self.receipt['extra'] = 'changed after preflight'
        self.save_receipt()
        with self.assertRaisesRegex(RuntimeError, 'receipt changed'):
            controller.unchanged_export(self.executable, manifest, before, digest)

    def test_source_cannot_change_after_preflight(self):
        manifest, before, digest = controller.frozen_export(self.executable, self.output)
        self.current['source_validation_sha256'] = 'changed controller bytes'
        with self.assertRaisesRegex(RuntimeError, 'Frozen source changed'):
            controller.unchanged_export(self.executable, manifest, before, digest)


if __name__ == '__main__':
    unittest.main()
